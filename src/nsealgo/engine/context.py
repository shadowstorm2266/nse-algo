"""What a strategy may see at decision time `now`.

Only bars with available_at <= now, the session's daily features (available_at
09:15), open positions, working orders and today's fills. Arrays are read-only
views; nothing here does I/O or reads a clock. `next_session` is the next date on the
trading calendar (tradeable or not), which the exchange holiday list gives in advance;
`next_tradeable_session` is the next one not marked no_trade.
"""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from nsealgo.engine.market import Series, SessionSlice
from nsealgo.engine.portfolio import PositionView
from nsealgo.engine.types import Fill, OrderView

_EMPTY_F = np.empty(0, dtype="float64")
_EMPTY_F.flags.writeable = False
_EMPTY_I = np.empty(0, dtype="int64")
_EMPTY_I.flags.writeable = False


class BarView:
    """The visible prefix of one symbol's bars."""

    __slots__ = ("_n", "_s")

    def __init__(self, series: Series | None, n: int) -> None:
        self._s, self._n = series, n

    def __len__(self) -> int:
        return self._n

    def _col(self, name: str, empty: np.ndarray) -> np.ndarray:
        return empty if self._s is None else getattr(self._s, name)[: self._n]

    @property
    def ts(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex([], tz="Asia/Kolkata") if self._s is None else self._s.ts[: self._n]

    @property
    def open(self) -> np.ndarray:
        return self._col("open", _EMPTY_F)

    @property
    def high(self) -> np.ndarray:
        return self._col("high", _EMPTY_F)

    @property
    def low(self) -> np.ndarray:
        return self._col("low", _EMPTY_F)

    @property
    def close(self) -> np.ndarray:
        return self._col("close", _EMPTY_F)

    @property
    def volume(self) -> np.ndarray:
        return self._col("volume", _EMPTY_I)

    @property
    def last_close(self) -> float | None:
        return float(self._s.close[self._n - 1]) if self._s is not None and self._n else None


@dataclass(frozen=True, slots=True)
class StrategyContext:
    now: pd.Timestamp
    session_date: date
    session_no_trade: bool
    next_session: date | None  # None after the calendar's last session
    next_tradeable_session: date | None  # skips no_trade sessions; None if none is left
    symbols: tuple[str, ...]
    positions: Mapping[str, PositionView]
    working_orders: tuple[OrderView, ...]
    fills_today: tuple[Fill, ...]
    _slice: SessionSlice
    _now_ns: int

    def bars(self, symbol: str) -> BarView:
        s = self._slice.series.get(symbol)
        return BarView(s, s.visible(self._now_ns) if s is not None else 0)

    def features(self, symbol: str) -> Mapping[str, Any] | None:
        """Today's daily features for `symbol` (from prior sessions), if available."""
        hit = self._slice.features.get(symbol)
        if hit is None or hit[0] > self._now_ns:
            return None
        return hit[1]

    def last_close(self, symbol: str) -> float | None:
        return self.bars(symbol).last_close


class LastCloses(Mapping[str, float]):
    """Lazy symbol -> last visible close, the RiskGovernor's reference prices."""

    def __init__(self, ctx: StrategyContext) -> None:
        self._ctx = ctx

    def __getitem__(self, symbol: str) -> float:
        px = self._ctx.last_close(symbol)
        if px is None:
            raise KeyError(symbol)
        return px

    def __iter__(self) -> Iterator[str]:
        return (s for s in self._ctx.symbols if self._ctx.last_close(s) is not None)

    def __len__(self) -> int:
        return sum(1 for _ in self)
