"""Run IPO v1 (research/ipo_strategy_plan.md): four cost tiers of Monte Carlo runs, one
trial per tier in research/trials.jsonl.

    uv run python scripts/run_ipo.py --check         # inputs only: no simulation, no trial
    uv run python scripts/run_ipo.py --run-holdout   # the run

The period passes holdout_start, so the run needs --run-holdout. Only the owner authorises
that (by typing "run holdout", hard rule 8), and it runs once per strategy version. It
refuses a dirty working tree. Output: research/runs/<stamp>_ipo_v1/ (results.json,
tables.md, terms.csv, excluded.csv).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from nsealgo.costs import load_cost_config, load_ipo_costs
from nsealgo.data.calendar import IST
from nsealgo.data.ipo_read import bhavcopy_day, bhavcopy_paths
from nsealgo.engine.ipo_sim import TradingDays, draws, simulate
from nsealgo.engine.loader import check_holdout, load_research_config
from nsealgo.reporting.ipo_report import (
    benchmark_returns,
    first_pass_checks,
    render_tables,
    summarize,
)
from nsealgo.reporting.trials import TRIALS_PATH, append_trial, git_state, holdout_already_run
from nsealgo.settings import REPO_ROOT
from nsealgo.strategies.ipo_v1 import (
    NAME,
    VERSION,
    IpoV1Config,
    issue_terms,
    k_by_year,
    one_lot_chance,
    pnl_paise,
    select_universe,
    sim_input,
    tax_schedule,
)

TIERS = ("none", "base", "stress1", "stress2")
COSTS_PATH = REPO_ROOT / "config" / "costs.yaml"
CONFIG_PATH = REPO_ROOT / "config" / "strategies" / "ipo_v1.yaml"
IPOS = REPO_ROOT / "data" / "clean" / "ipo" / "ipos.parquet"


def _inputs() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        cfg = IpoV1Config.model_validate(yaml.safe_load(fh))
    df = pd.read_parquet(IPOS)
    days = TradingDays(bhavcopy_day(p) for p in bhavcopy_paths(REPO_ROOT / "data/raw/ipo"))
    choices, excluded = select_universe(df, cfg)
    k = k_by_year(df)
    p, est = one_lot_chance(choices, k)
    terms = issue_terms(choices, days, cfg)
    return {
        "cfg": cfg,
        "days": days,
        "choices": choices,
        "excluded": excluded,
        "k": k,
        "p": p,
        "est": est,
        "terms": terms,
    }


def _print_check(i: dict) -> None:
    ch, ex = i["choices"], i["excluded"]
    status = ch["status"].value_counts().to_dict()
    print(f"choices: {len(ch)} {status}; estimated p: {int(i['est'].sum())}; excluded: {len(ex)}")
    for _, e in ex.iterrows():
        print(f"  excluded {e['issue_id']}: {e['reason']}")
    print("k by year:", {y: round(v, 3) for y, v in i["k"].items()})
    n_est = int(i["terms"]["allotment_date_estimated"].sum())
    print(f"application days: {ch['issue_close'].nunique()}; allotment dates estimated: {n_est}")
    print("days past the last session used:", sorted(i["days"].extended) or "none")
    for tier in TIERS:  # build every P&L input the run will use; print no values
        slip = i["ipo_costs"].listing_slippage_pct[tier]
        for col in ("list_open", "list_close"):
            sim_input(
                i["terms"],
                i["p"],
                pnl_paise(i["choices"], i["terms"], col, slip, i["costs"], i["ipo_costs"]),
            )
    print(f"simulation inputs build for tiers {', '.join(TIERS)}: OK (no simulation run)")


def _tier(i: dict, tier: str, u: np.ndarray, keys: np.ndarray, years: list[int]) -> dict:
    cfg, costs, ipo = i["cfg"], i["costs"], i["ipo_costs"]
    slip = ipo.listing_slippage_pct[tier]
    cap = cfg.capital_rupees * 100
    pnl = pnl_paise(i["choices"], i["terms"], "list_open", slip, costs, ipo)
    x = sim_input(i["terms"], i["p"], pnl)
    keep = ~i["est"].to_numpy()
    out = {
        "slippage_pct": float(slip),
        "main": summarize(simulate(x, cap, u, keys), x, years, cap),
        "without_estimated": summarize(
            simulate(x.take(keep), cap, u[:, keep], keys[:, keep]), x.take(keep), years, cap
        ),
    }
    if tier == "base":
        tax = tax_schedule(i["terms"], i["days"], cfg)
        out["tax_sensitivity"] = summarize(simulate(x, cap, u, keys, tax), x, years, cap)
        pc = pnl_paise(i["choices"], i["terms"], "list_close", slip, costs, ipo)
        xc = sim_input(i["terms"], i["p"], pc)
        out["listing_close"] = summarize(simulate(xc, cap, u, keys), xc, years, cap)
    return out


def _benchmark(cfg: IpoV1Config, years: list[int]) -> dict:
    tri = pd.read_csv(REPO_ROOT / cfg.benchmark.tri_csv, usecols=["date", "tri"])
    dates = pd.to_datetime(tri["date"]).dt.date
    series = pd.Series(tri["tri"].astype(float).to_numpy(), index=dates)
    b = cfg.benchmark
    cap = cfg.capital_rupees * 100
    return benchmark_returns(series, b.base_date, cfg.bid_close_to, years, cap, b.expense_ratio_pct)


def _record(i: dict, tier: str, t: dict, extra: dict, run_at: datetime, run_dir: Path) -> dict:
    cfg = i["cfg"]
    return {
        "run_at": run_at.isoformat(),
        **git_state(),
        "strategy": NAME,
        "strategy_version": VERSION,
        "params": cfg.model_dump(mode="json"),
        "product": "IPO (manual UPI, simulated)",
        "instrument": "EQ",
        "period": {"label": "ipo_2019_2026", "start": cfg.bid_close_from, "end": cfg.bid_close_to},
        "holdout": True,
        "cost_tier": tier,
        "listing_slippage_pct": t["slippage_pct"],
        "brokerage_preset": i["costs"].active_brokerage,
        "reference_tier": t["slippage_pct"] == 0,
        "universe": i["universe"],
        "capital": cfg.capital_rupees,
        "metrics": t | extra,
        "warnings": i["warnings"],
        "run_dir": str(run_dir),
    }


def _write(run_dir: Path, i: dict, results: dict) -> None:
    run_dir.mkdir(parents=True)
    (run_dir / "results.json").write_text(json.dumps(results, indent=2, default=str), "utf-8")
    (run_dir / "tables.md").write_text(render_tables(results), encoding="utf-8")
    terms = i["terms"].assign(p=i["p"], p_estimated=i["est"])
    terms.to_csv(run_dir / "terms.csv", index=False)
    i["excluded"].to_csv(run_dir / "excluded.csv", index=False)


def _guard(i: dict, run_holdout: bool) -> None:
    check_holdout(i["cfg"].bid_close_to, load_research_config(), run_holdout)
    if holdout_already_run(TRIALS_PATH, NAME, VERSION):
        sys.exit(f"holdout already run for {NAME} {VERSION}; a rerun needs a new version")
    if git_state()["git_dirty"]:
        sys.exit("working tree is dirty: commit first (the plan requires one clean commit)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="inputs only; no simulation, no trial")
    ap.add_argument("--run-holdout", action="store_true", help="human-only: the one run")
    args = ap.parse_args()
    i = _inputs()
    i |= {"costs": load_cost_config(COSTS_PATH), "ipo_costs": load_ipo_costs(COSTS_PATH)}
    if args.check:
        _print_check(i)
        return
    _guard(i, args.run_holdout)
    cfg = i["cfg"]
    years = list(range(cfg.bid_close_from.year, cfg.bid_close_to.year + 1))
    u, keys = draws(cfg.monte_carlo.runs, len(i["choices"]), cfg.monte_carlo.seed)
    tiers = {t: _tier(i, t, u, keys, years) for t in TIERS}
    bench = _benchmark(cfg, years)
    checks = first_pass_checks(tiers["stress2"]["main"], tiers["base"]["main"], bench)
    i["universe"] = {
        "choices": len(i["choices"]),
        "estimated": int(i["est"].sum()),
        "excluded": len(i["excluded"]),
    }
    ext = sorted(d.isoformat() for d in i["days"].extended)
    i["warnings"] = [f"weekdays used past the last session: {ext}"] if ext else []
    run_at = datetime.now(IST)
    run_dir = REPO_ROOT / "research" / "runs" / f"{run_at:%Y%m%d-%H%M%S}_ipo_v1"
    mc = cfg.monte_carlo
    head = f"Run {run_at:%Y-%m-%d %H:%M} IST, git {git_state()['git_hash'][:7]}, "
    head += f"{mc.runs} runs per tier, seed {mc.seed}."
    excluded = i["excluded"][["issue_id", "company", "issue_close", "reason"]].astype(str)
    results = {
        "header": head,
        "tiers": tiers,
        "benchmark": bench,
        "checks": checks,
        "k_by_year": i["k"],
        "universe": i["universe"],
        "excluded": excluded.to_dict("records"),
        "warnings": i["warnings"],
    }
    _write(run_dir, i, results)
    for t in TIERS:
        extra = {"checks": checks, "benchmark": bench} if t in ("base", "stress2") else {}
        append_trial(TRIALS_PATH, _record(i, t, tiers[t], extra, run_at, run_dir))
    print(render_tables(results))
    print(f"wrote {run_dir}; trials logged: {len(TIERS)}")


if __name__ == "__main__":
    main()
