"""Benchmarks and attribution for reports. Not strategies and not trials: nothing here
goes through the RiskGovernor or is logged to research/trials.jsonl. Numbers only.

- `buy_and_hold`: equal-weight buy-and-hold of every symbol in the bars, fractional
  shares, bought once at the first session's open, never rebalanced.
- `symbol_contribution` / `without_symbols`: a run's session-end equity with some
  symbols' trades taken out (their fills' cash flows and their holdings at each close).

Bars are daily: symbol, session_date, open, close.
"""

from collections.abc import Sequence
from decimal import Decimal

import pandas as pd

from nsealgo.costs import BrokerageModel, StatutoryRates, fill_charges


def _closes(bars: pd.DataFrame, sessions: pd.Index) -> pd.DataFrame:
    """Closes by session x symbol on `sessions`, the last close carried over a gap."""
    c = bars.assign(session_date=pd.to_datetime(bars["session_date"]))
    wide = c.pivot(index="session_date", columns="symbol", values="close").sort_index()
    return wide.reindex(wide.index.union(sessions)).ffill().reindex(sessions)


def buy_and_hold(
    bars: pd.DataFrame,
    capital: float,
    rates: StatutoryRates,
    delivery: BrokerageModel,
    slippage_bps: Decimal,
) -> pd.DataFrame:
    """Session-end equity (session_date, equity) of an equal-weight buy-and-hold.

    Every symbol in `bars` needs a bar on the first session. Each gets capital / n: one
    CNC buy's charges (on that share) come out of it, the rest buys fractional shares
    at the first open plus `slippage_bps`, and the few paise left stay in cash. No sell
    costs: holdings are marked at each session's close.
    """
    days = sorted(bars["session_date"].unique())
    first = bars[bars["session_date"] == days[0]].set_index("symbol")
    symbols = sorted(bars["symbol"].unique())
    missing = sorted(set(symbols) - set(first.index))
    if missing:
        raise ValueError(f"no bar on the first session {days[0]} for {missing}")
    share = Decimal(str(capital)) / len(symbols)
    cash, qty = Decimal(0), {}
    for s in symbols:
        value = share - fill_charges("CNC", "BUY", share, rates, delivery).total
        cash += share - value - fill_charges("CNC", "BUY", value, rates, delivery).total
        price = Decimal(str(first.at[s, "open"])) * (1 + slippage_bps / 10_000)
        qty[s] = float(value / price)
    closes = _closes(bars, pd.Index(pd.to_datetime(days)))
    equity = float(cash) + (closes[symbols] * pd.Series(qty)).sum(axis=1)
    return pd.DataFrame({"session_date": days, "equity": equity.to_numpy()})


def symbol_contribution(
    fills: pd.DataFrame, bars: pd.DataFrame, symbol: str, sessions: Sequence
) -> pd.Series:
    """`symbol`'s part of a run's session-end equity on each of `sessions`: the cash
    flows of its fills so far (a sale adds its value, a buy subtracts it, every fill
    pays its charges) plus the shares held at that session's close. Fill values are at
    fill prices, so slippage is in them."""
    idx = pd.Index(pd.to_datetime(list(sessions)))
    f = fills[fills["symbol"] == symbol]
    buy = f["side"] == "BUY"
    days = pd.to_datetime(f["session_date"])

    def to_date(x: pd.Series) -> pd.Series:
        return x.groupby(days).sum().reindex(idx, fill_value=0).cumsum()

    flows = to_date(f["value"].where(~buy, -f["value"]) - f["charges"])
    held = to_date(f["qty"].where(buy, -f["qty"]))
    mark = (held * _closes(bars[bars["symbol"] == symbol], idx)[symbol]).where(held != 0, 0.0)
    if mark.isna().any():
        raise ValueError(f"{symbol} is held on a session without a close")
    return (flows + mark).rename(symbol)


def without_symbols(
    equity: pd.DataFrame, fills: pd.DataFrame, bars: pd.DataFrame, symbols: Sequence[str]
) -> pd.DataFrame:
    """`equity` (session_date, equity) minus `symbols`' contributions: the run with
    their trades taken out and everything else unchanged. Under current-equity sizing,
    later trades were still sized off an account that included those trades."""
    sessions = equity["session_date"].tolist()
    out = equity[["session_date"]].copy()
    out["equity"] = equity["equity"].astype(float).to_numpy()
    for s in symbols:
        out["equity"] -= symbol_contribution(fills, bars, s, sessions).to_numpy()
    return out
