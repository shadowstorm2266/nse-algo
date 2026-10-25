"""Synthetic 1-minute bars for data-layer tests."""

from datetime import date

import numpy as np
import pandas as pd

from nsealgo.data.calendar import IST
from nsealgo.data.raw import BAR_COLS


def session_bars(
    symbol: str,
    day: date,
    n: int = 375,
    base: float = 100.0,
    volume: int = 1000,
    seed: int | None = None,
) -> pd.DataFrame:
    """`n` consecutive 1m bars from 09:15 IST on `day`; a random walk if `seed` is set."""
    ts = pd.date_range(f"{day.isoformat()} 09:15", periods=n, freq="min", tz=IST)
    if seed is None:
        close = base + 0.01 * np.arange(n)
    else:
        rng = np.random.default_rng(seed)
        close = base * np.exp(np.cumsum(rng.normal(0, 0.001, n)))
    open_ = np.r_[close[0], close[:-1]]
    df = pd.DataFrame(
        {
            "ts": ts,
            "symbol": symbol,
            "session_date": day,
            "open": open_,
            "high": np.maximum(open_, close) + 0.05,
            "low": np.minimum(open_, close) - 0.05,
            "close": close,
            "volume": np.full(n, volume, dtype="int64"),
        }
    )
    return df[BAR_COLS]


def business_days(start: str, n: int) -> list[date]:
    return [d.date() for d in pd.bdate_range(start, periods=n)]


def many_sessions(symbol: str, days: list[date], seed: int = 0) -> pd.DataFrame:
    parts = [
        session_bars(symbol, d, base=100 + i, volume=1000 + 10 * i, seed=seed + i)
        for i, d in enumerate(days)
    ]
    return pd.concat(parts, ignore_index=True)
