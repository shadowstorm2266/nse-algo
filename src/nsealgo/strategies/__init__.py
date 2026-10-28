"""Strategy registry for the backtest CLI.

Parameters come from config/strategies/<name>.yaml (loaded outside this package, which
does no I/O) with any overrides merged in; `make_strategy` passes them as keywords.
"""

from collections.abc import Callable
from typing import Any

from nsealgo.strategies.base import Strategy
from nsealgo.strategies.orb import OrbStrategy
from nsealgo.strategies.pullback import PullbackStrategy
from nsealgo.strategies.sector_rotation import SectorRotationStrategy
from nsealgo.strategies.swing_momentum import SwingMomentumStrategy

REGISTRY: dict[str, Callable[..., Strategy]] = {
    "orb": OrbStrategy,
    "swing": SwingMomentumStrategy,
    "pullback": PullbackStrategy,
    "sector_rotation": SectorRotationStrategy,
}


def make_strategy(name: str, params: dict[str, Any]) -> Strategy:
    if name not in REGISTRY:
        known = ", ".join(sorted(REGISTRY)) or "registry is empty"
        raise KeyError(f"unknown strategy {name!r} ({known})")
    return REGISTRY[name](**params)
