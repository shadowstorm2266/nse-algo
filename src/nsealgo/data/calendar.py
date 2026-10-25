"""Session constants and the trading calendar derived from the data.

A session is one NSE trading day. Regular 1-minute bars are labelled by their
start time, 09:15 .. 15:29 IST: 375 bars.
"""

from collections.abc import Mapping
from datetime import date, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

IST = ZoneInfo("Asia/Kolkata")
SESSION_OPEN = time(9, 15)
LAST_BAR_START = time(15, 29)
BARS_PER_SESSION = 375
SESSION_OPEN_OFFSET = pd.Timedelta(hours=9, minutes=15)

CALENDAR_COLS = ["session_date", "n_symbols", "max_bars", "no_trade", "no_trade_reason"]


def session_open_ts(ts: pd.Series) -> pd.Series:
    """09:15 IST on the same day as each tz-aware IST timestamp."""
    return ts.dt.normalize() + SESSION_OPEN_OFFSET


def load_holidays(path: Path) -> set[date]:
    """Dates from config/holidays.csv (comment lines start with '#'). Empty file -> empty set."""
    df = pd.read_csv(path, comment="#", dtype=str)
    return {date.fromisoformat(d.strip()) for d in df["date"].dropna()}


def build_calendar(
    session_bars: pd.DataFrame,
    no_trade: Mapping[date, str],
    holidays: set[date],
) -> pd.DataFrame:
    """One row per session present in the clean data.

    `session_bars` has one row per (symbol, session_date) with column `n_bars`.
    Raises if a listed holiday has data (the holidays file would be wrong).
    """
    cal = (
        session_bars.groupby("session_date")
        .agg(n_symbols=("symbol", "nunique"), max_bars=("n_bars", "max"))
        .reset_index()
        .sort_values("session_date", ignore_index=True)
    )
    clash = sorted(set(cal["session_date"]) & holidays)
    if clash:
        raise ValueError(f"holidays.csv lists dates that have data: {clash}")
    cal["no_trade"] = cal["session_date"].isin(set(no_trade))
    cal["no_trade_reason"] = cal["session_date"].map(lambda d: no_trade.get(d, ""))
    return cal[CALENDAR_COLS]


def classify_short_sessions(
    raw_session_bars: pd.DataFrame,
    excluded: Mapping[date, str],
    no_trade: Mapping[date, str],
    threshold: int,
) -> pd.DataFrame:
    """Sessions with fewer than `threshold` raw 1m bars (max over symbols), with their status.

    `raw_session_bars` has columns symbol, session_date, n_raw_bars (all raw rows in the
    clean date range, before any filter). Status is excluded / no_trade / UNCLASSIFIED.
    Raises if an excluded session is not short: dropping a full session is a config error.
    """
    per_day = raw_session_bars.groupby("session_date")["n_raw_bars"].max()
    full_excluded = sorted(d for d in excluded if per_day.get(d, 0) >= threshold)
    if full_excluded:
        raise ValueError(f"excluded sessions have full data, check config: {full_excluded}")
    short = per_day[per_day < threshold]
    rows = []
    for d, n in short.items():
        if d in excluded:
            status, reason = "excluded", excluded[d]
        elif d in no_trade:
            status, reason = "no_trade", no_trade[d]
        else:
            status, reason = "UNCLASSIFIED", ""
        rows.append({"session_date": d, "max_raw_bars": int(n), "status": status, "reason": reason})
    return pd.DataFrame(rows, columns=["session_date", "max_raw_bars", "status", "reason"])


def tradeable_sessions(calendar: pd.DataFrame) -> list[date]:
    """Sessions on which the engine may open trades (no_trade sessions removed)."""
    return list(calendar.loc[~calendar["no_trade"], "session_date"])
