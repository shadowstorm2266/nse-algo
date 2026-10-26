"""Run metrics from trades and daily equity. Numbers only, no verdicts.

Definitions (per round trip; partial exits of one trade are summed first):
- gross P&L is at reference prices; costs = charges + slippage; net = gross - costs.
- bps figures are means over trades of P&L / entry notional x 10,000.
- profit factor = sum of net wins / |sum of net losses| (None with no losses).
- cost share of gross = (charges + slippage) / gross P&L (None if gross <= 0).
- Sharpe = mean / std (ddof=1) of daily returns x sqrt(252), every session counted.
  A daily return is the session's P&L over the previous session-end equity
  (`current_equity` sizing, compounding) or over capital (`fixed_capital` sizing, where
  sizes do not compound and equity may go below zero).
- Max drawdown from session-end equity: peak minus equity, in rupees and as a percent
  of the running peak (the peak starts at capital), or of capital with `fixed_capital`
  sizing (sizes do not grow with the peak, and equity may be below zero).
"""

import math
from typing import Any

import numpy as np
import pandas as pd

from nsealgo.engine.types import HaltRecord

TRADING_DAYS = 252
SUM_COLS = ["gross_pnl", "costs", "slippage", "net_pnl", "notional"]


def _f(x: Any) -> float | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def trade_metrics(trades: pd.DataFrame) -> dict[str, Any]:
    if trades.empty:
        return (
            {"trades": 0}
            | dict.fromkeys(
                [
                    "win_rate",
                    "avg_win",
                    "avg_loss",
                    "net_expectancy_rs",
                    "net_expectancy_bps",
                    "gross_bps_per_trade",
                    "cost_bps_per_trade",
                    "charges_bps_per_trade",
                    "slippage_bps_per_trade",
                    "profit_factor",
                    "cost_share_of_gross",
                ]
            )
            | {"gross_pnl": 0.0, "charges": 0.0, "slippage": 0.0, "net_pnl": 0.0}
        )
    t = trades.groupby("trade_id", sort=False)[SUM_COLS].sum()
    net, gross, notional = t["net_pnl"], t["gross_pnl"], t["notional"]
    wins, losses = net[net > 0], net[net < 0]
    frictions = t["costs"] + t["slippage"]
    gross_total = float(gross.sum())
    return {
        "trades": len(t),
        "win_rate": len(wins) / len(t),
        "avg_win": _f(wins.mean()) if len(wins) else None,
        "avg_loss": _f(losses.mean()) if len(losses) else None,
        "net_expectancy_rs": float(net.mean()),
        "net_expectancy_bps": float((net / notional * 1e4).mean()),
        "gross_bps_per_trade": float((gross / notional * 1e4).mean()),
        "cost_bps_per_trade": float((frictions / notional * 1e4).mean()),
        "charges_bps_per_trade": float((t["costs"] / notional * 1e4).mean()),
        "slippage_bps_per_trade": float((t["slippage"] / notional * 1e4).mean()),
        "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
        "cost_share_of_gross": float(frictions.sum() / gross_total) if gross_total > 0 else None,
        "gross_pnl": gross_total,
        "charges": float(t["costs"].sum()),
        "slippage": float(t["slippage"].sum()),
        "net_pnl": float(net.sum()),
    }


def equity_metrics(
    equity: pd.DataFrame, capital: float, return_base: float | None = None
) -> dict[str, Any]:
    """`capital` is the equity before the first row. Returns are P&L over the previous
    equity and the drawdown percent is of the running peak, or both are over
    `return_base` when given (fixed-capital sizing)."""
    if equity.empty:
        return {
            "sessions": 0,
            "final_equity": capital,
            "total_return_pct": 0.0,
            "max_drawdown_rs": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_daily_annualized": None,
        }
    eq = equity["equity"].astype(float).to_numpy()
    path = np.r_[capital, eq]
    pnl = np.diff(path)
    rets = pnl / return_base if return_base else pnl / path[:-1]
    peak = np.maximum.accumulate(path)
    dd = peak - path
    sd = rets.std(ddof=1) if len(rets) > 1 else 0.0
    return {
        "sessions": len(eq),
        "final_equity": float(eq[-1]),
        "total_return_pct": float((eq[-1] - capital) / (return_base or capital) * 100),
        "max_drawdown_rs": float(dd.max()),
        "max_drawdown_pct": float(
            dd.max() / return_base * 100 if return_base else (dd / peak).max() * 100
        ),
        "sharpe_daily_annualized": float(rets.mean() / sd * math.sqrt(TRADING_DAYS))
        if sd > 0
        else None,
    }


def compute_metrics(
    trades: pd.DataFrame,
    equity: pd.DataFrame,
    capital: float,
    *,
    halt: HaltRecord | None = None,
    rejections: pd.DataFrame | None = None,
    fallback_exits: int = 0,
    sizing_basis: str = "current_equity",
) -> dict[str, Any]:
    base = capital if sizing_basis == "fixed_capital" else None
    out = trade_metrics(trades) | equity_metrics(equity, capital, base)
    out["sizing_basis"] = sizing_basis
    out["halt_would_fire_date"] = halt.date.isoformat() if halt else None
    out["halt_would_fire_drawdown_pct"] = halt.drawdown_pct if halt else None
    out["fallback_exits"] = fallback_exits
    out["exit_reasons"] = (
        {str(k): int(v) for k, v in trades["exit_reason"].value_counts().items()}
        if not trades.empty
        else {}
    )
    out["rejections_by_reason"] = (
        {str(k): int(v) for k, v in rejections["reason"].value_counts().items()}
        if rejections is not None and not rejections.empty
        else {}
    )
    return out
