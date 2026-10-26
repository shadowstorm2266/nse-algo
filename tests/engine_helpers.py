"""Builders for engine tests: fills, orders, snapshots, synthetic sessions, toy strategies."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date, time
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd

from nsealgo.costs import CostBreakdown, CostConfig, load_cost_config
from nsealgo.data.calendar import IST
from nsealgo.engine.config import MarginConfig, RiskConfig, load_risk_config
from nsealgo.engine.types import (
    ExitReason,
    Fill,
    IntentKind,
    Order,
    OrderIntent,
    OrderRole,
    OrderType,
    Product,
    Side,
)
from nsealgo.settings import REPO_ROOT

D = Decimal
ZERO = D(0)


def ts(day: date, hhmm: str) -> pd.Timestamp:
    return pd.Timestamp(f"{day.isoformat()} {hhmm}", tz=IST)


def charges(total: str | Decimal) -> CostBreakdown:
    t = D(total)
    return CostBreakdown(t, ZERO, ZERO, ZERO, ZERO, ZERO, ZERO, total=t)


def make_fill(
    side: Side,
    qty: int,
    price: str,
    ref: str,
    *,
    symbol: str = "X",
    product: Product = Product.MIS,
    role: OrderRole = OrderRole.ENTRY,
    cost: str = "0",
    when: pd.Timestamp | None = None,
    stop: str | None = None,
    reason: ExitReason | None = None,
    order_id: int = 1,
) -> Fill:
    when = when if when is not None else pd.Timestamp("2024-01-02 10:00", tz=IST)
    return Fill(
        order_id=order_id,
        symbol=symbol,
        product=product,
        side=side,
        qty=qty,
        ts=when,
        session_date=when.date(),
        price=D(price),
        ref_price=D(ref),
        charges=charges(cost),
        role=role,
        exit_reason=reason,
        stop_loss=D(stop) if stop else None,
    )


def risk_config(**overrides: Any) -> RiskConfig:
    """The repo's risk.yaml with overrides (swing overrides via swing={...})."""
    base = load_risk_config().model_dump()
    swing = overrides.pop("swing", {})
    base.update(overrides)
    base["swing"] = {**base["swing"], **swing}
    return RiskConfig.model_validate(base)


def margins(pct: str = "25", **symbols: str) -> MarginConfig:
    return MarginConfig(
        default_mis_margin_pct=D(pct), symbols={k: D(v) for k, v in symbols.items()}
    )


def cost_config() -> CostConfig:
    return load_cost_config(REPO_ROOT / "config" / "costs.yaml")


# --- intents ---


def entry(
    symbol: str = "X",
    side: Side = Side.BUY,
    *,
    product: Product = Product.MIS,
    order_type: OrderType = OrderType.MARKET,
    price: float | None = None,
    stop: float | None = None,
    target: float | None = None,
    rank: int | None = None,
    group: str | None = None,
) -> OrderIntent:
    return OrderIntent(
        IntentKind.ENTRY,
        symbol,
        product,
        side=side,
        order_type=order_type,
        price=price,
        stop_loss=stop,
        target=target,
        rank=rank,
        group_id=group,
    )


def exit_(symbol: str = "X", *, product: Product = Product.MIS, qty: int | None = None):
    return OrderIntent(IntentKind.EXIT, symbol, product, qty=qty)


def working_order(
    symbol: str,
    side: Side,
    qty: int,
    ref: str,
    *,
    when: pd.Timestamp,
    role: OrderRole = OrderRole.ENTRY,
    product: Product = Product.MIS,
    order_type: OrderType = OrderType.MARKET,
    group: str | None = None,
    reason: ExitReason | None = None,
) -> Order:
    return Order(
        symbol,
        product,
        side,
        qty,
        order_type,
        role,
        when,
        price=D(ref) if order_type is not OrderType.MARKET else None,
        ref_price=D(ref),
        group_id=group,
        exit_reason=reason,
    )


# --- synthetic bars ---


def session_frame(
    symbol: str,
    day: date,
    minutes: int,
    price: Callable[[pd.Timestamp], float] | float,
    *,
    spread: float = 0.5,
    overrides: Mapping[str, tuple[float, float, float, float]] | None = None,
) -> pd.DataFrame:
    """One full session of `minutes` bars with open = close = price(ts) and
    high/low = price +/- spread; `overrides` maps "HH:MM" to exact (o, h, l, c)."""
    start = ts(day, "09:15")
    n = 375 // minutes
    stamps = pd.date_range(start, periods=n, freq=f"{minutes}min")
    px = np.array([price(t) if callable(price) else price for t in stamps], dtype="float64")
    df = pd.DataFrame(
        {
            "ts": stamps,
            "available_at": stamps + pd.Timedelta(minutes=minutes),
            "symbol": symbol,
            "session_date": day,
            "open": px,
            "high": px + spread,
            "low": px - spread,
            "close": px,
            "volume": np.full(n, 1000, dtype="int64"),
        }
    )
    for hhmm, ohlc in (overrides or {}).items():
        i = df.index[df["ts"] == ts(day, hhmm)]
        df.loc[i, ["open", "high", "low", "close"]] = ohlc
    return df


def daily_frame(
    symbol: str, rows: Mapping[date, tuple[float, float, float, float]]
) -> pd.DataFrame:
    """Daily bars: ts 09:15, available_at 15:30."""
    days = sorted(rows)
    df = pd.DataFrame(
        {
            "ts": [ts(d, "09:15") for d in days],
            "available_at": [ts(d, "15:30") for d in days],
            "symbol": symbol,
            "session_date": days,
            "open": [rows[d][0] for d in days],
            "high": [rows[d][1] for d in days],
            "low": [rows[d][2] for d in days],
            "close": [rows[d][3] for d in days],
            "volume": 1000,
        }
    )
    return df


def calendar_frame(days: list[date], no_trade: tuple[date, ...] = ()) -> pd.DataFrame:
    return pd.DataFrame({"session_date": days, "no_trade": [d in no_trade for d in days]})


# --- toy strategies (tests only) ---


@dataclass(frozen=True)
class ScriptedStrategy:
    """Emits pre-scripted intents at given decision times; records every ctx it saw."""

    product: Product
    timeframe: str
    script: Mapping[pd.Timestamp, list[OrderIntent]]
    name: str = "scripted"
    version: str = "test"
    lookback_sessions: int = 0
    seen: list[Any] = field(default_factory=list, compare=False)

    def params(self) -> dict[str, Any]:
        return {}

    def on_bar(self, ctx: Any) -> list[OrderIntent]:
        self.seen.append(ctx)
        return list(self.script.get(ctx.now, []))


def at_time(day: date, hhmm: str) -> time:
    return ts(day, hhmm).time()


# --- RiskGovernor snapshots ---


def pos_view(symbol: str, qty: int, price: str, *, product: Product = Product.MIS, mark=None):
    from nsealgo.engine.portfolio import PositionView

    when = pd.Timestamp("2024-01-02 09:30", tz=IST)
    return PositionView(symbol, product, qty, D(price), D(mark or price), when, None)


def view(order_id: int, order: Order, status=None):
    from nsealgo.engine.types import OrderStatus, OrderView

    return OrderView(order_id, order, status or OrderStatus.WORKING)


def snap(
    now: pd.Timestamp,
    *,
    equity: str = "20000",
    start: str | None = None,
    peak: str = "20000",
    ledger: str | None = None,
    unrealized: str = "0",
    margin_used: str = "0",
    positions: tuple = (),
    orders: tuple = (),
    fills: tuple = (),
    marks: Mapping[str, float] | None = None,
):
    from nsealgo.engine.portfolio import AccountSnapshot

    return AccountSnapshot(
        now=now,
        session_date=now.date(),
        equity=D(equity),
        equity_at_session_start=D(start or equity),
        peak_equity=D(peak),
        ledger=D(ledger or equity),
        unrealized=D(unrealized),
        margin_used=D(margin_used),
        positions={p.symbol: p for p in positions},
        orders=tuple(orders),
        fills_today=tuple(fills),
        marks=dict(marks or {}),
    )


def run_frames(
    strategy: Any,
    bars: pd.DataFrame,
    days: list[date],
    *,
    no_trade: tuple[date, ...] = (),
    features: pd.DataFrame | None = None,
    mode: str = "backtest",
    margin_pct: str = "25",
    **risk_overrides: Any,
):
    """Run a Backtester on in-memory frames; returns (result, backtester)."""
    from nsealgo.engine.backtest import Backtester
    from nsealgo.engine.market import MarketData
    from nsealgo.engine.sessions import TradingCalendar

    bt = Backtester(
        strategy,
        universe=sorted(bars["symbol"].unique()),
        calendar=TradingCalendar(days, no_trade),
        risk_config=risk_config(**risk_overrides),
        margins=margins(margin_pct),
        costs=cost_config(),
        brokerage_preset="shoonya",
        slippage_bps=D(3),
        mode=mode,
    )
    return bt.run([MarketData(strategy.timeframe, bars, days, features)]), bt
