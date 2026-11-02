"""IPO v2 decisions for scripts/record_ipo_live.py (research/ipo_v2_plan.md section 4).

Every run checks each issue on disk whose last bid day D has come and that has no decision
yet:
- the scheduled run for D's 15:30 slot, fetching before 17:00, decides from the snapshot
  it has just saved;
- a run at or after 17:00 on D, or on a later day, decides by the full rule: the scheduled
  15:30 snapshot if one was saved before 17:00, else the latest snapshot fetched on D
  before 17:00, else "no decision data";
- any other run before 17:00 on D leaves the issue undecided.

One line per issue is appended to data/live/ipo/decisions.jsonl and never changed. The
file is backed up with the rest of data/live/ipo/ (appends only).
"""

import json
from datetime import datetime
from pathlib import Path

import yaml
from ipo_live_steps import Run, tracked

from nsealgo.data.calendar import IST
from nsealgo.data.ipo_live import Tracked, detail_matches, parse_snapshot_name
from nsealgo.strategies.ipo_v2 import (
    IpoV2Config,
    choose_snapshot,
    cutoff_at,
    decision_record,
    decision_slot_at,
)

DECISIONS = "decisions.jsonl"


def read_decisions(root: Path) -> list[dict]:
    path = root / DECISIONS
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]


def scheduled_file(rows: list[dict], issue_id: str, slot: datetime) -> str | None:
    """The snapshot file the scheduled run for `slot` saved for the issue, if any."""
    for r in rows:
        if not (r.get("scheduled") and r.get("slot")):
            continue
        if datetime.fromisoformat(r["slot"]) != slot:
            continue
        for a in r.get("actions", []):
            if a.get("issue") == issue_id and a.get("kind") == "snapshot":
                return a["file"]
    return None


def _decide_one(
    run: Run, root: Path, t: Tracked, rows: list[dict], cfg: IpoV2Config, final: bool
) -> dict | None:
    """The record for one issue, or None if it must wait (before the cutoff, no
    scheduled snapshot yet)."""
    assert t.issue_close is not None
    day, d = t.issue_close, root / t.issue_id
    snaps = [
        (n[1], p.name)
        for p in d.iterdir()
        if (n := parse_snapshot_name(p.name)) is not None and not n[0]
    ]
    scheduled = scheduled_file(rows, t.issue_id, decision_slot_at(day, cfg))
    chosen = choose_snapshot(snaps, scheduled, day, cfg)
    if not final and (chosen is None or chosen[1] != "scheduled_1530"):
        return None
    detail = json.loads((d / chosen[0]).read_bytes()) if chosen else None
    if detail is not None and not detail_matches(detail, t.issue_open):
        run.warn(f"{t.issue_id}: decision snapshot {chosen[0]} is another bid period's")
        detail, chosen = None, None
    return decision_record(t.issue_id, day, chosen, detail, cfg, run.clock())


def record_decisions(run: Run, root: Path, cfg: IpoV2Config, log_rows: list[dict]) -> None:
    """Append the decision of every issue that is due (module docstring)."""
    now = run.clock().astimezone(IST)
    done = {d["issue_id"] for d in read_decisions(root)}
    rows = [
        *log_rows,
        {"scheduled": run.scheduled, "slot": run.log.get("slot"), "actions": run.actions},
    ]
    for t in tracked(root):
        if t.issue_id in done or t.issue_close is None or t.issue_close > now.date():
            continue
        final = now >= cutoff_at(t.issue_close, cfg)
        try:
            rec = _decide_one(run, root, t, rows, cfg, final)
        except Exception as err:
            run.fail(f"{t.issue_id} v2 decision: {err!r}")
            continue
        if rec is None:
            continue
        with (root / DECISIONS).open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec) + "\n")
        keys = ("status", "total_x", "snapshot", "snapshot_source")
        run.did({"issue": t.issue_id, "kind": "v2_decision"} | {k: rec.get(k) for k in keys})


def load_v2_config(path: Path) -> IpoV2Config:
    return IpoV2Config.model_validate(yaml.safe_load(path.read_text("utf-8")))
