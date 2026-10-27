"""Event-driven backtest loop.

For each bar group (all symbols' bars that start at the same time):
1. the SimBroker fills working orders against those bars;
2. positions are marked to the bars' closes;
3. at `now` = the bars' available_at, the RiskGovernor's forced exits (flat_by) are
   placed, then the strategy sees everything visible at `now`, and each intent goes
   through the RiskGovernor to the broker.
A signal on bar T therefore fills on bar T+1 at the earliest, and fills inside bar
T+1 become visible only at T+1's available_at.
"""

import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

from nsealgo.brokers.fills import Bar
from nsealgo.brokers.sim import BrokerEvent, SimBroker
from nsealgo.costs import CostConfig
from nsealgo.data.calendar import IST
from nsealgo.engine.config import MarginConfig, RiskConfig
from nsealgo.engine.context import LastCloses, StrategyContext
from nsealgo.engine.market import MarketData, SessionSlice
from nsealgo.engine.portfolio import AccountSnapshot, Portfolio, TradeRecord
from nsealgo.engine.risk import RiskGovernor
from nsealgo.engine.sessions import TIMEFRAMES, TradingCalendar, check_on_grid, session_close
from nsealgo.engine.types import (
    ExitReason,
    Fill,
    HaltRecord,
    IntentKind,
    OrderIntent,
    OrderStatus,
    Product,
    Rejection,
    RejectReason,
)
from nsealgo.settings import Mode
from nsealgo.strategies.base import Strategy

logger = logging.getLogger("nsealgo.engine")
REJECTION_COLS = ["now", "symbol", "reason", "detail", "kind", "price", "rank", "group_id"]


FILL_COLS = [
    "order_id",
    "symbol",
    "product",
    "side",
    "qty",
    "ts",
    "session_date",
    "price",
    "ref_price",
    "value",
    "slippage",
    "charges",
    "dp_charge",
    "role",
    "exit_reason",
    "group_id",
]


@dataclass(frozen=True)
class BacktestResult:
    trades: pd.DataFrame
    fills: pd.DataFrame
    equity: pd.DataFrame
    intents: list[tuple[pd.Timestamp, OrderIntent]]
    rejections: pd.DataFrame
    events: list[BrokerEvent]
    halt: HaltRecord | None
    fallback_exits: int


def validate_strategy(strategy: Strategy, risk: RiskConfig) -> None:
    tf = strategy.timeframe
    if tf not in TIMEFRAMES:
        raise ValueError(f"unknown timeframe {tf!r}")
    if strategy.product is Product.MIS:
        if tf == "1d":
            raise ValueError("MIS strategies need an intraday timeframe")
        check_on_grid(TIMEFRAMES[tf], (risk.entry_start, risk.entry_end, risk.flat_by))
        if strategy.lookback_sessions:
            raise ValueError("lookback_sessions is only for 1d strategies")
    elif tf != "1d":
        raise ValueError("CNC (swing) strategies use daily bars")


class Backtester:
    def __init__(
        self,
        strategy: Strategy,
        *,
        universe: Sequence[str],
        calendar: TradingCalendar,
        risk_config: RiskConfig,
        margins: MarginConfig,
        costs: CostConfig,
        brokerage_preset: str,
        slippage_bps: Decimal,
        mode: Mode = "backtest",
        kill_file: Path | None = None,
    ) -> None:
        validate_strategy(strategy, risk_config)
        self.strategy = strategy
        self.universe = tuple(universe)
        self.calendar = calendar
        sizing = risk_config.sizing_basis.for_mode(mode)
        self.portfolio = Portfolio(risk_config.capital, margins, sizing)
        self.broker = SimBroker(
            costs,
            brokerage_preset,
            slippage_bps,
            funds=self.portfolio,
            on_fill=self._on_fill,
        )
        self.risk = RiskGovernor(
            risk_config,
            margins,
            calendar,
            costs,
            brokerage_preset,
            product=strategy.product,
            mode=mode,
            kill_file=kill_file,
        )
        self.intents: list[tuple[pd.Timestamp, OrderIntent]] = []
        self.fills: list[Fill] = []
        self.rejections: list[Rejection] = []
        self.equity_rows: list[dict[str, Any]] = []
        self.fallback_exits = 0
        self._last_bar: dict[str, Bar] = {}

    def run(self, chunks: Iterable[MarketData]) -> BacktestResult:
        last = self.calendar.sessions[-1] if self.calendar.sessions else None
        for chunk in chunks:
            for day in chunk.run_sessions:
                self._run_session(chunk.session(day), is_last=day == last)
        return self._result()

    # --- one session ---

    def _run_session(self, sl: SessionSlice, is_last: bool) -> None:
        self.portfolio.start_session(sl.day)
        for t_ns, now_ns in sl.steps:
            self._process(sl, t_ns)
            self._decide(sl, now_ns)
        if is_last:
            for symbol in list(self.portfolio.positions):
                self._force_close(symbol, sl.day, ExitReason.END_OF_RUN)
        self._end_session(sl.day)

    def _process(self, sl: SessionSlice, t_ns: int) -> None:
        bars = {}
        for symbol in self.broker.active_symbols():
            s = sl.series.get(symbol)
            i = s.index_at(t_ns) if s is not None else None
            if i is not None:
                bars[symbol] = s.bar(i)
        if not bars:
            return
        fills = self.broker.process(bars)
        for symbol, b in bars.items():
            self._last_bar[symbol] = b
            self.portfolio.mark(symbol, b.close)
        if self.portfolio.positions or fills:
            now = pd.Timestamp(t_ns, tz=IST)
            pf = self.portfolio
            self.risk.observe_equity(pf.equity(), pf.peak_equity, sl.day, now)

    def _decide(self, sl: SessionSlice, now_ns: int) -> None:
        now = pd.Timestamp(now_ns, tz=IST)
        self.broker.now = now
        if self.strategy.product is Product.MIS and now.time() >= self.risk.config.flat_by:
            orders, cancels = self.risk.forced_exits(self._snapshot(now, {}), now)
            for order_id in cancels:
                self.broker.cancel(order_id, "flat_by")
            for order in orders:
                self.broker.place(order)
        ctx = self._context(sl, now, now_ns)
        intents = list(self.strategy.on_bar(ctx))
        if not intents:
            return
        self.intents.extend((now, i) for i in intents)
        marks = LastCloses(ctx)
        ok, bad = self.risk.screen_groups(intents, self._snapshot(now, marks), now)
        self.rejections.extend(bad)
        self._review(ok, now, marks)

    def _review(self, intents: list[OrderIntent], now: pd.Timestamp, marks: Mapping) -> None:
        """Exits first, then entries by rank. OCO groups are all-or-nothing."""
        exits = [i for i in intents if i.kind is IntentKind.EXIT]
        entries = sorted(
            (i for i in intents if i.kind is IntentKind.ENTRY),
            key=lambda i: (i.rank is None, i.rank or 0),
        )
        failed: set[str] = set()
        placed: dict[str, list[tuple[int, OrderIntent]]] = defaultdict(list)
        for intent in exits + entries:
            gid = intent.group_id
            if gid is not None and gid in failed:
                self.rejections.append(self.risk.reject_group_leg(intent, now))
                continue
            result = self.risk.review(intent, self._snapshot(now, marks), now)
            if isinstance(result, Rejection):
                self.rejections.append(result)
                if gid is not None:
                    failed.add(gid)
                    for order_id, leg in placed.pop(gid, []):
                        self.broker.cancel(order_id, "OCO group leg rejected")
                        self.rejections.append(self.risk.reject_group_leg(leg, now))
                continue
            order_id = self.broker.place(result)
            if gid is not None:
                placed[gid].append((order_id, intent))

    def _end_session(self, day: date) -> None:
        close = session_close(day)
        self.broker.now = close
        self.broker.end_session(day)
        for symbol, p in list(self.portfolio.positions.items()):
            if p.product is Product.MIS:
                self._force_close(symbol, day, ExitReason.SESSION_END_FALLBACK)
        row = self.portfolio.end_session()
        self.equity_rows.append(row)
        self.risk.observe_equity(row["equity"], self.portfolio.peak_equity, day, close)
        broker_book = {s: p.qty for s, p in self.broker.positions().items()}
        books = {s: p.qty for s, p in self.portfolio.positions.items()}
        if broker_book != books:
            raise RuntimeError(f"{day}: broker {broker_book} != portfolio {books}")

    def _force_close(self, symbol: str, day: date, reason: ExitReason) -> None:
        bar = self._last_bar.get(symbol)
        if bar is None:
            raise RuntimeError(f"no price to close {symbol} on {day}")
        self.broker.force_close(symbol, bar.close, bar.ts, day, reason)
        if reason is ExitReason.SESSION_END_FALLBACK:
            self.fallback_exits += 1
            logger.warning("%s %s: no bar at or after flat_by; closed at last close", day, symbol)

    # --- helpers ---

    def _on_fill(self, fill: Fill) -> TradeRecord | None:
        self.fills.append(fill)
        return self.portfolio.apply_fill(fill)

    def _context(self, sl: SessionSlice, now: pd.Timestamp, now_ns: int) -> StrategyContext:
        return StrategyContext(
            now=now,
            session_date=sl.day,
            session_no_trade=self.calendar.is_no_trade(sl.day),
            next_session=self.calendar.next_session_after(sl.day),
            symbols=self.universe,
            positions=self.portfolio.position_views(),
            working_orders=tuple(
                v for v in self.broker.orders() if v.status is OrderStatus.WORKING
            ),
            fills_today=tuple(self.portfolio.fills_today),
            _slice=sl,
            _now_ns=now_ns,
        )

    def _snapshot(self, now: pd.Timestamp, marks: Mapping[str, float]) -> AccountSnapshot:
        return self.portfolio.snapshot(now, self.broker.orders(), marks)

    def _result(self) -> BacktestResult:
        broker_rejects = [
            Rejection(
                now=e.ts,
                symbol=e.symbol,
                reason=RejectReason.INSUFFICIENT_CASH
                if e.reason.startswith("INSUFFICIENT_CASH")
                else RejectReason.INVALID_INTENT,
                detail=e.reason,
                kind="BROKER",
            )
            for e in self.broker.events
            if e.status is OrderStatus.REJECTED
        ]
        return BacktestResult(
            trades=trades_frame(self.portfolio.trades),
            fills=fills_frame(self.fills),
            equity=_frame([_plain_row(r) for r in self.equity_rows]),
            intents=self.intents,
            rejections=_frame(
                [_plain_row(asdict(r)) for r in self.rejections + broker_rejects], REJECTION_COLS
            ),
            events=self.broker.events,
            halt=self.risk.halt,
            fallback_exits=self.fallback_exits,
        )


def _plain(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, Enum):
        return v.value
    return v


def _plain_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: _plain(v) for k, v in row.items()}


def _frame(rows: list[dict[str, Any]], columns: list[str] | None = None) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=columns) if columns else pd.DataFrame(rows)


def trades_frame(trades: list[TradeRecord]) -> pd.DataFrame:
    cols = list(TradeRecord.__dataclass_fields__)
    return _frame([_plain_row(asdict(t)) for t in trades], cols)


def fills_frame(fills: list[Fill]) -> pd.DataFrame:
    """One row per fill. `value` and `slippage` are rupees; `charges` is the order's total
    charges and `dp_charge` its DP charge before GST (GST on it is inside `charges`)."""
    rows = [
        {
            "order_id": f.order_id,
            "symbol": f.symbol,
            "product": f.product.value,
            "side": f.side.value,
            "qty": f.qty,
            "ts": f.ts,
            "session_date": f.session_date,
            "price": float(f.price),
            "ref_price": float(f.ref_price),
            "value": float(f.value),
            "slippage": float(f.slippage),
            "charges": float(f.charges.total),
            "dp_charge": float(f.charges.dp_charge),
            "role": f.role.value,
            "exit_reason": f.exit_reason.value if f.exit_reason is not None else None,
            "group_id": f.group_id,
        }
        for f in fills
    ]
    return _frame(rows, FILL_COLS)
