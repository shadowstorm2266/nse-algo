"""Daily features computed from prior sessions only.

A feature row for (symbol, session D) uses data from sessions strictly before D
and is available at D's 09:15 open. Windows must be complete: a missing session
inside a window gives NaN. Every feature is NaN until the symbol has
`warmup` prior sessions. Nothing is forward- or back-filled.
"""

from collections.abc import Sequence
from datetime import date

import numpy as np
import pandas as pd

from nsealgo.data.calendar import IST, SESSION_OPEN_OFFSET

FEATURE_COLS = [
    "symbol",
    "session_date",
    "available_at",
    "prior_sessions",
    "prev_high",
    "prev_low",
    "prev_close",
    "atr14",
    "zero_vol_share_20d",
]
RVOL_COLS = ["symbol", "session_date", "ts", "tod", "avg_volume_20d"]


def daily_bars(bars_1m: pd.DataFrame) -> pd.DataFrame:
    """Per (symbol, session): OHLCV, bar count, zero-volume bar count and rupee turnover."""
    b = bars_1m.sort_values(["symbol", "ts"]).assign(
        zero_vol=lambda x: x["volume"].eq(0),
        turnover=lambda x: x["close"] * x["volume"],
    )
    return (
        b.groupby(["symbol", "session_date"], sort=True)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            n_bars=("close", "size"),
            zero_vol_bars=("zero_vol", "sum"),
            turnover=("turnover", "sum"),
        )
        .reset_index()
    )


def _session_open(sessions: pd.Index) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(list(sessions))).tz_localize(IST) + SESSION_OPEN_OFFSET


def daily_features(
    daily: pd.DataFrame,
    sessions: Sequence[date],
    warmup: int = 20,
    atr_period: int = 14,
    avg_window: int = 20,
) -> pd.DataFrame:
    """Features for one symbol's daily bars on the calendar `sessions`.

    Rows are returned only for sessions where the symbol has data.
    """
    symbol = daily["symbol"].iloc[0]
    d = daily.set_index("session_date").reindex(pd.Index(sessions, name="session_date"))
    present = d["close"].notna()
    prior = present.cumsum().shift(1, fill_value=0).astype("int64")

    prev = d[["high", "low", "close"]].shift(1)
    true_range = pd.concat(
        [d["high"] - d["low"], (d["high"] - prev["close"]).abs(), (d["low"] - prev["close"]).abs()],
        axis=1,
    ).max(axis=1, skipna=False)
    zero_sum = d["zero_vol_bars"].rolling(avg_window, min_periods=avg_window).sum()
    bars_sum = d["n_bars"].rolling(avg_window, min_periods=avg_window).sum()

    out = pd.DataFrame(
        {
            "prev_high": prev["high"],
            "prev_low": prev["low"],
            "prev_close": prev["close"],
            "atr14": true_range.rolling(atr_period, min_periods=atr_period).mean().shift(1),
            "zero_vol_share_20d": (zero_sum / bars_sum).shift(1),
        },
        index=d.index,
    )
    out = out.mask(prior < warmup, np.nan)
    out.insert(0, "prior_sessions", prior)
    out.insert(0, "available_at", _session_open(d.index))
    out.insert(0, "symbol", symbol)
    return out[present].reset_index()[FEATURE_COLS]


def rvol_profile(bars_5m: pd.DataFrame, sessions: Sequence[date], window: int = 20) -> pd.DataFrame:
    """Average 5m-bucket volume over the prior `window` sessions, per time of day.

    `sessions` should list only complete sessions plus the ones to score: a session
    left out (e.g. a partial no_trade day) neither enters nor breaks the window.
    Returns one row per (session where the symbol has data, tod "HH:MM").
    """
    symbol = bars_5m["symbol"].iloc[0]
    b = bars_5m.assign(tod=bars_5m["ts"].dt.strftime("%H:%M"))
    wide = b.pivot_table(index="session_date", columns="tod", values="volume", aggfunc="sum")
    wide = wide.reindex(pd.Index(sessions, name="session_date"))
    present = wide.notna().any(axis=1)
    avg = wide.rolling(window, min_periods=window).mean().shift(1)[present]
    long = avg.stack(future_stack=True).rename("avg_volume_20d").reset_index()
    long.insert(0, "symbol", symbol)
    # Exact bucket start, so joins to 5m bars match on ts without timezone formatting.
    midnight = pd.to_datetime(long["session_date"]).dt.tz_localize(IST)
    long["ts"] = midnight + pd.to_timedelta(long["tod"] + ":00")
    return long[RVOL_COLS]
