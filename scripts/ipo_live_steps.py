"""Per-issue steps of scripts/record_ipo_live.py: bid-day snapshots, the final book, the
listing day and the basis-of-allotment advert. Network access comes in through `Net`, so
tests run these on fakes. Files are written only with nsealgo.data.ipo_live.write_new,
which refuses to overwrite.
"""

import hashlib
import json
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path

from download_bhavcopy import bhavcopy_name, bhavcopy_url
from download_ipo import SITE
from download_ipo_boa import URL as ADVERT_URL

from nsealgo.data.calendar import IST
from nsealgo.data.ipo_boa import advert_name, boa_probe_dates, parse_retail_boa, text_is_readable
from nsealgo.data.ipo_listing import MATCH_WINDOW_DAYS, read_bhavcopy
from nsealgo.data.ipo_live import (
    Tracked,
    book_summary,
    detail_matches,
    issue_id,
    listing_name,
    listing_row,
    scan_issue_dir,
    snapshot_name,
    write_new,
)
from nsealgo.data.ipo_read import pdf_text
from nsealgo.data.live_schedule import is_trading_day

DETAIL_URL = SITE + "/api/ipo-detail?symbol={symbol}&series=EQ"
DETAIL_REFERER = SITE + "/market-data/issue-information?symbol={symbol}&series=EQ&type=Active"
ADVERT_WINDOW_DAYS = 7
BHAVCOPY_DEADLINE = time(18)  # a day's bhavcopy still missing at 18:00 next day: no session
MAGIC = (b"%PDF", b"PK\x03\x04")


@dataclass
class Net:
    nse: Callable[[str, str], bytes]  # (url, referer) -> body, NSE cookie session
    archive: Callable[[str], bytes | None]  # nsearchives URL -> body, None on 404
    ready: Callable[[], bool]  # network reachable (it can lag a wake from sleep)


@dataclass
class Run:
    clock: Callable[[], datetime]
    started_at: datetime
    scheduled: bool
    log: dict = field(default_factory=dict)
    actions: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def warn(self, msg: str) -> None:
        print(f"WARNING: {msg}", flush=True)
        self.warnings.append(msg)

    def fail(self, msg: str) -> None:
        print(f"ERROR: {msg}", flush=True)
        self.errors.append(msg)

    def did(self, action: dict) -> None:
        print(" ".join(f"{k}={v}" for k, v in action.items()), flush=True)
        self.actions.append(action)


def tracked(root: Path) -> list[Tracked]:
    if not root.exists():
        return []
    dirs = sorted(p for p in root.iterdir() if p.is_dir())
    return [t for p in dirs if (t := scan_issue_dir(p)) is not None]


def record_book(
    net: Net, run: Run, root: Path, symbol: str, opened: date, final: bool
) -> dict | None:
    """Fetch and save the per-issue JSON. Returns its run-log summary, or None if NSE's
    JSON is another bid period's (then nothing is saved)."""
    iid, quoted = issue_id(symbol, opened), urllib.parse.quote(symbol)
    body = net.nse(DETAIL_URL.format(symbol=quoted), DETAIL_REFERER.format(symbol=quoted))
    detail = json.loads(body)
    summary = book_summary(detail)
    if not detail_matches(detail, opened):
        run.fail(f"{iid}: NSE's JSON is for bid period {summary['bid_open']}; not saved")
        return None
    path = write_new(root / iid / snapshot_name(run.clock(), final), body)
    run.did({"issue": iid, "kind": "final" if final else "snapshot", "file": path.name} | summary)
    if summary["stamp_unreadable"]:
        run.warn(f"{iid}: unreadable book stamp {summary['stamp_raw']!r}")
    return summary


def check_final(run: Run, t: Tracked, summary: dict | None) -> None:
    if summary is None or t.issue_close is None:
        return
    if summary["stamp"] is None:
        run.warn(f"{t.issue_id}: final book has no stamp ({summary['stamp_raw']!r})")
    elif date.fromisoformat(summary["stamp"][:10]) < t.issue_close:
        run.warn(f"{t.issue_id}: final book stamped {summary['stamp_raw']!r}, before the close")


def read_misses(root: Path) -> set[date]:
    path = root / "bhavcopy" / "misses.jsonl"
    if not path.exists():
        return set()
    lines = path.read_text("utf-8").splitlines()
    return {date.fromisoformat(json.loads(x)["day"]) for x in lines if x.strip()}


def get_bhavcopy(net: Net, root: Path, day: date) -> Path | None:
    path = root / "bhavcopy" / bhavcopy_name(day)
    if path.exists():
        return path
    body = net.archive(bhavcopy_url(day))
    return None if body is None else write_new(path, body)


def find_listing(
    net: Net, run: Run, root: Path, t: Tracked, today: date, holidays: set[date]
) -> dict | None:
    """Walk the bhavcopies from the close day; save and return the first listing row."""
    if t.issue_close is None:
        return None
    misses, day = read_misses(root), t.issue_close
    while day <= min(today, t.issue_close + timedelta(days=MATCH_WINDOW_DAYS)):
        if is_trading_day(day, holidays) and day not in misses:
            path = get_bhavcopy(net, root, day)
            if path is None:
                deadline = datetime.combine(day + timedelta(days=1), BHAVCOPY_DEADLINE, tzinfo=IST)
                if run.clock() < deadline:
                    run.did({"issue": t.issue_id, "kind": "listing_wait", "bhavcopy": str(day)})
                    return None
                with (root / "bhavcopy" / "misses.jsonl").open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"day": str(day), "at": run.clock().isoformat()}) + "\n")
            elif (row := listing_row(read_bhavcopy(path, day), t.symbol, t.isin)) is not None:
                if day == t.issue_close:
                    run.warn(f"{t.issue_id}: {t.symbol} already trades on the close day {day}")
                    return None
                return save_listing(run, root, t, row, path)
        day += timedelta(days=1)
    return None


def save_listing(run: Run, root: Path, t: Tracked, row: dict, bhav: Path) -> dict:
    content = {"issue_id": t.issue_id, "listing_date": row["session_date"]} | row
    content |= {
        "price_band": list(t.band) if t.band else None,
        "bhavcopy": bhav.name,
        "bhavcopy_sha256": hashlib.sha256(bhav.read_bytes()).hexdigest(),
        "recorded_at": run.clock().isoformat(),
    }
    day = date.fromisoformat(row["session_date"])
    write_new(root / t.issue_id / listing_name(day), json.dumps(content, indent=1).encode())
    keys = ("listing_date", "open", "close", "prev_close", "match")
    run.did({"issue": t.issue_id, "kind": "listing"} | {k: content[k] for k in keys})
    if t.band and not t.band[0] - 0.005 <= row["prev_close"] <= t.band[1] + 0.005:
        run.warn(f"{t.issue_id}: base price {row['prev_close']} is outside the band {t.band}")
    return content


def advert_fields(run: Run, path: Path, lot: int | None) -> dict:
    """A few parsed fields for the run log; the advert file is the record."""
    try:
        prose = pdf_text(path, table=False)
        if not text_is_readable(prose):
            return {"readable": False}
        boa = parse_retail_boa(prose, pdf_text(path, table=True), lot)
    except OSError as err:  # FileNotFoundError: pdftotext is not on PATH
        run.warn(f"{path.name} saved but not parsed: {err!r}")
        return {}
    if boa is None:
        return {"readable": True, "retail_section": False}
    keep = ("retail_sub_boa", "min_bid_shares", "min_bid_ratio_num", "min_bid_ratio_den")
    d = boa.as_dict()
    return {"readable": True, "allotment_date": str(d["allotment_date"])} | {k: d[k] for k in keep}


def probe_advert(net: Net, run: Run, root: Path, t: Tracked, listed: dict, today: date) -> None:
    if t.issue_close is None:
        return
    tried = []
    for day in boa_probe_dates(t.issue_close, date.fromisoformat(listed["listing_date"])):
        if day > today:
            continue
        name = advert_name(listed["isin"], day)
        tried.append(str(day))
        body = net.archive(ADVERT_URL.format(name=name))
        if body is None:
            continue
        if not body.startswith(MAGIC):
            raise ValueError(f"{name}: neither a PDF nor a zip")
        path = write_new(root / t.issue_id / name, body)
        fields = advert_fields(run, path, t.lot)
        run.did({"issue": t.issue_id, "kind": "advert", "file": name} | fields)
        return
    run.did({"issue": t.issue_id, "kind": "advert_not_yet", "tried": tried})


def after_close(
    net: Net, run: Run, root: Path, t: Tracked, today: date, holidays: set[date]
) -> None:
    """Final book, listing day and advert for an issue past its close day."""
    if t.issue_close is None:
        run.warn(f"{t.issue_id}: no per-issue JSON of this bid period on disk; skipped")
        return
    if today <= t.issue_close:
        return
    if not t.final:
        try:
            check_final(run, t, record_book(net, run, root, t.symbol, t.issue_open, final=True))
        except Exception as err:
            run.fail(f"{t.issue_id} final book: {err!r}")
    listed = t.listing
    if listed is None and today <= t.issue_close + timedelta(days=MATCH_WINDOW_DAYS):
        try:
            listed = find_listing(net, run, root, t, today, holidays)
        except Exception as err:
            run.fail(f"{t.issue_id} listing: {err!r}")
    if listed is None or t.advert is not None:
        return
    if today <= date.fromisoformat(listed["listing_date"]) + timedelta(days=ADVERT_WINDOW_DAYS):
        try:
            probe_advert(net, run, root, t, listed, today)
        except Exception as err:
            run.fail(f"{t.issue_id} advert: {err!r}")
