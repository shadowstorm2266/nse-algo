"""In-memory bars for one backtest chunk, as read-only numpy arrays.

Intraday: one `Series` per (session, symbol). Daily: one `Series` per symbol over
the whole chunk (lookback sessions included), so a strategy sees its history.
Each session yields its decision steps: (bar start, available_at) in time order.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any

import numpy as np
import pandas as pd

from nsealgo.brokers.fills import Bar
from nsealgo.data.calendar import IST
from nsealgo.engine.sessions import TIMEFRAMES

BAR_COLS = [
    "ts",
    "available_at",
    "symbol",
    "session_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
]
FEATURE_KEYS = ("symbol", "session_date", "available_at")
EMPTY_STEPS: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class Series:
    """One symbol's bars in time order. Arrays are read-only views."""

    symbol: str
    ts: pd.DatetimeIndex
    ts_ns: np.ndarray
    avail_ns: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray

    def visible(self, now_ns: int) -> int:
        """How many bars have available_at <= now."""
        return int(np.searchsorted(self.avail_ns, now_ns, side="right"))

    def index_at(self, t_ns: int) -> int | None:
        i = int(np.searchsorted(self.ts_ns, t_ns))
        return i if i < len(self.ts_ns) and self.ts_ns[i] == t_ns else None

    def bar(self, i: int) -> Bar:
        t = self.ts[i]
        return Bar(self.symbol, t, t.date(), self.open[i], self.high[i], self.low[i], self.close[i])


@dataclass(frozen=True, slots=True)
class SessionSlice:
    day: date
    series: Mapping[str, Series]
    steps: tuple[tuple[int, int], ...]  # (bar start ns, available_at ns)
    features: Mapping[str, tuple[int, Mapping[str, Any]]]  # symbol -> (available_at ns, row)


def _ns(col: pd.Series) -> np.ndarray:
    idx = pd.DatetimeIndex(col)
    if idx.tz is None:
        raise ValueError("timestamps must be tz-aware")
    return idx.tz_convert(IST).as_unit("ns").asi8


def _days(col: pd.Series) -> np.ndarray:
    return pd.to_datetime(col).to_numpy().astype("datetime64[D]")


def _readonly(a: np.ndarray) -> np.ndarray:
    a = np.ascontiguousarray(a)
    a.flags.writeable = False
    return a


class MarketData:
    """Bars and daily features for the sessions in `run_sessions` (plus any history)."""

    def __init__(
        self,
        timeframe: str,
        bars: pd.DataFrame,
        run_sessions: Sequence[date],
        features: pd.DataFrame | None = None,
    ) -> None:
        if timeframe not in TIMEFRAMES:
            raise ValueError(f"unknown timeframe {timeframe!r}")
        self.timeframe = timeframe
        self.daily = timeframe == "1d"
        self.run_sessions = tuple(run_sessions)
        b = bars[BAR_COLS].sort_values(["symbol", "ts"], ignore_index=True)
        self._load_arrays(b)
        self._features = self._group_features(features)

    def _load_arrays(self, b: pd.DataFrame) -> None:
        ts_ns, avail_ns = _ns(b["ts"]), _ns(b["available_at"])
        if len(b) and len(np.unique(avail_ns - ts_ns)) != 1:
            raise ValueError("bars of mixed lengths (available_at - ts is not constant)")
        self._ts = pd.DatetimeIndex(b["ts"]).tz_convert(IST).as_unit("ns")
        self._a = {
            "ts_ns": _readonly(ts_ns),
            "avail_ns": _readonly(avail_ns),
            **{c: _readonly(b[c].to_numpy("float64")) for c in ("open", "high", "low", "close")},
            "volume": _readonly(b["volume"].to_numpy("int64")),
        }
        self._symbols = b["symbol"].to_numpy(dtype=object)
        self._days = _days(b["session_date"])
        self._bounds = self._group_bounds()
        order = np.lexsort((ts_ns, self._days))
        days, stamps, avail = self._days[order], ts_ns[order], avail_ns[order]
        self._steps: dict[np.datetime64, tuple[tuple[int, int], ...]] = {}
        for d in np.unique(days):
            lo, hi = np.searchsorted(days, d, "left"), np.searchsorted(days, d, "right")
            uniq, first = np.unique(stamps[lo:hi], return_index=True)
            self._steps[d] = tuple(zip(uniq.tolist(), avail[lo:hi][first].tolist(), strict=True))

    def _group_bounds(self) -> dict[Any, dict[str, tuple[int, int]]]:
        """day (None for daily) -> symbol -> [start, end) rows in the symbol-sorted arrays."""
        n = len(self._symbols)
        if n == 0:
            return {}
        change = np.ones(n, dtype=bool)
        codes = pd.factorize(self._symbols)[0]
        change[1:] = codes[1:] != codes[:-1]
        if not self.daily:
            change[1:] |= self._days[1:] != self._days[:-1]
        starts = np.flatnonzero(change)
        ends = np.r_[starts[1:], n].astype(int)
        bounds: dict[Any, dict[str, tuple[int, int]]] = {}
        for lo, hi in zip(starts.tolist(), ends.tolist(), strict=True):
            key = None if self.daily else self._days[lo]
            bounds.setdefault(key, {})[self._symbols[lo]] = (lo, hi)
        return bounds

    def _series(self, symbol: str, lo: int, hi: int) -> Series:
        a = self._a
        return Series(
            symbol,
            self._ts[lo:hi],
            *(a[k][lo:hi] for k in ("ts_ns", "avail_ns", "open", "high", "low", "close", "volume")),
        )

    @staticmethod
    def _group_features(f: pd.DataFrame | None) -> dict[np.datetime64, dict[str, Any]]:
        if f is None or f.empty:
            return {}
        cols = [c for c in f.columns if c not in FEATURE_KEYS]
        out: dict[np.datetime64, dict[str, Any]] = {}
        days, avail = _days(f["session_date"]), _ns(f["available_at"])
        rows = f[cols].to_dict("records")
        for d, sym, t, row in zip(days, f["symbol"], avail, rows, strict=True):
            out.setdefault(d, {})[sym] = (int(t), MappingProxyType(row))
        return out

    def session(self, day: date) -> SessionSlice:
        d = np.datetime64(day, "D")
        rows = self._bounds.get(None if self.daily else d, {})
        series = {s: self._series(s, lo, hi) for s, (lo, hi) in rows.items()}
        return SessionSlice(
            day=day,
            series=MappingProxyType(series),
            steps=self._steps.get(d, EMPTY_STEPS),
            features=MappingProxyType(self._features.get(d, {})),
        )
