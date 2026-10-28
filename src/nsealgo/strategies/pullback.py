"""Strategy 3: pullback mean reversion, swing (CNC delivery, daily bars).

Pre-registered in research/strategy3_plan.md. Decides after the close of every session
that is not no_trade and has a tradeable session after it, using daily bars up to that
close. No decision on no_trade sessions: their stored close may not be the real one,
and an exit or entry due then waits for the next tradeable session's decision. The
RiskGovernor turns the intents into market orders for the next tradeable session's open.

- Entry candidates: symbols with a bar on the decision day, not held and with no
  working entry, whose close is strictly above their `trend_ma_sessions` simple average
  and whose Wilder RSI(`rsi_sessions`) is strictly below `rsi_entry_below`. Ranked by
  lowest RSI, ties by symbol. Every candidate gets an entry with its rank; the
  RiskGovernor buys as many as the swing limits allow, in rank order.
- Exit: the close is strictly above the `exit_ma_sessions` simple average, or the
  position has been held `max_hold_sessions` or more sessions. Sessions held are
  trading-calendar sessions from the one whose open filled the buy (1 at its close) to
  the decision session, no_trade sessions included. A held symbol without a bar on the
  decision day is checked only for the time exit. No stop loss.
- RSI is computed on the last RSI_HISTORY closes. For RSI(2) the seed's weight after 97
  smoothing steps is 2^-97, so this equals the full-history value to float precision
  and does not depend on where the history starts.

Equal weight, whole shares, the position cap and max_positions belong to the
RiskGovernor (config/risk.yaml). All parameters come from config/strategies/pullback.yaml;
nothing here has a default.
"""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from nsealgo.engine.context import StrategyContext
from nsealgo.engine.portfolio import PositionView
from nsealgo.engine.types import IntentKind, OrderIntent, OrderRole, Product, Side
from nsealgo.strategies.indicators import above_average, has_bar_on, wilder_rsi

RSI_HISTORY = 100  # closes the RSI is computed on


class PullbackParams(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    trend_ma_sessions: int = Field(gt=1)
    rsi_sessions: int = Field(gt=0, lt=RSI_HISTORY - 1)
    rsi_entry_below: float = Field(gt=0, lt=100)
    exit_ma_sessions: int = Field(gt=1)
    max_hold_sessions: int = Field(gt=0)


@dataclass(frozen=True, slots=True)
class Candidate:
    symbol: str
    rsi: float


class PullbackStrategy:
    name = "pullback"
    version = "1"  # bump on any logic change or change of a default in pullback.yaml
    product = Product.CNC
    instrument = "EQ"
    timeframe = "1d"
    reference_symbols: tuple[str, ...] = ()

    def __init__(self, **params: Any) -> None:
        self.p = PullbackParams.model_validate(params)
        self.lookback_sessions = max(self.p.trend_ma_sessions, self.p.exit_ma_sessions, RSI_HISTORY)

    def params(self) -> dict[str, Any]:
        return self.p.model_dump(mode="json")

    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:
        if ctx.session_no_trade or ctx.next_tradeable_session is None:
            return []
        return self.exits(ctx) + self.entries(ctx)

    # --- exits ---

    def exits(self, ctx: StrategyContext) -> list[OrderIntent]:
        exiting = {v.order.symbol for v in ctx.working_orders if v.order.role is OrderRole.EXIT}
        out = []
        for symbol, pos in sorted(ctx.positions.items()):
            if pos.product is not Product.CNC or symbol in exiting:
                continue
            tag = self.exit_tag(ctx, symbol, pos)
            if tag is not None:
                out.append(OrderIntent(IntentKind.EXIT, symbol, Product.CNC, tag=tag))
        return out

    def exit_tag(self, ctx: StrategyContext, symbol: str, pos: PositionView) -> str | None:
        """Why the position exits now, if it does: the average first, then time."""
        bars = ctx.bars(symbol)
        if has_bar_on(bars, ctx.session_date) and above_average(bars, self.p.exit_ma_sessions):
            return "pullback_exit_ma"
        if ctx.sessions_since(pos.entry_time.date()) >= self.p.max_hold_sessions:
            return "pullback_exit_time"
        return None

    # --- entries ---

    def entries(self, ctx: StrategyContext) -> list[OrderIntent]:
        pending = {v.order.symbol for v in ctx.working_orders if v.order.role is OrderRole.ENTRY}
        found = [
            c
            for s in ctx.symbols
            if s not in ctx.positions and s not in pending
            if (c := self.candidate(ctx, s)) is not None
        ]
        found.sort(key=lambda c: (c.rsi, c.symbol))
        return [
            OrderIntent(
                IntentKind.ENTRY, c.symbol, Product.CNC, side=Side.BUY, rank=k, tag="pullback"
            )
            for k, c in enumerate(found, start=1)
        ]

    def candidate(self, ctx: StrategyContext, symbol: str) -> Candidate | None:
        bars = ctx.bars(symbol)
        if not has_bar_on(bars, ctx.session_date):
            return None
        if not above_average(bars, self.p.trend_ma_sessions):
            return None
        rsi = wilder_rsi(bars.close[-RSI_HISTORY:], self.p.rsi_sessions)
        if rsi is None or not rsi < self.p.rsi_entry_below:
            return None
        return Candidate(symbol, rsi)
