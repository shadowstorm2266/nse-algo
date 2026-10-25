"""Resample 1-minute bars to N-minute bars anchored at the 09:15 session open.

Every bar is labelled by its start time `ts` and carries
`available_at = ts + bar length`: the earliest moment a strategy may see it.
"""

import pandas as pd

from nsealgo.data.calendar import BARS_PER_SESSION, session_open_ts

OUT_COLS = [
    "ts",
    "available_at",
    "symbol",
    "session_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "n_bars",
]


def with_available_at(bars: pd.DataFrame, minutes: int) -> pd.DataFrame:
    out = bars.copy()
    out.insert(1, "available_at", out["ts"] + pd.Timedelta(minutes=minutes))
    return out


def resample_bars(bars_1m: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Aggregate 1m bars (columns ts, symbol, session_date, OHLCV) into `minutes` bars.

    Buckets never cross sessions; a bucket with no 1m bars produces no row.
    `n_bars` is how many 1m bars went into each bar.
    """
    if minutes < 1 or BARS_PER_SESSION % minutes:
        raise ValueError(f"{minutes}m does not divide the {BARS_PER_SESSION}-minute session")
    b = bars_1m.sort_values(["symbol", "ts"], ignore_index=True)
    step = pd.Timedelta(minutes=minutes)
    open_ts = session_open_ts(b["ts"])
    if (b["ts"] < open_ts).any():
        raise ValueError("bar before the 09:15 session open")
    start = (open_ts + ((b["ts"] - open_ts) // step) * step).rename("bucket")
    out = (
        b.groupby([b["symbol"], b["session_date"], start], sort=True)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            n_bars=("close", "size"),
        )
        .reset_index()
        .rename(columns={"bucket": "ts"})
    )
    return with_available_at(out, minutes)[OUT_COLS]
