"""Strategy registry for the backtest CLI. No real strategy is implemented yet."""

from collections.abc import Callable
from typing import Any

from nsealgo.strategies.base import Strategy

REGISTRY: dict[str, Callable[..., Strategy]] = {}


def make_strategy(name: str, params: dict[str, Any]) -> Strategy:
    if name not in REGISTRY:
        known = ", ".join(sorted(REGISTRY)) or "registry is empty"
        raise KeyError(f"unknown strategy {name!r} ({known})")
    return REGISTRY[name](**params)
