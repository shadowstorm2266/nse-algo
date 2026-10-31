"""IPO v1 reporting (research/ipo_strategy_plan.md sections 7-11): per-run yearly net
profit and returns from a simulation, Monte Carlo statistics, the Nifty 50 TRI benchmark,
the first-pass checks and markdown tables. Numbers only: no verdict beyond each check's
PASS / FAIL / REPORTED.

Money in a summary is rupees, returns are percent. A year's net profit is the P&L of sales
listed in that year less tax paid in it; its return is over the equity at the end of the
previous year (the capital for the first year).
"""

from datetime import date

import numpy as np
import pandas as pd

from nsealgo.data.etf_proxy import accrual_factor
from nsealgo.engine.ipo_sim import SimInput, SimResult

COUNTS = ("applications", "allotments", "skipped_blocked", "skipped_capital")


def _onehot(of_issue: np.ndarray, years: list[int]) -> np.ndarray:
    if not np.isin(of_issue, years).all():
        raise ValueError(f"issue years {sorted(set(of_issue) - set(years))} outside {years}")
    return (of_issue[:, None] == np.array(years)[None, :]).astype(np.int64)


def yearly_net(res: SimResult, x: SimInput, years: list[int]) -> np.ndarray:
    """(runs, years) net profit in paise."""
    net = res.allotted.astype(np.int64) @ (x.pnl[:, None] * _onehot(x.pnl_year, years))
    for j, y in enumerate(years):
        net[:, j] -= res.tax_paid.get(y, 0)
    if set(res.tax_paid) - set(years):
        raise ValueError("tax paid outside the reported years")
    return net


def _stats(a: np.ndarray) -> dict[str, float]:
    p5, p50, p95 = np.percentile(a, [5, 50, 95])
    return {"mean": float(a.mean()), "median": float(p50), "p5": float(p5), "p95": float(p95)}


def _mm(a: np.ndarray) -> dict[str, float]:
    return {"median": float(np.median(a)), "mean": float(a.mean())}


def _counts(res: SimResult, x: SimInput, years: list[int]) -> dict[str, np.ndarray]:
    hot = _onehot(x.count_year, years)
    masks = (res.applied, res.allotted, res.skipped_blocked, res.skipped_capital)
    return {name: m.astype(np.int64) @ hot for name, m in zip(COUNTS, masks, strict=True)}


def summarize(res: SimResult, x: SimInput, years: list[int], capital: int) -> dict:
    """Statistics over runs, by year and overall (capital and amounts in paise in)."""
    net = yearly_net(res, x, years)
    total = res.final_cash - capital
    if (net.sum(axis=1) != total).any():
        raise AssertionError("yearly net profits do not add up to the final cash")
    end = capital + np.cumsum(net, axis=1)
    start = np.column_stack([np.full(len(net), capital), end[:, :-1]])
    ret = net / start * 100
    counts = _counts(res, x, years)
    out_years = {}
    for j, y in enumerate(years):
        out_years[str(y)] = {
            "net_rs": _stats(net[:, j] / 100),
            "net_pct": _stats(ret[:, j]),
            **{name: _mm(c[:, j]) for name, c in counts.items()},
            "p_loss": float((net[:, j] < 0).mean()),
        }
    overall = {
        "net_rs": _stats(total / 100),
        "net_pct": _stats(total / capital * 100),
        **{name: _mm(c.sum(axis=1)) for name, c in counts.items()},
        "p_losing_year": float((net < 0).any(axis=1).mean()),
    }
    rank = np.lexsort((np.arange(len(total)), total))[(len(total) - 1) // 2]
    median_run = {
        "run": int(rank),
        "total_pct": float(total[rank] / capital * 100),
        "years_pct": {str(y): float(ret[rank, j]) for j, y in enumerate(years)},
    }
    return {"years": out_years, "overall": overall, "median_run": median_run}


def benchmark_returns(
    tri: pd.Series, base: date, end: date, years: list[int], capital: int, expense_pct: float
) -> dict:
    """Capital in the TRI from the close of `base`, less `expense_pct` a year accrued daily,
    valued at each year's last session (to `end`). Capital in paise; output in Rs and %."""
    tri = tri.sort_index()
    if base not in tri.index:
        raise ValueError(f"benchmark base date {base} is not in the TRI series")

    def value(d: date) -> float:
        days = np.array([(d - base).days])
        growth = float(tri[d]) / float(tri[base])
        return capital / 100 * growth * float(accrual_factor(days, expense_pct)[0])

    prev, out = value(base), {}
    ends = {}
    for y in years:
        upto = [d for d in tri.index if base < d <= min(date(y, 12, 31), end)]
        if not upto:
            raise ValueError(f"no TRI session in {y}")
        ends[str(y)] = upto[-1]
        v = value(upto[-1])
        out[str(y)] = (v / prev - 1) * 100
        prev = v
    last = ends[str(years[-1])]
    return {
        "years": out,
        "total_pct": (value(last) / (capital / 100) - 1) * 100,
        "value_end_rs": value(last),
        "year_end_sessions": {y: d.isoformat() for y, d in ends.items()},
    }


def first_pass_checks(stress2: dict, base: dict, bench: dict) -> list[dict]:
    """The three checks of plan section 10 ("beats" is strictly greater)."""
    mean = stress2["overall"]["net_rs"]["mean"]
    med = base["overall"]["net_pct"]["median"]
    per_year = {y: (base["years"][y]["net_pct"]["median"], b) for y, b in bench["years"].items()}
    beaten = int(sum(bool(m > b) for m, b in per_year.values()))
    two = bool(med > bench["total_pct"]) and beaten >= 5
    return [
        {
            "check": 1,
            "name": "mean net profit > 0 at stress2",
            "tier": "stress2",
            "value": mean,
            "verdict": "PASS" if mean > 0 else "FAIL",
        },
        {
            "check": 2,
            "name": "median run beats the benchmark overall and in >= 5 of 8 years",
            "tier": "base",
            "median_total_pct": med,
            "benchmark_total_pct": bench["total_pct"],
            "years_beaten": beaten,
            "years": per_year,
            "verdict": "PASS" if two else "FAIL",
        },
        {
            "check": 3,
            "name": "P(losing year) at base",
            "tier": "base",
            "value": base["overall"]["p_losing_year"],
            "verdict": "REPORTED",
        },
    ]


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows])


def _rs(v: float) -> str:
    return f"{v:,.0f}"


def _pc(v: float) -> str:
    return f"{v:.1f}%"


def _tier_rows(tiers: dict, variant: str) -> list[list[str]]:
    rows = []
    for tier, t in tiers.items():
        o = t[variant]["overall"]
        n, q = o["net_rs"], o["net_pct"]
        rows.append(
            [tier, f"{t['slippage_pct']:g}%", _rs(n["mean"]), _rs(n["median"]), _rs(n["p5"])]
            + [_rs(n["p95"]), _pc(q["median"]), _pc(q["p5"]), _pc(q["p95"])]
            + [f"{o['p_losing_year']:.3f}"]
            + [f"{o[c]['mean']:.1f}" for c in COUNTS]
        )
    return rows


TIER_HEAD = ["Tier", "Slippage", "Mean Rs", "Median Rs", "p5 Rs", "p95 Rs", "Median %"]
TIER_HEAD += ["p5 %", "p95 %", "P(losing year)", "Applications", "Allotments"]
TIER_HEAD += ["Skipped, blocked", "Skipped, capital"]
YEAR_HEAD = ["Year", "Median Rs", "p5 Rs", "p95 Rs", "Median %", "p5 %", "p95 %"]
YEAR_HEAD += ["Applications", "Allotments", "Skipped, blocked", "Skipped, capital"]
YEAR_HEAD += ["P(loss)", "Benchmark %"]


def _year_rows(s: dict, bench: dict) -> list[list[str]]:
    rows = []
    for y, v in s["years"].items():
        n, q = v["net_rs"], v["net_pct"]
        rows.append(
            [y, _rs(n["median"]), _rs(n["p5"]), _rs(n["p95"])]
            + [_pc(q["median"]), _pc(q["p5"]), _pc(q["p95"])]
            + [f"{v[c]['median']:g}" for c in COUNTS]
            + [f"{v['p_loss']:.3f}", _pc(bench["years"][y])]
        )
    o = s["overall"]
    n, q = o["net_rs"], o["net_pct"]
    rows.append(
        ["**All**", _rs(n["median"]), _rs(n["p5"]), _rs(n["p95"])]
        + [_pc(q["median"]), _pc(q["p5"]), _pc(q["p95"])]
        + [f"{o[c]['median']:g}" for c in COUNTS]
        + [f"{o['p_losing_year']:.3f} (any)", _pc(bench["total_pct"])]
    )
    return rows


def _check_rows(checks: list[dict]) -> list[list[str]]:
    rows = []
    for c in checks:
        if c["check"] == 2:
            num = (
                f"median {c['median_total_pct']:.1f}% vs {c['benchmark_total_pct']:.1f}%; "
                f"{c['years_beaten']} of {len(c['years'])} years beaten"
            )
        elif c["check"] == 1:
            num = f"Rs {c['value']:,.0f}"
        else:
            num = f"{c['value']:.3f}"
        rows.append([str(c["check"]), c["name"], c["tier"], num, c["verdict"]])
    return rows


def render_tables(r: dict) -> str:
    """Markdown tables for a run's results dict (scripts/run_ipo.py)."""
    tiers, bench = r["tiers"], r["benchmark"]
    out = [f"# IPO v1 run tables\n\n{r['header']}\n", "## First-pass checks\n"]
    out.append(_table(["#", "Check", "Tier", "Number", "Verdict"], _check_rows(r["checks"])))
    out.append(f"\n## Tiers, all {r['universe']['choices']} choices (amounts per run)\n")
    out.append(_table(TIER_HEAD, _tier_rows(tiers, "main")))
    for tier, t in tiers.items():
        out.append(f"\n## By year, {tier} ({t['slippage_pct']:g}%), all choices\n")
        out.append(_table(YEAR_HEAD, _year_rows(t["main"], bench)))
    n = r["universe"]["choices"] - r["universe"]["estimated"]
    out.append(f"\n## Tiers, without the estimated issues ({n} choices)\n")
    out.append(_table(TIER_HEAD, _tier_rows(tiers, "without_estimated")))
    out.append("\n## By year, base, without the estimated issues\n")
    out.append(_table(YEAR_HEAD, _year_rows(tiers["base"]["without_estimated"], bench)))
    for key, title in (("tax_sensitivity", "20% STCG"), ("listing_close", "sale at the close")):
        out.append(f"\n## By year, base, {title} (secondary)\n")
        out.append(_table(YEAR_HEAD, _year_rows(tiers["base"][key], bench)))
    mr = tiers["base"]["main"]["median_run"]
    yrs = ", ".join(f"{y} {_pc(v)}" for y, v in mr["years_pct"].items())
    total = _pc(mr["total_pct"])
    out.append(f"\n## Median run, base (information)\n\nRun {mr['run']}: total {total}; {yrs}.\n")
    ks = ", ".join(f"{y} {v:.3f}" for y, v in r["k_by_year"].items())
    out.append(f"## k by year (average lots per valid application)\n\n{ks}\n")
    rows = [[e["issue_id"], e["company"], e["issue_close"], e["reason"]] for e in r["excluded"]]
    out.append("## Excluded issues\n")
    out.append(_table(["Issue", "Company", "Bid close", "Reason"], rows))
    out.append("\n## Warnings\n\n" + ("\n".join(f"- {w}" for w in r["warnings"]) or "none"))
    return "\n".join(out) + "\n"
