"""Strategy 2: monthly momentum, swing (CNC delivery, daily bars).

Decides after the close of the last tradeable session of each month M (the calendar's
next tradeable session is in another month), using data up to that close: a month whose
last session is no_trade decides on the last tradeable session before it. The
RiskGovernor turns the intents into market orders for the next tradeable session's open.

- Momentum: close at the end of month M - skip over the close at the end of month
  M - skip - lookback, minus 1 (6 months, skipping the latest month, by default). A
  month's end close is the symbol's last close in that month.
- Ranked: symbols with a bar on the decision day, at least `trend_ma_sessions` closes,
  and a close strictly above their `trend_ma_sessions` simple average. Highest
  momentum first; ties by symbol.
- Target: the top N. Holdings still in it are kept as they are (no top-up or trim);
  holdings not in it get a market exit; newcomers get a market entry with their rank.
  Only newcomers are bought: if the RiskGovernor skips one (one share above the
  position cap), its slot stays in cash until the next rebalance.
- Market filter (optional): if the index closes below its own simple average at a
  rebalance, the target is empty (go to cash). Without the index bars on the decision
  day, or with too few of them, the filter is skipped for that rebalance.

Equal weight, whole shares, the position cap and max_positions belong to the
RiskGovernor (config/risk.yaml). All parameters come from config/strategies/swing.yaml;
nothing here has a default.
"""

import math
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from nsealgo.engine.context import BarView, StrategyContext
from nsealgo.engine.types import IntentKind, OrderIntent, OrderRole, Product, Side

MAX_SESSIONS_PER_MONTH = 23  # NSE months have at most 23 weekday sessions


class _Params(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MarketFilter(_Params):
    enabled: bool
    index_symbol: str = Field(min_length=1)
    ma_sessions: int = Field(gt=1)


class SwingParams(_Params):
    top_n: int = Field(gt=0)
    lookback_months: int = Field(gt=0)
    skip_months: int = Field(ge=0)
    trend_ma_sessions: int = Field(gt=1)
    resize_holdings: bool
    market_filter: MarketFilter

    @field_validator("resize_holdings")
    @classmethod
    def _no_resize(cls, v: bool) -> bool:
        if v:
            raise ValueError(
                "resize_holdings: true is not implemented: the engine holds one position "
                "per symbol and cannot add to it"
            )
        return v


@dataclass(frozen=True, slots=True)
class Candidate:
    symbol: str
    momentum: float  # fraction: 0.10 is +10%


def month_index(d: date) -> int:
    return d.year * 12 + d.month - 1


def is_month_end(ctx: StrategyContext) -> bool:
    """The last tradeable session of its month: today is not no_trade and the calendar's
    next tradeable session is in another month. False when no tradeable session follows
    (nothing could fill)."""
    nxt = ctx.next_tradeable_session
    if ctx.session_no_trade or nxt is None:
        return False
    return month_index(nxt) != month_index(ctx.session_date)


def month_end_close(months: np.ndarray, close: np.ndarray, month: int) -> float | None:
    """The last close in `month` (a month_index), if the symbol has a bar in it."""
    i = int(np.searchsorted(months, month, side="right")) - 1
    if i < 0 or months[i] != month:
        return None
    return float(close[i])


def above_average(bars: BarView, sessions: int) -> bool:
    c = bars.close
    return len(c) >= sessions and float(c[-1]) > float(c[-sessions:].mean())


class SwingMomentumStrategy:
    name = "swing"
    # bump on any logic change or change of a default in swing.yaml
    # 2: a month ending on no_trade sessions decides on its last tradeable session
    version = "2"
    product = Product.CNC
    timeframe = "1d"

    def __init__(self, **params: Any) -> None:
        self.p = SwingParams.model_validate(params)
        mf = self.p.market_filter
        months = self.p.lookback_months + self.p.skip_months
        self.lookback_sessions = max(
            self.p.trend_ma_sessions,
            mf.ma_sessions if mf.enabled else 0,
            MAX_SESSIONS_PER_MONTH * months,
        )
        self.reference_symbols: tuple[str, ...] = (mf.index_symbol,) if mf.enabled else ()

    def params(self) -> dict[str, Any]:
        return self.p.model_dump(mode="json")

    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:
        if not is_month_end(ctx):
            return []
        ranked = self.ranked(ctx)
        target = [] if self.risk_off(ctx) else [c.symbol for c in ranked[: self.p.top_n]]
        rank = {c.symbol: i for i, c in enumerate(ranked, start=1)}
        return self.rebalance(ctx, target, rank)

    # --- ranking ---

    def ranked(self, ctx: StrategyContext) -> list[Candidate]:
        out = [c for s in ctx.symbols if (c := self.candidate(ctx, s)) is not None]
        out.sort(key=lambda c: (-c.momentum, c.symbol))
        return out

    def candidate(self, ctx: StrategyContext, symbol: str) -> Candidate | None:
        bars = ctx.bars(symbol)
        if not len(bars) or bars.ts[-1].date() != ctx.session_date:
            return None
        if not above_average(bars, self.p.trend_ma_sessions):
            return None
        mom = self.momentum(bars, ctx.session_date)
        return Candidate(symbol, mom) if mom is not None else None

    def momentum(self, bars: BarView, day: date) -> float | None:
        months = np.asarray(bars.ts.year * 12 + bars.ts.month - 1)
        end_month = month_index(day) - self.p.skip_months
        end = month_end_close(months, bars.close, end_month)
        start = month_end_close(months, bars.close, end_month - self.p.lookback_months)
        if end is None or start is None or not start > 0:
            return None
        mom = end / start - 1
        return mom if math.isfinite(mom) else None

    def risk_off(self, ctx: StrategyContext) -> bool:
        """True when the market filter is on and the index closed below its average.
        Missing or short index data skips the filter (False)."""
        mf = self.p.market_filter
        if not mf.enabled:
            return False
        bars = ctx.bars(mf.index_symbol)
        if len(bars) < mf.ma_sessions or bars.ts[-1].date() != ctx.session_date:
            return False
        return float(bars.close[-1]) < float(bars.close[-mf.ma_sessions :].mean())

    # --- order intents ---

    @staticmethod
    def rebalance(
        ctx: StrategyContext, target: list[str], rank: dict[str, int]
    ) -> list[OrderIntent]:
        """Exits for holdings not in `target`, entries for `target` symbols not held."""
        held = {s for s, p in ctx.positions.items() if p.product is Product.CNC}
        working = {(v.order.symbol, v.order.role) for v in ctx.working_orders}
        exits = [
            OrderIntent(IntentKind.EXIT, s, Product.CNC, tag="swing_exit")
            for s in sorted(held - set(target))
            if (s, OrderRole.EXIT) not in working
        ]
        entries = [
            OrderIntent(IntentKind.ENTRY, s, Product.CNC, side=Side.BUY, rank=rank[s], tag="swing")
            for s in target
            if s not in held and (s, OrderRole.ENTRY) not in working
        ]
        return exits + entries
