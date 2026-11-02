"""Live IPO recorder (IPO track step 3, data only): parsing and file naming for
scripts/record_ipo_live.py. No strategy reads these files and nothing here is a trial.

NSE sources, read from the IPO page's own script
(dist/js/sections/live-market/upcoming-ipo.js, 2026-11-02):
- /api/ipo-current-issue: the "Current Issues" table, one row per issue open for bids,
  mainboard and SME. Fields used: symbol, companyName, series ('EQ' or 'SME'),
  issueStartDate, issueEndDate, status.
- /api/ipo-detail?symbol=<SYMBOL>&series=EQ: the per-issue JSON (as scripts/download_ipo.py
  fetches it). Its activeCat is the consolidated category-wise book and activeCat.updateTime
  its 'Updated as on' stamp; parsed with nsealgo.data.ipo.

Layout under data/live/ipo/. Every file is created once and never rewritten:
  current_issue/<stamp>.json            each run's /api/ipo-current-issue body
  <issue_id>/<stamp>.json               per-issue JSON fetched on a bid day (close day too)
  <issue_id>/final_<stamp>.json         per-issue JSON from the first run after the close day
  <issue_id>/listing_<YYYYMMDD>.json    the issue's row in the listing day's bhavcopy
  <issue_id>/ADV_<ISIN>_<DDMONYYYY>.pdf basis-of-allotment advert, NSE's own file name
  bhavcopy/<NSE file name>.zip          bhavcopies read to find the listing day
  run_log.jsonl                         one line per run
<stamp> is the fetch time in IST, 'YYYYMMDDTHHMMSS+0530'. <issue_id> is
'<SYMBOL>_<YYYYMMDD of the bid open>', as in the research dataset (nsealgo.data.ipo).
"""

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from nsealgo.data.calendar import IST
from nsealgo.data.ipo import (
    category_bids,
    issue_info,
    parse_issue_period,
    parse_lot,
    parse_nse_date,
    parse_price_range,
)
from nsealgo.data.ipo_listing import LISTING_SERIES

STAMP_FORMAT = "%Y%m%dT%H%M%S%z"
_STAMP = r"\d{8}T\d{6}\+0530"
_SNAPSHOT_FILE = re.compile(rf"(final_)?({_STAMP})\.json")
_SYMBOL = re.compile(r"[A-Z0-9][A-Z0-9&-]*")
_ISSUE_ID = re.compile(r"([A-Z0-9][A-Z0-9&-]*)_(\d{8})")
_LISTING_FILE = re.compile(r"listing_(\d{8})\.json")


def file_stamp(at: datetime) -> str:
    """Fetch time as used in file names: 2026-11-02 12:00:04 IST -> '20261102T120004+0530'."""
    if at.tzinfo is None:
        raise ValueError(f"naive datetime {at!r}")
    return at.astimezone(IST).strftime(STAMP_FORMAT)


def snapshot_name(at: datetime, final: bool = False) -> str:
    return f"{'final_' if final else ''}{file_stamp(at)}.json"


def parse_snapshot_name(name: str) -> tuple[bool, datetime] | None:
    """(is the final book, fetch time) for a snapshot file name; None for other files."""
    m = _SNAPSHOT_FILE.fullmatch(name)
    if m is None:
        return None
    return bool(m[1]), datetime.strptime(m[2], STAMP_FORMAT).astimezone(IST)


def listing_name(day: date) -> str:
    return f"listing_{day:%Y%m%d}.json"


def issue_id(symbol: str, issue_open: date) -> str:
    """'BCSSL', 2026-10-29 -> 'BCSSL_20261029'. Refuses symbols that are not NSE-style
    (capitals, digits, '&', '-'), which also keeps the id safe as a directory name."""
    if _SYMBOL.fullmatch(symbol) is None:
        raise ValueError(f"unexpected symbol {symbol!r}")
    return f"{symbol}_{issue_open:%Y%m%d}"


def parse_issue_id(name: str) -> tuple[str, date] | None:
    m = _ISSUE_ID.fullmatch(name)
    if m is None:
        return None
    return m[1], datetime.strptime(m[2], "%Y%m%d").replace(tzinfo=IST).date()


def write_new(path: Path, body: bytes) -> Path:
    """Create `path` with `body`; FileExistsError if it exists (snapshots are never
    overwritten)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as fh:
        fh.write(body)
    return path


@dataclass(frozen=True)
class OpenIssue:
    symbol: str
    company: str
    issue_open: date
    issue_close: date
    status: str

    @property
    def issue_id(self) -> str:
        return issue_id(self.symbol, self.issue_open)


def current_issue_kind(row: Mapping) -> str:
    """'mainboard', or why a /api/ipo-current-issue row is not a mainboard IPO: 'sme',
    'not_equity' (any series but EQ and SME), 'fpo', 'partly_paid'."""
    series = (row.get("series") or "").strip().upper()
    if series == "SME":
        return "sme"
    if series != "EQ":
        return "not_equity"
    if re.search(r"\bFPO\b|Further\s+Public\s+Offer", row.get("companyName") or "", re.I):
        return "fpo"
    if re.search(r"PP\d*$", (row.get("symbol") or "").strip()):
        return "partly_paid"
    return "mainboard"


def open_mainboard(rows: Iterable[Mapping], today: date) -> tuple[list[OpenIssue], list[dict]]:
    """Mainboard rows whose bid dates contain `today`, and every other row as {symbol,
    series, status, reason}: its kind, 'not_open' (mainboard, `today` outside its dates)
    or 'bad_row: ...' (dates or symbol unreadable)."""
    issues: list[OpenIssue] = []
    other: list[dict] = []
    for row in rows:
        sym = (row.get("symbol") or "").strip()
        note = {"symbol": sym, "series": row.get("series"), "status": row.get("status")}
        kind = current_issue_kind(row)
        if kind != "mainboard":
            other.append(note | {"reason": kind})
            continue
        dates = (row.get("issueStartDate"), row.get("issueEndDate"))
        try:
            start, end = parse_nse_date(dates[0]), parse_nse_date(dates[1])
            if start is None or end is None or end < start:
                raise ValueError(f"bid dates {dates!r}")
            issue_id(sym, start)  # validates the symbol
        except ValueError as err:
            other.append(note | {"reason": f"bad_row: {err}"})
            continue
        if start <= today <= end:
            company = (row.get("companyName") or "").strip()
            issues.append(OpenIssue(sym, company, start, end, row.get("status") or ""))
        else:
            other.append(note | {"reason": "not_open"})
    return issues, other


def parse_stamp(text: str | None) -> datetime | None:
    """The book's stamp: 'Updated as on 02-Nov-2026 11:24:00' -> 2026-11-02 11:24 IST;
    'Updated as on null', '' or None -> None. Any other form raises ValueError (older
    books used 'Updated as on 09th Dec 2021 at 1700 hrs'; not expected live)."""
    s = re.sub(r"^\s*Updated\s+as\s+on\s*", "", text or "", flags=re.I).strip()
    if s.lower() in ("", "null"):
        return None
    m = re.fullmatch(r"(\d{1,2}-[A-Za-z]{3,9}-\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?", s)
    day = parse_nse_date(m[1]) if m else None
    if m is None or day is None:
        raise ValueError(f"unparseable book stamp {text!r}")
    return datetime(day.year, day.month, day.day, int(m[2]), int(m[3]), int(m[4] or 0), tzinfo=IST)


def _period(detail: Mapping) -> tuple[date, date] | None:
    try:
        return parse_issue_period(issue_info(detail).get("Issue Period"))
    except ValueError:
        return None


def detail_matches(detail: Mapping, issue_open: date) -> bool:
    """True if the per-issue JSON is this attempt's: its bid period starts on `issue_open`.
    NSE keeps one JSON per symbol, so a relaunched issue's JSON is the later attempt's."""
    period = _period(detail)
    return period is not None and period[0] == issue_open


def book_summary(detail: Mapping) -> dict:
    """Run-log fields of a per-issue JSON: the stamp (raw and parsed), bid period, lot, and
    retail and total (shares offered, shares bid, times). A stamp parse_stamp cannot read
    is kept raw with stamp=None and stamp_unreadable=True."""
    raw = (detail.get("activeCat") or {}).get("updateTime")
    try:
        stamp, unreadable = parse_stamp(raw), False
    except ValueError:
        stamp, unreadable = None, True
    period = _period(detail)
    retail, total = category_bids(detail, "Retail Individual"), category_bids(detail, "Total")
    info = issue_info(detail)
    return {
        "stamp_raw": raw,
        "stamp": stamp.isoformat() if stamp else None,
        "stamp_unreadable": unreadable,
        "bid_open": period[0].isoformat() if period else None,
        "bid_close": period[1].isoformat() if period else None,
        "lot": parse_lot(info.get("Bid Lot")) or parse_lot(info.get("Minimum Order Quantity")),
        "retail": list(retail) if retail else None,
        "total": list(total) if total else None,
        "isin": (detail.get("metaInfo") or {}).get("isin") or None,
    }


def price_band(detail: Mapping) -> tuple[float, float] | None:
    try:
        return parse_price_range(issue_info(detail).get("Price Range"))
    except ValueError:
        return None


def listing_row(bhav: pd.DataFrame, symbol: str, isin: str | None) -> dict | None:
    """The issue's EQ/BE row in one bhavcopy (nsealgo.data.ipo_listing.read_bhavcopy
    columns): by ISIN when known, else (or if the ISIN is absent) by symbol. None if
    neither is there; ValueError if two rows match."""
    eq = bhav[bhav["series"].isin(LISTING_SERIES)]
    for method, hit in (
        ("isin", eq[eq["isin"] == isin] if isin else eq.iloc[0:0]),
        ("symbol", eq[eq["symbol"] == symbol]),
    ):
        if len(hit) > 1:
            raise ValueError(f"{symbol}: {len(hit)} bhavcopy rows match by {method}")
        if len(hit) == 1:
            r = hit.iloc[0]
            fields = ["symbol", "series", "isin", "open", "high", "low", "close", "prev_close"]
            out = {k: (r[k].item() if hasattr(r[k], "item") else r[k]) for k in fields}
            return {"session_date": r["session_date"].isoformat(), "match": method} | out
    return None


@dataclass(frozen=True)
class Tracked:
    """What is on disk for one issue directory."""

    issue_id: str
    symbol: str
    issue_open: date
    issue_close: date | None  # from the latest per-issue JSON of this attempt
    lot: int | None
    isin: str | None  # latest metaInfo.isin, if NSE has filled it
    band: tuple[float, float] | None
    snapshots: int
    final: bool
    listing: dict | None  # the saved listing file's content
    advert: str | None  # advert file name


def scan_issue_dir(path: Path) -> Tracked | None:
    """Tracked for data/live/ipo/<issue_id>/, or None if the name is not an issue id."""
    parsed = parse_issue_id(path.name)
    if parsed is None:
        return None
    symbol, opened = parsed
    snaps: list[tuple[datetime, bool, Path]] = []
    for p in path.iterdir():
        if (n := parse_snapshot_name(p.name)) is not None:
            snaps.append((n[1], n[0], p))
    snaps.sort()
    mine = [json.loads(p.read_bytes()) for _, _, p in snaps]
    mine = [d for d in mine if detail_matches(d, opened)]
    latest = book_summary(mine[-1]) if mine else {}
    isins = [i for d in mine if (i := (d.get("metaInfo") or {}).get("isin"))]
    listings = sorted(p for p in path.iterdir() if _LISTING_FILE.fullmatch(p.name))
    adverts = sorted(p.name for p in path.glob("ADV_*"))
    return Tracked(
        issue_id=path.name,
        symbol=symbol,
        issue_open=opened,
        issue_close=date.fromisoformat(latest["bid_close"]) if latest.get("bid_close") else None,
        lot=latest.get("lot"),
        isin=isins[-1] if isins else None,
        band=price_band(mine[-1]) if mine else None,
        snapshots=sum(not f for _, f, _ in snaps),
        final=any(f for _, f, _ in snaps),
        listing=json.loads(listings[0].read_text("utf-8")) if listings else None,
        advert=adverts[0] if adverts else None,
    )


def decision_inputs(detail: Mapping) -> dict:
    """What the IPO v2 rule reads from a per-issue JSON (nsealgo.strategies.ipo_v2):
    total (consolidated) and retail times, lot, top of the band and NSE's stamp. A missing
    or unreadable field is None."""
    s, band = book_summary(detail), price_band(detail)
    return {
        "total_x": s["total"][2] if s["total"] else None,
        "retail_x": s["retail"][2] if s["retail"] else None,
        "lot": s["lot"],
        "band_high": band[1] if band else None,
        "stamp": s["stamp"],
    }
