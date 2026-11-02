"""IPO v2 evaluation (research/ipo_v2_plan.md sections 5-8). It runs the Monte Carlo over
the evaluation set with IPO v1's engine, the v1-rules comparison, the Nifty 50 TRI
benchmark and the checks.

No file I/O. scripts/evaluate_ipo_v2.py builds the issue table (ISSUE_COLS) from the
recorded files and decides whether the evaluation may run at all; this module only
computes. The v1 functions (issue_terms, pnl_paise, one_lot_chance, sim_input) are reused
unchanged: blocking, costs and allotment are "exactly as IPO v1".
"""

from datetime import date
from decimal import Decimal

import numpy as np
import pandas as pd

from nsealgo.costs import CostConfig, IpoCosts
from nsealgo.data.etf_proxy import accrual_factor
from nsealgo.engine.ipo_sim import SimInput, TradingDays, draws, simulate
from nsealgo.strategies.ipo_v1 import issue_terms, one_lot_chance, pnl_paise, sim_input
from nsealgo.strategies.ipo_v2 import IpoV2Config

TIERS = ("none", "base", "stress1", "stress2")
ISSUE_COLS = [
    "issue_id",
    "status",  # listed | withdrawn
    "decision",  # apply | skip
    "total_x",  # total subscription at the decision snapshot
    "issue_close",  # last bid day D
    "lot_size",
    "price_band_high",
    "retail_discount",
    "issue_price",
    "listing_date",
    "list_open",
    "list_close",
    "allotment_date",
    "p_1lot",  # from the advert, NaN if it gives none
    "retail_sub_exch",  # retail times in the final book (for an estimated p)
    "retail_shares_applied",
    "retail_valid_applications",
]


def set_k(df: pd.DataFrame) -> float | None:
    """Median average lots per valid retail application over the set's issues with a
    parsed 1-lot chance (plan section 5); None if there is none."""
    ok = (
        (df["status"] == "listed")
        & df["p_1lot"].notna()
        & df["retail_shares_applied"].notna()
        & (pd.to_numeric(df["retail_valid_applications"]) > 0)
    )
    rows = df[ok]
    if rows.empty:
        return None
    avg = rows["retail_shares_applied"].astype(float) / rows["lot_size"]
    return float((avg / rows["retail_valid_applications"].astype(float)).median())


def chances(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """(p, estimated) per issue: the advert's 1-lot chance, else v1's estimate with the
    set's k (one_lot_chance raises if an estimate is needed and impossible)."""
    k = set_k(df)
    years = {d.year for d in df["issue_close"]}
    return one_lot_chance(df, {y: k for y in years} if k is not None else {})


def v2_order_keys(df: pd.DataFrame, n_runs: int) -> np.ndarray:
    """Same-day order keys (runs x issues): rank by total subscription, highest first,
    ties by issue_id; the same in every run (plan section 5)."""
    order = sorted(range(len(df)), key=lambda i: (-df["total_x"].iloc[i], df["issue_id"].iloc[i]))
    rank = np.empty(len(df), dtype=np.float64)
    rank[order] = np.arange(len(df))
    return np.broadcast_to(rank, (n_runs, len(df))).copy()


def net_stats(x: SimInput, capital: int, u: np.ndarray, keys: np.ndarray) -> dict:
    """Simulate and summarise net profit in Rs (final equity - capital) over runs."""
    res = simulate(x, capital, u, keys)
    net = (res.final_cash - capital) / 100
    return {
        "mean_rs": float(net.mean()),
        "median_rs": float(np.median(net)),
        "p5_rs": float(np.percentile(net, 5)),
        "p95_rs": float(np.percentile(net, 95)),
        "p_loss": float((net < 0).mean()),
        "applications_mean": float(res.applied.sum(axis=1).mean()),
        "allotments_mean": float(res.allotted.sum(axis=1).mean()),
        "skipped_cash_mean": float((res.skipped_blocked | res.skipped_capital).sum(axis=1).mean()),
    }


def benchmark(tri: pd.Series, first_day: date, end: date, capital_rs: float, pct: float) -> dict:
    """Rs `capital_rs` in the TRI from the close of the last session before `first_day`
    to the last session on or before `end`, less `pct` a year (v1 section 8)."""
    before = [d for d in tri.index if d < first_day]
    upto = [d for d in tri.index if d <= end]
    if not before or not upto:
        raise ValueError(f"TRI does not cover {first_day} to {end}")
    base, last = max(before), max(upto)
    growth = float(tri[last]) / float(tri[base])
    value = capital_rs * growth * float(accrual_factor(np.array([(last - base).days]), pct)[0])
    return {
        "base": base.isoformat(),
        "end": last.isoformat(),
        "value_rs": value,
        "end_short": last < end,
    }


def end_date(df: pd.DataFrame, days: TradingDays, cfg: IpoV2Config) -> date:
    """E: the latest listing date +2 trading days (the last possible release), or the
    latest bid close if nothing listed."""
    listed = df.loc[df["status"] == "listed", "listing_date"]
    if listed.empty:
        return max(df["issue_close"])
    return days.after(max(listed), cfg.release.allotted_days_after_listing)


def _check(n: int, what: str, value: object, ok: bool | None) -> dict:
    result = "REPORTED" if ok is None else ("PASS" if ok else "FAIL")
    return {"check": n, "what": what, "value": value, "result": result}


def checks(tiers: dict, v1: dict, bench: dict, capital_rs: float) -> list[dict]:
    """The plan's checks (section 8); strict inequalities, a tie fails."""
    v2_eq, v1_eq = capital_rs + tiers["base"]["mean_rs"], capital_rs + v1["mean_rs"]
    s2, b, bv = tiers["stress2"]["mean_rs"], tiers["base"], bench["value_rs"]
    return [
        _check(1, "mean net profit > 0 at stress2", s2, s2 > 0),
        _check(2, "mean v2 final equity > mean v1-rules final equity (base)", [v2_eq, v1_eq],
               v2_eq > v1_eq),
        _check(3, "mean v2 final equity > Nifty 50 TRI value at E (base)", [v2_eq, bv], v2_eq > bv),
        _check(4, "base: median, p5 net profit, P(loss)", [b["median_rs"], b["p5_rs"], b["p_loss"]],
               None),
    ]  # fmt: skip


def evaluate(
    df: pd.DataFrame,
    days: TradingDays,
    cfg: IpoV2Config,
    costs: CostConfig,
    ipo_costs: IpoCosts,
    tri: pd.Series,
    n_runs: int | None = None,
) -> dict:
    """The whole evaluation of one set (ISSUE_COLS rows). `n_runs` overrides the plan's
    10,000 for tests only."""
    df = df.sort_values(["issue_close", "issue_id"]).reset_index(drop=True)
    terms = issue_terms(df, days, cfg)  # uses cfg.release, as v1
    p, est = chances(df)
    runs = n_runs or cfg.monte_carlo.runs
    u, random_keys = draws(runs, len(df), cfg.monte_carlo.seed)
    capital = cfg.capital_rupees * 100
    idx = np.flatnonzero((df["decision"] == "apply").to_numpy())
    sub, sub_terms = df.iloc[idx], terms.iloc[idx]
    keys = v2_order_keys(sub, runs)
    tiers = {}
    for tier in TIERS:
        slip = Decimal(ipo_costs.listing_slippage_pct[tier])
        pnl = pnl_paise(sub, sub_terms, "list_close", slip, costs, ipo_costs)
        tiers[tier] = net_stats(sim_input(sub_terms, p.iloc[idx], pnl), capital, u[:, idx], keys)
    base_slip = Decimal(ipo_costs.listing_slippage_pct["base"])
    v1_pnl = pnl_paise(df, terms, "list_open", base_slip, costs, ipo_costs)
    v1 = net_stats(sim_input(terms, p, v1_pnl), capital, u, random_keys)
    end = end_date(df, days, cfg)
    bench = benchmark(
        tri, min(df["issue_close"]), end, cfg.capital_rupees, cfg.benchmark.expense_ratio_pct
    )
    return {
        "issues": len(df),
        "applies": len(idx),
        "estimated_p": df.loc[est, "issue_id"].tolist(),
        "set_k": set_k(df),
        "first_bid_close": min(df["issue_close"]).isoformat(),
        "end_date": end.isoformat(),
        "runs": runs,
        "tiers": tiers,
        "v1_rules_base": v1,
        "benchmark": bench,
        "checks": checks(tiers, v1, bench, cfg.capital_rupees),
        "days_past_calendar": sorted(d.isoformat() for d in days.extended),
    }
