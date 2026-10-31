"""Mainboard IPO dataset: NSE's past-issue lists and per-issue JSON -> one row per issue.

Pure functions on parsed JSON (scripts/build_ipo.py does the I/O). Sources, both PRIMARY
(www.nseindia.com, downloaded by scripts/download_ipo.py):
- the past-issue list (security_type=Equity): symbol, company, bid open and close dates,
  price band, issue price;
- the per-issue JSON: issue information (bid period, price band, bid lot, registrar) and
  the consolidated (all exchanges) category-wise bid book at the close of bidding.

A list row is kept as an issue unless a rule below drops it (`list_row_kind`). The JSON is
used for a row only when its bid period starts on the row's open date: NSE keeps one JSON
per symbol, so a relaunched issue (same symbol) gets the later attempt's JSON or none.
"""

import re
from collections.abc import Iterable, Mapping
from datetime import date

import pandas as pd

MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    )
}
FULL_MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
MONTH_NAMES = MONTHS | {m: i + 1 for i, m in enumerate(FULL_MONTHS)} | {"sept": 9}
ISSUE_COLS = [
    "issue_id",
    "list_symbol",
    "company",
    "issue_open",
    "issue_close",
    "price_band_low",
    "price_band_high",
    "issue_price_list",
    "list_listing_date",
    "list_status",
    "list_row_overwritten",
    "lot_size",
    "registrar",
    "detail_used",
    "retail_shares_offered_exch",
    "retail_shares_bid_exch",
    "retail_sub_exch",
    "total_sub_exch",
    "meta_isin",
    "meta_listing_date",
]
_NUM = r"(\d[\d,]*(?:\.\d+)?)"


def parse_nse_date(text: str | None) -> date | None:
    """'02-JAN-2025', '09-Sept-2024', '16-June-2021', '2024-09-16' -> date; '-', '' or
    None -> None."""
    s = (text or "").strip()
    if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s):
        return date(int(m[1]), int(m[2]), int(m[3]))
    if m := re.fullmatch(r"(\d{1,2})-([A-Za-z]{3,9})-(\d{4})", s):
        mon = MONTH_NAMES.get(m[2].lower())
        if mon is None:
            raise ValueError(f"unknown month in {text!r}")
        return date(int(m[3]), mon, int(m[1]))
    if s in ("", "-"):
        return None
    raise ValueError(f"unparseable NSE date {text!r}")


def parse_long_date(text: str) -> date | None:
    """'September 14, 2020', 'May 04, 2022', '10th October, 2019', 'Thursday, July, 22, 2021'
    -> date; None unless exactly one month name, one day and one year are found."""
    s = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", text)
    words = re.sub(r"[,.]", " ", s).split()
    months = [MONTH_NAMES[w.lower()] for w in words if w.lower() in MONTH_NAMES]
    nums = [int(w) for w in words if w.isdigit()]
    days = [n for n in nums if 1 <= n <= 31]
    years = [n for n in nums if 2000 <= n <= 2100]
    if len(months) != 1 or len(days) != 1 or len(years) != 1:
        return None
    return date(years[0], months[0], days[0])


def _number(text: str) -> float:
    return float(text.replace(",", ""))


def parse_price_range(text: str | None) -> tuple[float, float] | None:
    """'Rs.204 to Rs.215 ', 'Rs. 300/- to Rs. 315/- ', 'Rs.1000' -> (low, high)."""
    nums = [_number(n) for n in re.findall(_NUM, text or "")]
    if len(nums) == 1:
        return nums[0], nums[0]
    if len(nums) == 2 and nums[0] <= nums[1]:
        return nums[0], nums[1]
    if not nums:
        return None
    raise ValueError(f"unparseable price range {text!r}")


def parse_issue_period(text: str | None) -> tuple[date, date] | None:
    """'08-May-2024 to 10-May-2024' or '08-May-2017, 09-May-2017 and 11-May-2017' (bid
    days listed around a holiday) -> (first day, last day). Text in brackets, such as
    '(Excluding 22-Jan-2024)', is a holiday note and is ignored."""
    if not (text or "").strip():
        return None
    body = re.sub(r"\([^)]*\)", " ", text or "")
    days = [parse_nse_date(t) for t in re.findall(r"\d{1,2}-[A-Za-z]{3,9}-\d{4}", body)]
    if not days:  # 'September 29, 2020 to October 1, 2020'
        days = [parse_long_date(p) for p in re.split(r"\bto\b", body.strip(' "'), flags=re.I)]
    if len(days) < 2 or None in days or days != sorted(days):
        raise ValueError(f"unparseable issue period {text!r}")
    return days[0], days[-1]


def parse_lot(text: str | None) -> int | None:
    """'47 Equity Shares and in multiples thereof', 'Minimum 132 Equity shares ...' -> 47, 132."""
    m = re.match(r"\s*(?:Minimum\s+)?(\d[\d,]*)\s+Equity", text or "", flags=re.I)
    return int(m[1].replace(",", "")) if m else None


def issue_info(detail: Mapping) -> dict[str, str]:
    """The 'Issue Information' table of a per-issue JSON as {title: value}."""
    rows = (detail.get("issueInfo") or {}).get("dataList") or []
    return {(r.get("title") or "").strip(): (r.get("value") or "").strip() for r in rows}


def category_bids(detail: Mapping, prefix: str) -> tuple[float, float, float] | None:
    """(shares offered, shares bid, times) of the first consolidated category whose name
    starts with `prefix`, e.g. 'Retail Individual' or 'Total'. Some older JSON has no
    'times' field; it is then shares bid / shares offered, which is its definition."""
    rows = (detail.get("activeCat") or {}).get("dataList") or []
    for r in rows:
        if (r.get("category") or "").strip().startswith(prefix):
            try:
                offered, bid = float(r["noOfShareOffered"]), float(r["noOfSharesBid"])
            except (KeyError, TypeError, ValueError):
                return None
            times = r.get("noOfTotalMeant")
            if times not in (None, ""):
                return offered, bid, float(times)
            return (offered, bid, bid / offered) if offered > 0 else None
    return None


def list_row_kind(row: Mapping) -> str:
    """'ipo', 'withdrawn' (kept), or why the row is not an IPO: 'ncd', 'fpo', 'partly_paid',
    'withdrawal_window', 'not_equity'. Rules read only the list row itself; 'ncd' is NSE's
    own page code for the issue (htmSym, e.g. 'rhflncd1')."""
    name = row.get("company") or ""
    if "ncd" in (row.get("htmSym") or "").lower():
        return "ncd"
    if re.search(r"\bFPO\b", name, re.I):
        return "fpo"
    if re.search(r"special\s+withdrawal", name, re.I):
        return "withdrawal_window"
    if re.search(r"PP\d*$", (row.get("symbol") or "").strip()):
        return "partly_paid"
    if (row.get("securityType") or "").strip() not in ("EQ", "BE", "P1", "W1"):
        return "not_equity"
    if re.search(r"withdrawn", name, re.I):
        return "withdrawn"
    return "ipo"


def _dedupe(rows: Iterable[Mapping]) -> list[dict]:
    """One row per (symbol, open date); the yearly lists overlap at year ends. Two
    different rows for one key are allowed only if exactly one says 'withdrawn' (NSE
    lists some withdrawn issues twice); that one is kept."""
    out: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = ((r.get("symbol") or "").strip(), (r.get("ipoStartDate") or "").strip())
        if key in out and out[key] != dict(r):
            marked = [x for x in (out[key], dict(r)) if list_row_kind(x) == "withdrawn"]
            if len(marked) != 1:
                raise ValueError(f"conflicting list rows for {key}")
            out[key] = marked[0]
            continue
        out[key] = dict(r)
    return list(out.values())


def _issue_price(text: str | None) -> float | None:
    s = (text or "").strip()
    return None if s in ("", "-") else _number(s)


def _detail_fields(detail: Mapping | None, open_date: date) -> dict:
    """Fields taken from the per-issue JSON, or {'detail_used': False} if it is another
    attempt's (bid period not starting on `open_date`) or missing."""
    info = issue_info(detail or {})
    period = parse_issue_period(info.get("Issue Period"))
    if detail is None or period is None or period[0] != open_date:
        return {"detail_used": False}
    retail = category_bids(detail, "Retail Individual")
    total = category_bids(detail, "Total")
    meta = detail.get("metaInfo") or {}
    lot = parse_lot(info.get("Bid Lot")) or parse_lot(info.get("Minimum Order Quantity"))
    return {
        "detail_used": True,
        "lot_size": lot,
        "registrar": info.get("Name of the Registrar") or None,
        "retail_shares_offered_exch": retail[0] if retail else None,
        "retail_shares_bid_exch": retail[1] if retail else None,
        "retail_sub_exch": retail[2] if retail else None,
        "total_sub_exch": total[2] if total else None,
        "meta_isin": meta.get("isin") or None,
        "meta_listing_date": parse_nse_date(meta.get("listingDate")),
    }


TRUST_TYPES = ("IV", "RR")  # InvIT and REIT units: not mainboard equity IPOs


def _is_trust(row: Mapping) -> bool:
    name = row.get("company") or ""
    return (row.get("securityType") or "").strip() in TRUST_TYPES or bool(
        re.search(r"\b(Trust|InvIT|REIT)\b", name, re.I)
    )


def overwritten_ipo_rows(all_rows: Iterable[Mapping], eq_rows: Iterable[Mapping]) -> list[dict]:
    """IPO rows that NSE's Equity list lost. NSE overwrites an issue's list row with the
    company's later listed security (NTPC Green's Nov 2024 IPO row shows a 2026 bond:
    symbol 727NGEL36, type N0, listing 13-JUL-2026), so the row drops out of the Equity
    filter. Such a row keeps its bid dates, price band and page code (htmSym). Taken from
    the unfiltered list: not in the Equity list, not SME, not a trust, not an NCD, and a
    price band of two different prices. Returned as equity rows: symbol = page code in
    capitals (usually the equity symbol), listing date and issue price blanked (they are
    the later security's), and 'overwritten': True."""
    seen = {
        ((r.get("symbol") or "").strip(), (r.get("ipoStartDate") or "").strip()) for r in eq_rows
    }
    out: dict[tuple[str, str], dict] = {}
    for r in all_rows:
        key = ((r.get("symbol") or "").strip(), (r.get("ipoStartDate") or "").strip())
        sec = (r.get("securityType") or "").strip()
        band = set(re.findall(_NUM, r.get("priceRange") or ""))
        if key in seen or sec in ("EQ", "BE", "P1", "W1", "SME") or _is_trust(r):
            continue
        if "ncd" in (r.get("htmSym") or "").lower() or len(band) != 2:
            continue
        fixed = dict(r) | {
            "symbol": (r.get("htmSym") or "").strip().upper(),
            "securityType": "EQ",
            "listingDate": "-",
            "issuePrice": "-",
            "overwritten": True,
        }
        out[(fixed["symbol"], key[1])] = fixed
    return list(out.values())


def issues_frame(list_rows: Iterable[Mapping], details: Mapping[str, Mapping]) -> pd.DataFrame:
    """One row per issue kept by `list_row_kind` (ISSUE_COLS), sorted by open date.
    `details` maps list symbol -> per-issue JSON."""
    out = []
    for r in _dedupe(list_rows):
        kind = list_row_kind(r)
        if kind not in ("ipo", "withdrawn"):
            continue
        sym = r["symbol"].strip()
        open_date, close_date = parse_nse_date(r["ipoStartDate"]), parse_nse_date(r["ipoEndDate"])
        if open_date is None or close_date is None:
            raise ValueError(f"{sym}: list row without bid dates")
        band = parse_price_range(r.get("priceRange"))
        row = {
            "issue_id": f"{sym}_{open_date:%Y%m%d}",
            "list_symbol": sym,
            "company": re.sub(r"\s*-\s*Issue Withdrawn\s*$", "", r["company"].strip(), flags=re.I),
            "issue_open": open_date,
            "issue_close": close_date,
            "price_band_low": band[0] if band else None,
            "price_band_high": band[1] if band else None,
            "issue_price_list": _issue_price(r.get("issuePrice")),
            "list_listing_date": parse_nse_date(r.get("listingDate")),
            "list_status": kind,
            "list_row_overwritten": bool(r.get("overwritten", False)),
        }
        out.append(row | _detail_fields(details.get(sym), open_date))
    df = pd.DataFrame(out).reindex(columns=ISSUE_COLS)
    if df["issue_id"].duplicated().any():
        raise ValueError(f"duplicate issue ids: {df.loc[df['issue_id'].duplicated(), 'issue_id']}")
    return df.sort_values(["issue_open", "issue_id"], ignore_index=True)
