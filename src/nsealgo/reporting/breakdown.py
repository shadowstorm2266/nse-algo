"""Breakdowns of one run: trade metrics by year, side or symbol, equity metrics by
calendar year, turnover and costs by the year each leg happened, position-cap skips and
holding periods. Numbers only, no verdicts. Trade and equity definitions are those of
reporting/metrics.py.
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


# --- turnover and costs by the year each leg happened ---

LEG_COLS = ["ts", "side", "value", "charges", "dp_charge", "slippage"]


def legs_from_fills(fills: pd.DataFrame) -> pd.DataFrame:
    """fills.parquet rows as legs (exact: each fill's own charges and slippage)."""
    return fills[LEG_COLS].copy()


def legs_from_trades(trades: pd.DataFrame) -> pd.DataFrame:
    """Two legs per trades.parquet row, for runs written before fills.parquet existed.
    The round trip's charges and slippage sit on the exit leg, so costs by year are exact
    only when entry and exit fall in the same year (always true for MIS)."""
    long = trades["side"] == "long"
    qty = trades["qty"]
    entry = pd.DataFrame(
        {
            "ts": trades["entry_time"],
            "side": long.map({True: "BUY", False: "SELL"}),
            "value": trades["entry_price"] * qty,
            "charges": 0.0,
            "dp_charge": float("nan"),
            "slippage": 0.0,
        }
    )
    exit_ = pd.DataFrame(
        {
            "ts": trades["exit_time"],
            "side": long.map({True: "SELL", False: "BUY"}),
            "value": trades["exit_price"] * qty,
            "charges": trades["costs"],
            "dp_charge": float("nan"),
            "slippage": trades["slippage"],
        }
    )
    return pd.concat([entry, exit_], ignore_index=True)[LEG_COLS]


def yearly_activity(legs: pd.DataFrame, capital: float) -> pd.DataFrame:
    """Per calendar year of the leg: rupees bought and sold, one-way turnover
    ((bought + sold) / 2 / capital), charges (DP before GST shown separately, already in
    charges), slippage, and charges + slippage as a percent of capital."""
    years = pd.to_datetime(legs["ts"]).dt.year
    rows = {}
    for year, g in legs.groupby(years, sort=True):
        buys = float(g.loc[g["side"] == "BUY", "value"].sum())
        sells = float(g.loc[g["side"] == "SELL", "value"].sum())
        charges, slippage = float(g["charges"].sum()), float(g["slippage"].sum())
        dp = g["dp_charge"]
        rows[year] = {
            "buys_rs": buys,
            "sells_rs": sells,
            "turnover_x": (buys + sells) / 2 / capital,
            "charges_rs": charges,
            "dp_rs": float(dp.sum()) if dp.notna().all() else float("nan"),
            "slippage_rs": slippage,
            "costs_rs": charges + slippage,
            "costs_pct_capital": (charges + slippage) / capital * 100,
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def cap_skips(rejections: pd.DataFrame) -> pd.DataFrame:
    """Entries skipped because one share was above the position cap, with the decision
    time, price and rank (rejections.parquet, reason PRICE_ABOVE_POSITION_CAP)."""
    r = rejections[rejections["reason"] == "PRICE_ABOVE_POSITION_CAP"]
    out = r[["now", "symbol", "price", "rank"]].rename(columns={"now": "decision"})
    return out.reset_index(drop=True)


def holding_days(trades: pd.DataFrame) -> pd.Series:
    """Calendar days from entry to the last exit, one value per trade."""
    t = trades.groupby("trade_id", sort=False).agg(
        entry=("entry_time", "first"), exit=("exit_time", "max")
    )
    return (pd.to_datetime(t["exit"]) - pd.to_datetime(t["entry"])).dt.total_seconds() / 86_400
