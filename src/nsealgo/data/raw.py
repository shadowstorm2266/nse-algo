"""Read the raw Kaggle NSE 1-minute CSVs and normalize them.

Raw files are `data/raw/<SYMBOL>_minute.csv` with columns
date (naive IST wall clock, bar start), open, high, low, close, volume.
Prices are already split/bonus adjusted by the source.
"""

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from nsealgo.data.calendar import IST, LAST_BAR_START, SESSION_OPEN

RAW_SUFFIX = "_minute.csv"
PRICE_COLS = ["open", "high", "low", "close"]
BAR_COLS = ["ts", "symbol", "session_date", *PRICE_COLS, "volume"]
_RAW_DTYPES = {c: "float64" for c in PRICE_COLS} | {"volume": "int64", "date": "string"}


def raw_symbols(raw_dir: Path) -> list[str]:
    return sorted(p.name.removesuffix(RAW_SUFFIX) for p in raw_dir.glob(f"*{RAW_SUFFIX}"))


def read_raw(raw_dir: Path, symbol: str) -> pd.DataFrame:
    """Raw rows for one symbol with `ts` tz-aware IST (no filtering)."""
    df = pd.read_csv(raw_dir / f"{symbol}{RAW_SUFFIX}", dtype=_RAW_DTYPES)
    ts = pd.to_datetime(df.pop("date"), format="%Y-%m-%d %H:%M:%S")
    df.insert(0, "ts", ts.dt.tz_localize(IST))
    return df


@dataclass(frozen=True)
class Normalized:
    bars: pd.DataFrame  # BAR_COLS, regular session only, sorted by ts
    raw_session_bars: pd.DataFrame  # session_date, n_raw_bars: every raw row in date range
    out_of_session: pd.DataFrame  # session_date, n_rows dropped outside 09:15-15:29
    off_grid: pd.DataFrame  # session_date, n_rows dropped for non-zero seconds


def normalize(
    raw: pd.DataFrame, symbol: str, start: date, end: date, excluded: Collection[date]
) -> Normalized:
    """Keep [start, end], drop excluded sessions, keep 09:15-15:29 whole-minute bars.

    Raises on duplicate timestamps: which copy is right cannot be decided here.
    """
    df = raw.assign(symbol=symbol, session_date=raw["ts"].dt.date)
    df = df[(df["session_date"] >= start) & (df["session_date"] <= end)]
    raw_counts = _count(df, "n_raw_bars")
    df = df[~df["session_date"].isin(set(excluded))]

    if df["ts"].duplicated().any():
        dups = df.loc[df["ts"].duplicated(keep=False), "ts"]
        raise ValueError(f"{symbol}: {len(dups)} duplicate timestamps, e.g. {dups.iloc[0]}")

    t = df["ts"].dt.time
    in_session = (t >= SESSION_OPEN) & (t <= LAST_BAR_START)
    on_grid = df["ts"].dt.second.eq(0) & df["ts"].dt.microsecond.eq(0)
    bars = df[in_session & on_grid].sort_values("ts", ignore_index=True)
    return Normalized(
        bars=bars[BAR_COLS],
        raw_session_bars=raw_counts,
        out_of_session=_count(df[~in_session], "n_rows"),
        off_grid=_count(df[in_session & ~on_grid], "n_rows"),
    )


def _count(df: pd.DataFrame, name: str) -> pd.DataFrame:
    return df.groupby("session_date").size().rename(name).reset_index()
