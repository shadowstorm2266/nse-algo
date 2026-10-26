"""The strategy interface. The same strategy object runs in backtest, paper and live.

A strategy is pure: `on_bar(ctx)` depends only on `ctx` and the strategy's own
parameters. No I/O, no clock, no globals, no randomness, no mutable state carried
between calls. It never sizes or places orders: it returns `OrderIntent`s and the
RiskGovernor decides.
"""

from typing import Any, Protocol

from nsealgo.engine.context import StrategyContext
from nsealgo.engine.types import OrderIntent, Product


class Strategy(Protocol):
    name: str
    version: str  # bump on any logic or default-parameter change (holdout runs once per version)
    product: Product  # MIS (intraday) or CNC (swing)
    timeframe: str  # "1m", "5m", "15m" (MIS) or "1d" (CNC)
    lookback_sessions: int  # daily bars of history before the period start ("1d" only)

    def params(self) -> dict[str, Any]: ...

    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]: ...
