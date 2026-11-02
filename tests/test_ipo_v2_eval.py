"""IPO v2 evaluation (research/ipo_v2_plan.md sections 5-8): the script shows counts only
until 20 decisions have all listed and refuses a second evaluation; the simulation orders
same-day applications by subscription, applies only 'apply' decisions, sells at the close,
and compares with v1's rules and the TRI. Synthetic issues only."""

import json
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from nsealgo.costs import load_cost_config, load_ipo_costs
from nsealgo.engine.ipo_sim import draws, simulate
from nsealgo.reporting.ipo_v2_eval import ISSUE_COLS, evaluate, v2_order_keys
from nsealgo.settings import REPO_ROOT
from nsealgo.strategies.ipo_v1 import issue_terms, sim_input

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import evaluate_ipo_v2
import ipo_v2_decisions

COSTS = REPO_ROOT / "config" / "costs.yaml"


@pytest.fixture
def cfg():
    return ipo_v2_decisions.load_v2_config(REPO_ROOT / "config" / "ipo_v2.yaml")


def days(start: date = date(2026, 11, 1)):
    return evaluate_ipo_v2.trading_days({date(2026, 12, 25)}, start)


def issue(i: int, close: date, decision: str = "apply", total: float = 8.0, **kw) -> dict:
    row = dict.fromkeys(ISSUE_COLS) | {
        "issue_id": f"I{i:02d}_{close:%Y%m%d}",
        "status": "listed",
        "decision": decision,
        "total_x": total,
        "issue_close": close,
        "lot_size": 100,
        "price_band_high": 100.0,
        "issue_price": 100.0,
        "listing_date": close + timedelta(days=3),
        "list_open": 110.0,
        "list_close": 120.0,
        "allotment_date": close + timedelta(days=1),
        "p_1lot": 1.0,
        "retail_sub_exch": 3.0,
        "retail_shares_applied": 3000,
        "retail_valid_applications": 20,
    }
    return row | kw


def weekly_set(n: int = 20) -> pd.DataFrame:
    """n issues on Mondays a week apart from 2026-11-02; odd ones are skips."""
    rows = [
        issue(i, date(2026, 11, 2) + timedelta(weeks=i), "skip" if i % 2 else "apply")
        for i in range(n)
    ]
    return pd.DataFrame(rows, columns=ISSUE_COLS)


def toy_tri() -> pd.Series:
    start = date(2026, 10, 1)
    idx = [start + timedelta(days=k) for k in range(400)]
    return pd.Series([1000.0 + k for k in range(400)], index=idx)


# --- the simulation -----------------------------------------------------------------------


def test_same_day_applications_go_to_the_highest_subscription_first(cfg):
    d = date(2026, 11, 2)
    big = {"lot_size": 150}  # Rs 15,000 each: Rs 20,000 covers one of the two
    df = pd.DataFrame(
        [issue(1, d, total=6.0, **big), issue(2, d, total=40.0, **big)], columns=ISSUE_COLS
    )
    terms = issue_terms(df, days(), cfg)
    x = sim_input(terms, pd.Series([0.0, 0.0]), np.zeros(2, dtype=np.int64))
    u, random_keys = draws(300, 2, 1)
    res = simulate(x, 2_000_000, u, v2_order_keys(df, 300))
    assert res.applied[:, 1].all() and not res.applied[:, 0].any()
    # v1's random order would take each about half the time
    v1 = simulate(x, 2_000_000, u, random_keys)
    assert 0.3 < v1.applied[:, 1].mean() < 0.7


def test_a_deterministic_set_gives_the_expected_ordering_of_results(cfg):
    df = weekly_set()
    costs, ipo_costs = load_cost_config(COSTS), load_ipo_costs(COSTS)
    r = evaluate(df, days(), cfg, costs, ipo_costs, toy_tri(), n_runs=200)
    assert (r["issues"], r["applies"]) == (20, 10)
    t = r["tiers"]
    # p = 1 and one issue a week: every run is the same path
    assert t["base"]["median_rs"] == pytest.approx(t["base"]["mean_rs"])
    assert t["base"]["applications_mean"] == 10 and t["base"]["p_loss"] == 0
    assert (
        t["none"]["mean_rs"]
        > t["base"]["mean_rs"]
        > t["stress1"]["mean_rs"]
        > t["stress2"]["mean_rs"]
    )
    # gross per allotment at base: 100 x (120 x 0.9975 - 100) = Rs 1,970 before sale charges
    assert 10 * 1_900 < t["base"]["mean_rs"] < 10 * 1_970
    # v1's rules: all 20, sold at the open (Rs 110)
    assert r["v1_rules_base"]["applications_mean"] == 20
    assert 20 * 900 < r["v1_rules_base"]["mean_rs"] < 20 * 975
    assert [c["result"] for c in r["checks"]] == ["PASS", "PASS", "PASS", "REPORTED"]
    assert r["benchmark"]["base"] == "2026-11-01" and not r["benchmark"]["end_short"]


def test_estimated_and_withdrawn_issues(cfg):
    df = weekly_set()
    df.loc[0, "p_1lot"] = None  # advert unreadable: v1's estimate with the set's k
    df.loc[2, ["status", "listing_date", "list_open", "list_close"]] = [
        "withdrawn",
        None,
        None,
        None,
    ]
    costs, ipo_costs = load_cost_config(COSTS), load_ipo_costs(COSTS)
    r = evaluate(df, days(), cfg, costs, ipo_costs, toy_tri(), n_runs=200)
    assert r["estimated_p"] == [df.loc[0, "issue_id"]]
    assert r["set_k"] == pytest.approx(1.5)  # 3000 shares / 100 lot / 20 applications
    # k / x = 1.5 / 3.0: issue 0 allotted in about half the runs; issue 2 never pays
    assert 8 < r["tiers"]["base"]["allotments_mean"] < 9


# --- the script: counts only until ready, one evaluation ----------------------------------


def write_decisions(root, n: int, listed: int) -> None:
    root.mkdir(parents=True)
    lines = []
    for i in range(n):
        iid = f"I{i:02d}_20261102"
        close = (date(2026, 11, 2) + timedelta(weeks=i)).isoformat()
        lines.append({"issue_id": iid, "bid_close": close, "status": "apply", "total_x": 9.0,
                      "lot": 100, "band_high": 100.0})  # fmt: skip
        if i < listed:
            (root / iid).mkdir()
            (root / iid / "listing_20261105.json").write_text("{}")
    text = "".join(json.dumps(x) + "\n" for x in lines)
    (root / "decisions.jsonl").write_text(text, encoding="utf-8")


def test_fewer_than_20_decisions_show_counts_only(tmp_path, cfg, capsys):
    write_decisions(tmp_path / "live", 19, listed=19)
    es, _ = evaluate_ipo_v2.status(tmp_path / "live", cfg, date(2027, 6, 1))
    out = capsys.readouterr().out
    assert es is None and "performance withheld: 19 of 20 decisions" in out
    assert "decisions: 19" in out and "Rs" not in out and "mean" not in out


def test_an_unlisted_issue_in_the_set_withholds_performance(tmp_path, cfg, capsys):
    write_decisions(tmp_path / "live", 20, listed=19)
    es, pending = evaluate_ipo_v2.status(tmp_path / "live", cfg, date(2027, 6, 1))
    out = capsys.readouterr().out
    assert len(es) == 20 and pending == ["I19_20261102"]
    assert "OVERDUE" in out and "performance withheld: 1 issue(s) not yet listed" in out


def test_main_stops_before_evaluating_and_refuses_a_second_evaluation(
    tmp_path, monkeypatch, capsys
):
    root, trials = tmp_path / "live", tmp_path / "trials.jsonl"
    write_decisions(root, 20, listed=20)
    monkeypatch.setattr(evaluate_ipo_v2, "LIVE", root)
    monkeypatch.setattr(evaluate_ipo_v2, "TRIALS_PATH", trials)
    assert evaluate_ipo_v2.main([]) == 0
    assert "ready: run with --evaluate" in capsys.readouterr().out
    trials.write_text(json.dumps({"strategy": "ipo", "strategy_version": "2"}) + "\n")
    with pytest.raises(SystemExit, match="already evaluated"):
        evaluate_ipo_v2.main(["--evaluate"])
