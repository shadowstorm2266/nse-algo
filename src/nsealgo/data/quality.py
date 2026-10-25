"""Data-quality checks. They flag problems; callers decide what is dropped and log it.

Event rows (for research/data_quality_events.csv) have EVENT_COLS.
"""

from typing import Any

import pandas as pd

from nsealgo.data.raw import PRICE_COLS

EVENT_COLS = ["symbol", "session_date", "ts", "kind", "action", "detail"]


def event(
    symbol: str, session_date: Any, kind: str, action: str, detail: str, ts: Any = ""
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "session_date": session_date,
        "ts": str(ts),
        "kind": kind,
        "action": action,
        "detail": detail,
    }


def nonpositive_mask(bars: pd.DataFrame) -> pd.Series:
    """Rows with any of open/high/low/close <= 0."""
    return (bars[PRICE_COLS] <= 0).any(axis=1)


def ohlc_inconsistent_mask(bars: pd.DataFrame, tol: float = 1e-9) -> pd.Series:
    """Rows where high is not the max or low is not the min of the four prices."""
    px = bars[PRICE_COLS]
    return (bars["high"] < px.max(axis=1) - tol) | (bars["low"] > px.min(axis=1) + tol)


def bad_print_mask(bars: pd.DataFrame, max_dev: float, lookaround: int) -> pd.Series:
    """1m bars with a price far from BOTH the median close of the previous and the next
    `lookaround` bars of the same session. Bars must be sorted by ts.

    A genuine jump has its pre-jump prices near the 'before' median and its
    post-jump prices near the 'after' median, so it is not flagged; a one-off
    spike is far from both. At a session edge only the available side is used.
    """
    g = bars.groupby("session_date", sort=False)["close"]
    before = g.transform(lambda s: s.shift(1).rolling(lookaround, min_periods=1).median())
    after = g.transform(
        lambda s: s.iloc[::-1].shift(1).rolling(lookaround, min_periods=1).median().iloc[::-1]
    )
    has_ref = before.notna() | after.notna()
    bad = pd.Series(False, index=bars.index)
    for col in PRICE_COLS:
        p = bars[col]
        far_before = before.isna() | ((p / before - 1).abs() > max_dev)
        far_after = after.isna() | ((p / after - 1).abs() > max_dev)
        bad |= far_before & far_after & has_ref
    return bad


def overnight_moves(daily: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Sessions whose open is more than `threshold` away from the previous present
    session's close (one symbol's daily bars, sorted)."""
    prev_close = daily["close"].shift(1)
    move = daily["open"] / prev_close - 1
    out = daily.assign(prev_close=prev_close, move=move)
    return out.loc[move.abs() > threshold, ["session_date", "prev_close", "open", "move"]]


def out_of_line_days(daily: pd.DataFrame, window: int, low: float, high: float) -> pd.DataFrame:
    """'Different company' check: closes outside [low, high] x a centered rolling median.

    QA only: the centered window looks ahead, so this must never feed a strategy.
    """
    ref = daily["close"].rolling(window, center=True, min_periods=window // 4).median()
    ratio = daily["close"] / ref
    out = daily.assign(ref=ref, ratio=ratio)
    return out.loc[(ratio < low) | (ratio > high), ["session_date", "close", "ref", "ratio"]]
