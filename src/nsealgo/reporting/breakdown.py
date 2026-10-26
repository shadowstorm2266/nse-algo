"""Breakdowns of one run: trade metrics by year, side or symbol, and equity metrics by
calendar year. Numbers only, no verdicts. Definitions are those of reporting/metrics.py.
"""

import pandas as pd

from nsealgo.reporting.metrics import equity_metrics, trade_metrics


def breakdown(trades: pd.DataFrame, key: str | pd.Series) -> pd.DataFrame:
    """`trade_metrics` for each value of `key` (a column or a per-row Series), one row
    per value in sorted order. Rows of one trade (partial exits) must share the key."""
    keys = trades[key] if isinstance(key, str) else key
    rows = {k: trade_metrics(sub) for k, sub in trades.groupby(keys, sort=True)}
    return pd.DataFrame.from_dict(rows, orient="index")


def entry_year(trades: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(trades["entry_time"]).dt.year.rename("year")


def yearly_equity(equity: pd.DataFrame, capital: float, fixed_capital: bool) -> pd.DataFrame:
    """`equity_metrics` per calendar year. Each year starts from the previous year's last
    session-end equity (the first from `capital`), so returns and drawdowns are in-year.
    With fixed-capital sizing, returns and the drawdown percent are over `capital` in
    every year (a year can start below zero)."""
    years = pd.to_datetime(equity["session_date"]).dt.year
    rows, start = {}, capital
    base = capital if fixed_capital else None
    for year, sub in equity.groupby(years, sort=True):
        rows[year] = equity_metrics(sub, start, base)
        start = float(sub["equity"].iloc[-1])
    return pd.DataFrame.from_dict(rows, orient="index")
