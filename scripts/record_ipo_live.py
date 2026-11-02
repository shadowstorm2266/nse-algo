"""Record live NSE data for every open mainboard IPO (IPO track step 3: data only).

    uv run python scripts/record_ipo_live.py              # one manual run
    uv run python scripts/record_ipo_live.py --scheduled  # what Task Scheduler runs
    uv run python scripts/record_ipo_live.py --status     # what is on disk; fetches nothing
    uv run python scripts/record_ipo_live.py --check-env OUT.json  # environment report only

No strategy, no simulation, no trial. It runs on the owner's Windows laptop from Task
Scheduler (scripts/make_ipo_task_xml.py); it is not the trading bot. Writes only under
data/live/ipo/; the layout and file names are in nsealgo.data.ipo_live, and no file is
ever overwritten. Machine paths come from config/ipo_live.yaml. Each run:

1. Schedule check (nsealgo.data.live_schedule; slots 12:00, 15:30, 19:30 IST on NSE trading
   days): a WARNING for each slot no scheduled run covered since the last one, and for a
   scheduled run that started over 30 minutes late. A scheduled run on a weekday listed in
   config/holidays.csv logs itself and stops.
2. Bid days: saves /api/ipo-current-issue, then the per-issue JSON of every mainboard issue
   open today and of every issue on disk whose bid period (from its latest JSON) contains
   today: NSE may drop an issue from the list before the close day's 19:30 run.
3. After the close, per issue on disk (scripts/ipo_live_steps.py):
   - final book: the per-issue JSON fetched by the first run on a day after the close day
     (the latest update seen in step 1b was 23:15 on the close day);
   - listing day: NSE bhavcopies from the close day on (scripts/download_bhavcopy.py URLs,
     read with nsealgo.data.ipo_listing.read_bhavcopy). The listing day is the first
     session after the close whose bhavcopy has the issue's EQ/BE row, by ISIN once NSE's
     JSON has one, else by symbol. A trading day's file still missing at 18:00 the next
     day counts as no session; before that the search waits. Up to 45 days after the close;
   - basis-of-allotment advert: probed like scripts/download_ipo_boa.py once the listing
     day is known, until found or 7 days after listing; parsed with nsealgo.data.ipo_boa
     using the configured pdftotext (checked every run; a parse failure is a warning).
4. IPO v2 decisions (scripts/ipo_v2_decisions.py, research/ipo_v2_plan.md): for each issue
   whose last bid day has come, the decision from the 15:30 snapshot is appended to
   data/live/ipo/decisions.jsonl (fallback rules after 17:00).
5. The scheduled run for the 19:30 slot commits and pushes data/live/ipo/ to its own git
   repository (scripts/ipo_live_backup.py). Git never touches the main repo, and the main
   repo is only read (code version: git rev-parse and status without optional locks).
6. Appends one line to data/live/ipo/run_log.jsonl, also when the run fails; the 19:30
   backup therefore holds that run's files and the log up to the previous run. Exit status
   1 if any step failed.
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path

from download_ipo import IPO_PAGE, SITE, NseSession
from download_ipo_boa import _get as archive_get
from ipo_live_backup import BackupError, LiveConfig, backup, load_live_config
from ipo_live_backup import check as backup_check
from ipo_live_steps import Net, Run, after_close, pdftotext_check, record_book, tracked
from ipo_v2_decisions import load_v2_config, record_decisions

from nsealgo.data.calendar import IST, load_holidays
from nsealgo.data.ipo_live import open_mainboard, snapshot_name, write_new
from nsealgo.data.live_schedule import LATE_WARN, check_schedule, is_trading_day, missed_in_window
from nsealgo.settings import REPO_ROOT
from nsealgo.strategies.ipo_v2 import IpoV2Config

LIVE = REPO_ROOT / "data" / "live" / "ipo"
HOLIDAYS = REPO_ROOT / "config" / "holidays.csv"
IPO_V2 = REPO_ROOT / "config" / "ipo_v2.yaml"
CURRENT_URL = SITE + "/api/ipo-current-issue"
ARCHIVE_PAUSE_SECONDS = 0.4
MAX_MISSED_SHOWN = 12


def read_log(root: Path) -> list[dict]:
    path = root / "run_log.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text("utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            print(f"WARNING: unreadable run_log line skipped: {line[:80]!r}")
    return rows


def covered_slots(rows: list[dict]) -> list[datetime]:
    return [datetime.fromisoformat(r["slot"]) for r in rows if r.get("scheduled") and r.get("slot")]


def schedule_step(run: Run, root: Path, holidays: set[date]) -> bool:
    """Fills the log's schedule fields and warns; False if a scheduled run must stop."""
    check = check_schedule(covered_slots(read_log(root)), run.started_at, run.scheduled, holidays)
    today = run.started_at.date()
    run.log |= {
        "slot": check.slot.isoformat() if check.slot else None,
        "late_minutes": round(check.late.total_seconds() / 60, 1) if check.late else None,
        "missed_slots": [s.isoformat() for s in check.missed],
        "trading_day": is_trading_day(today, holidays),
    }
    if check.missed:
        shown = ", ".join(f"{s:%a %d %b %H:%M}" for s in check.missed[:MAX_MISSED_SHOWN])
        more = len(check.missed) - MAX_MISSED_SHOWN
        run.warn(f"missed scheduled run(s): {shown}{f' and {more} more' if more > 0 else ''}")
    if check.slot and check.late and check.late > LATE_WARN:
        run.warn(f"the {check.slot:%a %d %b %H:%M} run started {run.log['late_minutes']} min late")
    if check.duplicate:
        run.warn(f"slot {check.slot:%H:%M} was already covered by an earlier scheduled run")
    if not any(d.year == today.year for d in holidays):
        run.warn(f"config/holidays.csv has no {today.year} dates; all weekdays count as sessions")
    return run.log["trading_day"] or not run.scheduled


def bid_days(net: Net, run: Run, root: Path, today: date) -> None:
    """Save the current-issue list, then one snapshot per issue in its bid period."""
    due: dict[str, tuple[str, date]] = {}
    try:
        body = net.nse(CURRENT_URL, IPO_PAGE)
        rows = json.loads(body)
        if not isinstance(rows, list):
            raise ValueError(f"expected a list, got {type(rows).__name__}")
        write_new(root / "current_issue" / snapshot_name(run.clock()), body)
        open_now, other = open_mainboard(rows, today)
        run.log |= {"open_mainboard": [i.issue_id for i in open_now], "other_current": other}
        due = {i.issue_id: (i.symbol, i.issue_open) for i in open_now}
    except Exception as err:
        run.fail(f"current issues: {err!r}")
    for t in tracked(root):
        if t.issue_close is not None and t.issue_open <= today <= t.issue_close:
            due.setdefault(t.issue_id, (t.symbol, t.issue_open))
    for iid, (symbol, opened) in sorted(due.items()):
        try:
            record_book(net, run, root, symbol, opened, final=False)
        except Exception as err:
            run.fail(f"{iid} snapshot: {err!r}")


def append_log(root: Path, run: Run) -> None:
    line = {"started_at": run.started_at.isoformat(), "finished_at": run.clock().isoformat()}
    line |= {"scheduled": run.scheduled} | run.log
    line |= {"actions": run.actions, "warnings": run.warnings, "errors": run.errors}
    line["ok"] = not run.errors
    root.mkdir(parents=True, exist_ok=True)
    with (root / "run_log.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(line, default=str) + "\n")


def maybe_backup(run: Run, cfg: LiveConfig) -> None:
    """Back up after the scheduled run for the backup slot (19:30)."""
    slot = run.log.get("slot")
    if not (run.scheduled and slot and datetime.fromisoformat(slot).time() == cfg.backup_after):
        return
    try:
        result = backup(cfg.backup, f"data after the {slot} run")
    except (BackupError, OSError) as err:
        run.fail(f"backup: {err}")
        return
    run.log["backup"] = result
    if not result["pushed"]:
        run.warn(f"backup: {result['note']}")


def run_once(
    net: Net,
    root: Path,
    holidays: set[date],
    scheduled: bool,
    clock: Callable[[], datetime],
    version: dict,
    cfg: LiveConfig | None = None,
    v2: IpoV2Config | None = None,
) -> Run:
    run = Run(clock=clock, started_at=clock(), scheduled=scheduled, log=dict(version))
    if cfg is not None:
        run.pdftotext = cfg.pdftotext
        run.log["pdftotext"] = pdftotext_check(cfg.pdftotext)
        if not run.log["pdftotext"]["ok"]:
            run.warn(f"pdftotext not usable: {run.log['pdftotext']}")
    try:
        if not schedule_step(run, root, holidays):
            run.log["skipped"] = "not an NSE trading day (config/holidays.csv)"
            print(run.log["skipped"])
        elif not net.ready():
            run.fail("network: www.nseindia.com unreachable")
        else:
            today = run.started_at.date()
            bid_days(net, run, root, today)
            if v2 is not None:
                record_decisions(run, root, v2, read_log(root))
            for t in tracked(root):
                after_close(net, run, root, t, today, holidays)
        if cfg is not None:
            maybe_backup(run, cfg)
    except Exception as err:
        run.fail(f"run: {err!r}")
    finally:
        append_log(root, run)
    return run


def print_status(root: Path, holidays: set[date], now: datetime) -> None:
    """Issues on disk, the last 10 runs, and slots missed in the last 14 days."""
    print("issue_id | bid period | snapshots | final | listing (open, close) | advert")
    for t in tracked(root):
        lst = t.listing
        listing = f"{lst['listing_date']} ({lst['open']}, {lst['close']})" if lst else "-"
        print(
            f"{t.issue_id} | {t.issue_open} to {t.issue_close} | {t.snapshots} | "
            f"{'yes' if t.final else 'no'} | {listing} | {t.advert or '-'}"
        )
    runs = read_log(root)
    print(f"\nlast runs ({len(runs)} logged):")
    for r in runs[-10:]:
        print(
            f"{r['started_at']} scheduled={r.get('scheduled')} slot={r.get('slot')} "
            f"ok={r.get('ok')} actions={len(r.get('actions', []))} "
            f"warnings={len(r.get('warnings', []))} errors={len(r.get('errors', []))}"
        )
    missed = missed_in_window(covered_slots(runs), now - timedelta(days=14), now, holidays)
    print(f"\nmissed slots, last 14 days: {len(missed)}")
    for s in missed:
        print(f"WARNING: missed scheduled run {s:%a %d %b %Y %H:%M} IST")


def wait_for_network(host: str = "www.nseindia.com", tries: int = 12, pause: float = 10.0) -> bool:
    """True once `host` accepts a TCP connection; Wi-Fi can lag a wake from sleep."""
    for attempt in range(tries):
        try:
            socket.create_connection((host, 443), timeout=10).close()
            return True
        except OSError:
            if attempt < tries - 1:
                time.sleep(pause)
    return False


def keep_awake(on: bool) -> None:
    """Windows only: ask the system not to sleep while a run is going."""
    if sys.platform == "win32":
        import ctypes

        es_continuous, es_system_required = 0x80000000, 0x00000001
        flags = es_continuous | (es_system_required if on else 0)
        ctypes.windll.kernel32.SetThreadExecutionState(flags)


def code_version() -> dict:
    """Main repo HEAD and whether it has local changes, read without writing anything
    (no optional locks, so git status does not refresh the index)."""

    def git(*args: str) -> str:
        cmd = ["git", "--no-optional-locks", "-C", str(REPO_ROOT), *args]
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()

    try:
        return {
            "git_hash": git("rev-parse", "HEAD"),
            "git_dirty": bool(git("status", "--porcelain")),
        }
    except (OSError, subprocess.CalledProcessError):
        return {"git_hash": "unknown", "git_dirty": None}


def check_env(cfg: LiveConfig, out: Path) -> None:
    """Write what this environment (e.g. a scheduled task's) sees; fetches no IPO data."""
    report = {
        "at": datetime.now(IST).isoformat(),
        "user": f"{os.environ.get('USERDOMAIN')}\\{os.environ.get('USERNAME')}",
        "cwd": os.getcwd(),
        "python": sys.executable,
        "pdftotext_on_path": shutil.which("pdftotext"),
        "pdftotext": pdftotext_check(cfg.pdftotext),
        "nse_reachable": wait_for_network(tries=1),
        "backup": backup_check(cfg.backup),
        "code": code_version(),
    }
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


def archive(url: str) -> bytes | None:
    body = archive_get(url)
    time.sleep(ARCHIVE_PAUSE_SECONDS)
    return body


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scheduled", action="store_true", help="started by Task Scheduler")
    parser.add_argument("--status", action="store_true", help="report only; fetch nothing")
    parser.add_argument("--check-env", type=Path, metavar="OUT", help="environment report only")
    args = parser.parse_args(argv)
    holidays, cfg = load_holidays(HOLIDAYS), load_live_config()
    if args.status:
        print_status(LIVE, holidays, datetime.now(IST))
        return 0
    if args.check_env:
        check_env(cfg, args.check_env)
        return 0
    net = Net(nse=NseSession().get, archive=archive, ready=wait_for_network)
    keep_awake(True)
    try:
        now = lambda: datetime.now(IST)  # noqa: E731
        v2 = load_v2_config(IPO_V2)
        run = run_once(net, LIVE, holidays, args.scheduled, now, code_version(), cfg, v2)
    finally:
        keep_awake(False)
    print(
        f"done: {len(run.actions)} actions, {len(run.warnings)} warnings, {len(run.errors)} errors"
    )
    return 1 if run.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
