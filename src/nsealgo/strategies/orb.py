"""Strategy 1: 30-minute Opening Range Breakout (intraday MIS).

At the end of the opening range (09:45 for 30 minutes), for each symbol: ORH and ORL
are the high and low of the bars starting 09:15 .. 09:40. Two STOP entry legs share
one OCO group: buy above ORH x (1 + buffer), sell below ORL x (1 - buffer). Each leg
carries a bracket stop (the far side of the range, or its midpoint) and a target at
target_r x R from its trigger. When one leg fills the broker cancels the other;
unfilled legs expire at the RiskGovernor's entry_end. Open positions get a market exit
at time_exit, and the RiskGovernor flattens everything at flat_by.

Entries are emitted only at the range-end step, so a symbol gets at most one OCO group,
hence one trade, per day. Candidates are ranked by range width / ATR14, both known at
the range end; the RiskGovernor reviews groups in rank order and rejects those beyond
max_trades_per_day (MAX_TRADES_PER_DAY), which is the log of skipped symbols.

A symbol is skipped when its opening range is incomplete (a missing bar) or its daily
features are missing (the warmup sessions). All parameters come from
config/strategies/orb.yaml; nothing here has a default.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from nsealgo.engine.context import BarView, StrategyContext
from nsealgo.engine.sessions import TIMEFRAMES
from nsealgo.engine.types import IntentKind, OrderIntent, OrderRole, OrderType, Product, Side

SESSION_OPEN_MINUTE = 9 * 60 + 15


class _Params(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RangeWidthFilter(_Params):
    enabled: bool
    min_pct: float = Field(ge=0)
    max_pct: float = Field(gt=0)

    @model_validator(mode="after")
    def _ordered(self) -> "RangeWidthFilter":
        if self.min_pct >= self.max_pct:
            raise ValueError("range_width needs min_pct < max_pct")
        return self


class GapFilter(_Params):
    enabled: bool
    max_abs_pct: float = Field(ge=0)


class Switch(_Params):
    enabled: bool


class NiftyFilter(_Params):
    enabled: bool

    @field_validator("enabled")
    @classmethod
    def _not_implemented(cls, v: bool) -> bool:
        if v:
            raise ValueError("nifty_direction is not implemented: no NIFTY 50 index bars")
        return v


class DayOfWeekFilter(_Params):
    enabled: bool
    skip_weekdays: tuple[int, ...]

    @model_validator(mode="after")
    def _weekdays(self) -> "DayOfWeekFilter":
        if any(not 0 <= d <= 4 for d in self.skip_weekdays):
            raise ValueError("skip_weekdays are 0 (Monday) .. 4 (Friday)")
        if self.enabled and not self.skip_weekdays:
            raise ValueError("day_of_week is enabled but skip_weekdays is empty")
        return self


class OrbFilters(_Params):
    range_width: RangeWidthFilter
    gap: GapFilter
    prev_day_confluence: Switch
    nifty_direction: NiftyFilter
    day_of_week: DayOfWeekFilter


class OrbParams(_Params):
    timeframe: Literal["1m", "5m"]
    range_minutes: int = Field(gt=0)
    buffer_pct: float = Field(ge=0)
    stop: Literal["full", "mid"]
    target_r: float = Field(gt=0)
    time_exit: time
    rank_order: Literal["narrowest_first", "widest_first"]
    filters: OrbFilters

    @model_validator(mode="after")
    def _grid(self) -> "OrbParams":
        if self.range_minutes % TIMEFRAMES[self.timeframe]:
            raise ValueError("range_minutes must be a whole number of bars")
        if self.time_exit <= self.range_end:
            raise ValueError("time_exit must be after the opening range ends")
        return self

    @property
    def range_end(self) -> time:
        end = SESSION_OPEN_MINUTE + self.range_minutes
        return time(end // 60, end % 60)

    @property
    def range_bars(self) -> int:
        return self.range_minutes // TIMEFRAMES[self.timeframe]


@dataclass(frozen=True, slots=True)
class Setup:
    """One symbol's opening range at the range end."""

    symbol: str
    high: float
    low: float
    score: float  # (high - low) / ATR14
    long_ok: bool
    short_ok: bool


def _num(features: Mapping[str, Any], key: str) -> float | None:
    v = features.get(key)
    if v is None:
        return None
    v = float(v)
    return v if math.isfinite(v) else None


class OrbStrategy:
    name = "orb"
    version = "1"  # bump on any logic change or change of a default in orb.yaml
    product = Product.MIS
    instrument = "EQ"
    lookback_sessions = 0
    reference_symbols: tuple[str, ...] = ()

    def __init__(self, **params: Any) -> None:
        self.p = OrbParams.model_validate(params)
        self.timeframe = self.p.timeframe

    def params(self) -> dict[str, Any]:
        return self.p.model_dump(mode="json")

    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:
        t = ctx.now.time()
        if t >= self.p.time_exit:
            return time_exits(ctx)
        if t == self.p.range_end and not ctx.session_no_trade:
            return self.entries(ctx)
        return []

    # --- entries ---

    def entries(self, ctx: StrategyContext) -> list[OrderIntent]:
        dow = self.p.filters.day_of_week
        if dow.enabled and ctx.session_date.weekday() in dow.skip_weekdays:
            return []
        setups = [s for sym in ctx.symbols if (s := self.setup(ctx, sym)) is not None]
        sign = 1 if self.p.rank_order == "narrowest_first" else -1
        setups.sort(key=lambda s: (sign * s.score, s.symbol))
        out: list[OrderIntent] = []
        for rank, s in enumerate(setups, start=1):
            out += self.legs(s, rank, ctx.session_date)
        return out

    def setup(self, ctx: StrategyContext, symbol: str) -> Setup | None:
        """The symbol's opening range if it is complete and passes the filters."""
        bars, feats = ctx.bars(symbol), ctx.features(symbol)
        if feats is None or not self._complete_range(bars):
            return None
        atr = _num(feats, "atr14")
        if atr is None or atr <= 0:
            return None
        hi, lo, opn = float(bars.high.max()), float(bars.low.min()), float(bars.open[0])
        if not self._passes(opn, hi, lo, feats):
            return None
        long_ok, short_ok = self._sides(hi, lo, feats)
        if not (long_ok or short_ok):
            return None
        return Setup(symbol, hi, lo, (hi - lo) / atr, long_ok, short_ok)

    def _complete_range(self, bars: BarView) -> bool:
        # Called at the range end, so every visible bar belongs to the range.
        if len(bars) != self.p.range_bars:
            return False
        first = bars.ts[0]
        return first.hour * 60 + first.minute == SESSION_OPEN_MINUTE

    def _passes(self, opn: float, hi: float, lo: float, feats: Mapping[str, Any]) -> bool:
        f = self.p.filters
        if f.range_width.enabled:
            width = (hi - lo) / opn * 100
            if not f.range_width.min_pct <= width <= f.range_width.max_pct:
                return False
        if f.gap.enabled:
            prev_close = _num(feats, "prev_close")
            if prev_close is None or prev_close <= 0:
                return False
            if abs(opn / prev_close - 1) * 100 > f.gap.max_abs_pct:
                return False
        return True

    def _sides(self, hi: float, lo: float, feats: Mapping[str, Any]) -> tuple[bool, bool]:
        if not self.p.filters.prev_day_confluence.enabled:
            return True, True
        prev_high, prev_low = _num(feats, "prev_high"), _num(feats, "prev_low")
        long_ok = prev_high is not None and self.trigger(hi, Side.BUY) > prev_high
        short_ok = prev_low is not None and self.trigger(lo, Side.SELL) < prev_low
        return long_ok, short_ok

    # --- order intents ---

    def trigger(self, level: float, side: Side) -> float:
        return level * (1 + side.sign * self.p.buffer_pct / 100)

    def legs(self, s: Setup, rank: int, day: date) -> list[OrderIntent]:
        group = f"orb-{day.isoformat()}-{s.symbol}"
        sides = [side for side, ok in ((Side.BUY, s.long_ok), (Side.SELL, s.short_ok)) if ok]
        return [self._leg(s, side, rank, group) for side in sides]

    def _leg(self, s: Setup, side: Side, rank: int, group: str) -> OrderIntent:
        long = side is Side.BUY
        trigger = self.trigger(s.high if long else s.low, side)
        far_side = s.low if long else s.high
        stop = (s.high + s.low) / 2 if self.p.stop == "mid" else far_side
        target = trigger + side.sign * self.p.target_r * abs(trigger - stop)
        return OrderIntent(
            IntentKind.ENTRY,
            s.symbol,
            Product.MIS,
            side=side,
            order_type=OrderType.STOP,
            price=trigger,
            stop_loss=stop,
            target=target,
            rank=rank,
            group_id=group,
            tag="orb",
        )


def time_exits(ctx: StrategyContext) -> list[OrderIntent]:
    """A market exit for every open MIS position without a working exit."""
    exiting = {v.order.symbol for v in ctx.working_orders if v.order.role is OrderRole.EXIT}
    return [
        OrderIntent(IntentKind.EXIT, symbol, Product.MIS, tag="orb_time_exit")
        for symbol, p in sorted(ctx.positions.items())
        if p.product is Product.MIS and symbol not in exiting
    ]
