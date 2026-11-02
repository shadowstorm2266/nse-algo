"""IPO v2 decisions (research/ipo_v2_plan.md section 4): the decision snapshot and its
fallback, the 5x threshold, the universe cut at the plan's commit time, one decision per
issue, the evaluation set cut at the 20th decision's day, and the counts. The recorder
step runs end to end on a fake network."""

import json
import sys
from datetime import date, datetime, time

import pytest

from nsealgo.data.calendar import IST
from nsealgo.data.ipo_live import decision_inputs
from nsealgo.settings import REPO_ROOT
from nsealgo.strategies.ipo_v2 import (
    IpoV2Config,
    choose_snapshot,
    counts,
    decide,
    decision_record,
    evaluation_set,
)
from tests.ipo_live_helpers import current_rows, detail

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import ipo_live_steps
import ipo_v2_decisions
import record_ipo_live

D = date(2026, 11, 2)  # BCSSL's last bid day


def ist(*args: int) -> datetime:
    return datetime(*args, tzinfo=IST)


@pytest.fixture
def cfg() -> IpoV2Config:
    return ipo_v2_decisions.load_v2_config(REPO_ROOT / "config" / "ipo_v2.yaml")


def with_total(x: str | None) -> dict:
    d = detail(stamp="Updated as on 02-Nov-2026 15:24:00")
    rows = d["activeCat"]["dataList"]
    if x is None:
        rows.pop()  # no Total row
    else:
        rows[-1]["noOfTotalMeant"] = x
    return d


def total(x: str | None) -> float | None:
    return decision_inputs(with_total(x))["total_x"]


# --- pure rules ---------------------------------------------------------------------------


def test_the_repo_config_is_the_pre_registered_one(cfg):
    assert cfg.plan_commit.startswith("31e5750")
    assert cfg.plan_committed_at == ist(2026, 11, 2, 13, 16, 28)
    assert (cfg.threshold_total_x, cfg.decision_slot, cfg.cutoff) == (5.0, time(15, 30), time(17))
    assert (cfg.min_decisions, cfg.capital_rupees, cfg.monte_carlo.seed) == (20, 20000, 20261101)


def test_the_scheduled_1530_snapshot_wins_if_fetched_before_the_cutoff(cfg):
    snaps = [(ist(2026, 11, 2, 12, 0, 3), "a"), (ist(2026, 11, 2, 15, 30, 4), "s"),
             (ist(2026, 11, 2, 16, 40), "m")]  # fmt: skip
    assert choose_snapshot(snaps, "s", D, cfg) == ("s", "scheduled_1530", snaps[1][0])
    # no scheduled snapshot: the latest fetched on D before 17:00, from any run
    assert choose_snapshot(snaps, None, D, cfg) == ("m", "latest_before_cutoff", snaps[2][0])
    # a scheduled run started after the cutoff is too late
    late = [*snaps[:1], (ist(2026, 11, 2, 17, 10), "s")]
    assert choose_snapshot(late, "s", D, cfg) == ("a", "latest_before_cutoff", late[0][0])
    after = [(ist(2026, 11, 2, 17, 0, 0), "x"), (ist(2026, 11, 1, 16, 0), "y")]
    assert choose_snapshot(after, None, D, cfg) is None


def test_apply_at_5x_or_more_on_the_consolidated_total():
    assert decide(total("5.0"), 5.0) == ("apply", 5.0)
    assert decide(total("4.999999"), 5.0) == ("skip", 4.999999)
    assert decide(total("10.731376230779968"), 5.0)[0] == "apply"
    assert decide(total(None), 5.0) == ("no_decision_data", None)


def test_decision_records_and_the_universe_cut(cfg):
    now = ist(2026, 11, 2, 15, 30, 9)
    chosen = ("20261102T153004+0530.json", "scheduled_1530", ist(2026, 11, 2, 15, 30, 4))
    r = decision_record("BCSSL_20261029", D, chosen, decision_inputs(with_total("10.73")), cfg, now)
    assert (r["status"], r["total_x"], r["lot"], r["band_high"]) == ("apply", 10.73, 182, 82.0)
    assert r["application_rs"] == 182 * 82.0 and r["plan_commit"] == cfg.plan_commit
    early = (chosen[0], chosen[1], ist(2026, 11, 2, 13, 0))  # fetched before the plan commit
    assert (
        decision_record("X", D, early, decision_inputs(with_total("10")), cfg, now)["status"]
        == "before_plan"
    )
    assert decision_record("X", D, None, None, cfg, now)["status"] == "no_decision_data"
    old = decision_record("X", date(2026, 10, 30), None, None, cfg, now)
    assert old["status"] == "before_plan"


def dec(issue: str, day: str, status: str = "apply") -> dict:
    return {"issue_id": issue, "bid_close": day, "status": status}


def test_the_evaluation_set_ends_on_the_day_of_the_20th_decision():
    rows = [dec(f"I{i:02d}", f"2027-01-{i + 1:02d}") for i in range(19)]
    rows += [
        dec("Z_NODATA", "2027-01-02", "no_decision_data"),
        dec("Y", "2026-11-01", "before_plan"),
    ]
    assert evaluation_set(rows, 20) is None
    rows += [dec("A20", "2027-02-01", "skip"), dec("B20", "2027-02-01"), dec("LATE", "2027-03-01")]
    got, day = evaluation_set(rows, 20)
    assert day == date(2027, 2, 1) and len(got) == 21  # two issues close on the 20th's day
    assert [d["issue_id"] for d in got[-2:]] == ["A20", "B20"]
    assert "LATE" not in {d["issue_id"] for d in got}


def test_counts_show_no_performance():
    rows = [
        dec("A", "2026-11-02"),
        dec("B", "2026-11-03", "skip"),
        dec("C", "2026-11-04", "no_decision_data"),
    ]
    c = counts(rows, listed={"A"}, withdrawn=set())
    assert c == {"decisions": 2, "applies": 1, "skips": 1, "no_decision_data": 1,
                 "before_plan": 0, "listed": 1, "withdrawn": 0, "pending": 1}  # fmt: skip


# --- the recorder step ----------------------------------------------------------------------


@pytest.fixture
def day_runner(tmp_path, cfg):
    bodies = {
        record_ipo_live.CURRENT_URL: json.dumps(current_rows()).encode(),
        ipo_live_steps.DETAIL_URL.format(symbol="BCSSL"): json.dumps(with_total("10.73")).encode(),
    }
    net = ipo_live_steps.Net(
        nse=lambda url, ref: bodies[url], archive=lambda url: None, ready=lambda: True
    )
    root = tmp_path / "live"

    def run(at: datetime, scheduled: bool = True) -> ipo_live_steps.Run:
        hol = {date(2026, 12, 25)}
        return record_ipo_live.run_once(net, root, hol, scheduled, lambda: at, {}, None, cfg)

    return root, run


def decisions(root) -> list[dict]:
    return ipo_v2_decisions.read_decisions(root)


def test_the_1530_run_decides_once(day_runner):
    root, run = day_runner
    run(ist(2026, 11, 2, 12, 0, 3))
    assert decisions(root) == []  # 15:30 has not come
    r = run(ist(2026, 11, 2, 15, 30, 4))
    assert [a["kind"] for a in r.actions] == ["snapshot", "v2_decision"] and not r.errors
    (d,) = decisions(root)
    assert (d["status"], d["total_x"], d["snapshot_source"]) == ("apply", 10.73, "scheduled_1530")
    assert d["snapshot"] == "20261102T153004+0530.json"
    run(ist(2026, 11, 2, 19, 30, 2))
    run(ist(2026, 11, 3, 12, 0, 1))
    assert len(decisions(root)) == 1


def test_without_the_1530_snapshot_the_decision_waits_for_the_cutoff(day_runner):
    root, run = day_runner
    run(ist(2026, 11, 2, 12, 0, 3))
    run(ist(2026, 11, 2, 16, 10), scheduled=False)  # the 15:30 run never happened
    run(ist(2026, 11, 2, 16, 50), scheduled=False)
    assert decisions(root) == []  # before 17:00 a later manual snapshot could still come
    run(ist(2026, 11, 2, 19, 30, 2))
    (d,) = decisions(root)
    assert (d["snapshot"], d["snapshot_source"]) == (
        "20261102T165000+0530.json",
        "latest_before_cutoff",
    )


def test_no_snapshot_before_the_cutoff_is_no_decision_data(day_runner):
    root, run = day_runner
    run(ist(2026, 11, 2, 19, 30, 2))
    (d,) = decisions(root)
    assert d["status"] == "no_decision_data" and "total_x" not in d


def test_a_snapshot_before_the_plan_commit_is_before_plan(day_runner):
    root, run = day_runner
    run(ist(2026, 11, 2, 12, 0, 3))  # 12:00 is before the plan's 13:16:28 commit
    run(ist(2026, 11, 2, 19, 30, 2))
    (d,) = decisions(root)
    assert d["status"] == "before_plan" and d["snapshot"] == "20261102T120003+0530.json"
