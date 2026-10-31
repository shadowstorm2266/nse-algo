"""scripts/run_ipo.py end to end on synthetic issues: every tier and variant simulates, the
tables render, and each trial record serialises through append_trial (to a temp file).
The real run happens once, so nothing after the simulation may fail on it."""

import importlib.util
import json
from datetime import date, datetime, timedelta

import pandas as pd
import yaml

from nsealgo.costs import load_cost_config, load_ipo_costs
from nsealgo.data.calendar import IST
from nsealgo.engine.ipo_sim import TradingDays, draws
from nsealgo.reporting.ipo_report import benchmark_returns, first_pass_checks, render_tables
from nsealgo.reporting.trials import append_trial, read_trials
from nsealgo.settings import REPO_ROOT
from nsealgo.strategies.ipo_v1 import (
    IpoV1Config,
    issue_terms,
    k_by_year,
    one_lot_chance,
    select_universe,
)

spec = importlib.util.spec_from_file_location("run_ipo", REPO_ROOT / "scripts" / "run_ipo.py")
run_ipo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_ipo)


def _weekdays(start: date, end: date) -> TradingDays:
    n = (end - start).days + 1
    return TradingDays(d for d in (start + timedelta(k) for k in range(n)) if d.weekday() < 5)


def _issue(issue_id: str, close: date, **kw) -> dict:
    row = {
        "issue_id": issue_id,
        "company": issue_id.title(),
        "status": "listed",
        "issue_close": close,
        "lot_size": 100.0,
        "price_band_high": 140.0,
        "issue_price": 140.0,
        "retail_discount": float("nan"),
        "p_1lot": 0.5,
        "retail_sub_exch": 3.0,
        "retail_shares_applied": 1_200_000.0,
        "retail_valid_applications": 10_000.0,
        "allotment_date": close + timedelta(days=1),
        "listing_date": close + timedelta(days=5),
        "list_open": 150.0,
        "list_close": 145.0,
    }
    return row | kw


def test_every_tier_renders_and_logs(tmp_path):
    cfg = IpoV1Config.model_validate(yaml.safe_load(run_ipo.CONFIG_PATH.read_text("utf-8")))
    df = pd.DataFrame(
        [
            _issue("ALPHA_1", date(2024, 3, 6)),
            _issue("BETA_1", date(2024, 3, 6), p_1lot=None),  # estimated
            _issue("GAMMA_1", date(2025, 7, 2), status="withdrawn", listing_date=None),
            _issue("DELTA_1", date(2025, 12, 24), list_open=120.0, list_close=118.0),  # a loss
            _issue("CAMS_20200921", date(2024, 4, 1), status="not_listed_on_nse_at_ipo"),
        ]
    )
    days = _weekdays(date(2023, 12, 1), date(2026, 12, 31))
    choices, excluded = select_universe(df, cfg)
    k = k_by_year(df)
    p, est = one_lot_chance(choices, k)
    i = {
        "cfg": cfg,
        "days": days,
        "choices": choices,
        "excluded": excluded,
        "k": k,
        "p": p,
        "est": est,
        "terms": issue_terms(choices, days, cfg),
        "costs": load_cost_config(run_ipo.COSTS_PATH),
        "ipo_costs": load_ipo_costs(run_ipo.COSTS_PATH),
        "universe": {"choices": len(choices), "estimated": int(est.sum()), "excluded": 1},
        "warnings": [],
    }
    years = list(range(2019, 2027))
    u, keys = draws(200, len(choices), 1)
    tiers = {t: run_ipo._tier(i, t, u, keys, years) for t in run_ipo.TIERS}
    tri = pd.Series(
        [100.0 + 5 * n for n in range(9)], index=[date(2018 + n, 12, 31) for n in range(9)]
    )
    bench = benchmark_returns(tri, date(2018, 12, 31), date(2026, 10, 31), years, 2_000_000, 0.05)
    checks = first_pass_checks(tiers["stress2"]["main"], tiers["base"]["main"], bench)
    excl = excluded[["issue_id", "company", "issue_close", "reason"]].astype(str)
    results = {
        "header": "synthetic",
        "tiers": tiers,
        "benchmark": bench,
        "checks": checks,
        "k_by_year": k,
        "universe": i["universe"],
        "excluded": excl.to_dict("records"),
        "warnings": [],
    }
    md = render_tables(results)
    assert "## First-pass checks" in md and "CAMS_20200921" in md and "20% STCG" in md
    run_ipo._write(tmp_path / "run", i, results)
    assert json.loads((tmp_path / "run" / "results.json").read_text())["universe"]["choices"] == 4
    log = tmp_path / "trials.jsonl"
    for t in run_ipo.TIERS:
        rec = run_ipo._record(i, t, tiers[t], {"checks": checks}, datetime.now(IST), tmp_path)
        append_trial(log, rec)
    got = read_trials(log)
    assert [r["cost_tier"] for r in got] == list(run_ipo.TIERS)
    assert got[0]["reference_tier"] and not got[1]["reference_tier"] and got[0]["holdout"]
    # base slippage costs money: the base mean is below the reference tier's
    none_mean = tiers["none"]["main"]["overall"]["net_rs"]["mean"]
    assert tiers["base"]["main"]["overall"]["net_rs"]["mean"] < none_mean
    assert tiers["base"]["listing_close"]["overall"]["net_rs"]["mean"] < none_mean
