"""Telegram messages from scripts/record_ipo_live.py, sent only to the owner's chat
(nsealgo.notify; TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID through nsealgo.settings):

- each IPO v2 decision when it is made: issue, apply/skip, total subscription at the
  decision snapshot, application amount (lot x upper band);
- an alert when a run has errors, finds scheduled slots that no earlier run reported
  missed, or the 19:30 backup did not push;
- one heartbeat after the scheduled 19:30 run, also on a holiday: runs, decisions and
  launch failures today, issues open for bidding. No heartbeat means the laptop was off
  or the launch failed (scripts/run_ipo_task.ps1 logs launch failures).

The v2 forward test is blind: nothing about listings, adverts, allotment, post-listing
prices or P&L is sent. An error's text is sent only for steps that come before the
listing (allowlist SAFE_ERROR); any other error is named without its text. A failed
send is a warning in the run's log, never an error.
"""

import json
import re
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from pathlib import Path

from ipo_live_steps import Run
from ipo_v2_decisions import read_decisions

from nsealgo.notify import Notifier

HEARTBEAT_SLOT = time(19, 30)
EARLY = timedelta(minutes=5)  # a scheduled run may start a little before its slot
MAX_ERRORS = 5
MAX_ERROR_CHARS = 300
MAX_SLOTS_SHOWN = 12
SAFE_ERROR = re.compile(
    r"^(current issues|network|backup"
    r"|\S+ (snapshot|final book|v2 decision)"
    r"|\S+: NSE's JSON is for bid period)\b"
)
STATUS = {
    "apply": "APPLY",
    "skip": "SKIP",
    "no_decision_data": "NO DECISION DATA",
    "before_plan": "BEFORE PLAN (not in the test)",
}


def error_line(msg: str) -> str:
    if SAFE_ERROR.match(msg):
        return msg[:MAX_ERROR_CHARS]
    return f"{msg.split(':', 1)[0]}: failed (text in run_log.jsonl, not sent: v2 is blind)"


def rupees(x: float) -> str:
    return f"₹{x:,.0f}" if float(x).is_integer() else f"₹{x:,.2f}"


def decision_text(rec: dict) -> str:
    """Only the decision itself; the record's other fields are not sent."""
    lines = [f"IPO v2 decision: {rec['issue_id']}: {STATUS.get(rec['status'], rec['status'])}"]
    total = rec.get("total_x")
    lines.append(f"Total subscription: {total:.2f}x" if total is not None else "Total: -")
    if rec.get("snapshot_fetched_at"):
        at = datetime.fromisoformat(rec["snapshot_fetched_at"])
        lines.append(f"Snapshot: {at:%d %b %H:%M} IST ({rec.get('snapshot_source')})")
    app = rec.get("application_rs")
    lines.append(f"Application: {rupees(app)}" if app else "Application: -")
    lines.append(f"Rule: apply if total >= {rec.get('threshold')}x")
    return "\n".join(lines)


def run_name(run: Run) -> str:
    if run.log.get("backfill"):
        return f"backfill {run.log['backfill']}"
    slot = run.log.get("slot")
    if run.scheduled and slot:
        return f"scheduled {datetime.fromisoformat(slot):%a %d %b %H:%M}"
    kind = "scheduled" if run.scheduled else "manual"
    return f"{kind} {run.started_at:%a %d %b %H:%M}"


def new_missed(run: Run, earlier: Sequence[dict]) -> list[str]:
    """Missed slots this run found that no earlier run_log line reported."""
    seen = {s for r in earlier for s in r.get("missed_slots") or []}
    return [s for s in run.log.get("missed_slots") or [] if s not in seen]


def backup_unpushed(run: Run) -> str | None:
    b = run.log.get("backup")
    return None if not b or b.get("pushed") else str(b.get("note", "not pushed"))


def alert_text(run: Run, missed: list[str]) -> str | None:
    lines: list[str] = []
    if run.errors:
        lines.append(f"{len(run.errors)} error(s):")
        lines += [f"- {error_line(e)}" for e in run.errors[:MAX_ERRORS]]
        if len(run.errors) > MAX_ERRORS:
            lines.append(f"- and {len(run.errors) - MAX_ERRORS} more")
    if missed:
        first = missed[:MAX_SLOTS_SHOWN]
        shown = ", ".join(f"{datetime.fromisoformat(s):%a %d %b %H:%M}" for s in first)
        more = len(missed) - MAX_SLOTS_SHOWN
        lines.append(f"Missed scheduled run(s): {shown}{f' and {more} more' if more > 0 else ''}")
    if note := backup_unpushed(run):
        lines.append(f"Backup not pushed: {note}")
    if not lines:
        return None
    return "\n".join([f"⚠ IPO recorder: {run_name(run)} run", *lines])


def heartbeat_due(run: Run, slot_time: time) -> bool:
    """The scheduled run for the 19:30 slot; on a holiday (no slot) a scheduled run
    started at 19:25 or later."""
    if not run.scheduled or run.log.get("backfill"):
        return False
    if run.log.get("slot"):
        return datetime.fromisoformat(run.log["slot"]).time() == slot_time
    start = (datetime.combine(date.min, slot_time) - EARLY).time()
    return run.log.get("trading_day") is False and run.started_at.time() >= start


def launch_failures_on(root: Path, day: date) -> int:
    path = root / "launch_failures.jsonl"
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text("utf-8").splitlines():
        try:
            n += datetime.fromisoformat(json.loads(line)["time"]).date() == day
        except (ValueError, KeyError, TypeError):
            n += 1  # an unreadable line counts: better a false alarm than a silent one
    return n


def heartbeat_text(run: Run, root: Path, earlier: Sequence[dict]) -> str:
    day = run.started_at.date()
    today = [r for r in earlier if datetime.fromisoformat(r["started_at"]).date() == day]
    runs, ok = len(today) + 1, sum(bool(r.get("ok")) for r in today) + (not run.errors)
    missed_today = {
        s
        for r in [*today, run.log]
        for s in r.get("missed_slots") or []
        if datetime.fromisoformat(s).date() == day
    }
    decided = [
        d for d in read_decisions(root) if datetime.fromisoformat(d["decided_at"]).date() == day
    ]
    launch = launch_failures_on(root, day)
    good = ok == runs and not missed_today and not launch and backup_unpushed(run) is None
    head = "✅ IPO recorder: all OK" if good else "⚠ IPO recorder: problems today (see alerts)"
    lines = [f"{head} ({day:%a %d %b})"]
    if run.log.get("trading_day") is False:
        lines.append("Not an NSE trading day (config/holidays.csv)")
    lines.append(f"Runs today: {runs}, {ok} ok, {len(missed_today)} missed slot(s)")
    if launch:
        lines.append(f"Launch failures today: {launch} (launch_failures.jsonl)")
    lines.append(f"Decisions today: {len(decided)}")
    open_now = run.log.get("open_mainboard")
    lines.append(f"Open for bidding: {', '.join(open_now) if open_now else 'none'}")
    if run.log.get("backup", {}).get("pushed"):
        lines.append("Backup: pushed")
    return "\n".join(lines)


def send(run: Run, notifier: Notifier, what: str, text: str) -> None:
    try:
        notifier.send(text)
        run.log.setdefault("telegram_sent", []).append(what)
    except Exception as err:  # a failed send never fails the run
        run.warn(f"telegram {what} not sent: {type(err).__name__}: {err}")


def notify_run(
    run: Run,
    root: Path,
    notifier: Notifier | None,
    earlier: Sequence[dict],
    slot_time: time = HEARTBEAT_SLOT,
) -> None:
    """Send this run's messages; `earlier` is run_log.jsonl before this run's line."""
    run.log["telegram"] = notifier is not None
    if notifier is None:
        return
    try:
        made = [a["issue"] for a in run.actions if a.get("kind") == "v2_decision"]
        recs = {d["issue_id"]: d for d in read_decisions(root) if d["issue_id"] in made}
        texts = [(f"decision {i}", decision_text(recs[i])) for i in made if i in recs]
        if alert := alert_text(run, new_missed(run, earlier)):
            texts.append(("alert", alert))
        if heartbeat_due(run, slot_time):
            texts.append(("heartbeat", heartbeat_text(run, root, earlier)))
    except Exception as err:
        run.warn(f"telegram: messages not built: {err!r}")
        return
    for what, text in texts:
        send(run, notifier, what, text)
