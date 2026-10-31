"""Listing day of each IPO from NSE bhavcopies (end-of-day files, every security).

An IPO's listing day is the first session on which its ISIN appears in the bhavcopy. On
that day NSE's bhavcopy previous close is the base price, which for an IPO is the issue
price, and the open is the first price of the day; on an IPO's listing day that is the
price discovered in the pre-open call auction (SEBI circular CIR/MRD/DP/01/2012, read
only as a reproduction; see docs/data.md). Pure functions; files are read by the caller.

Matching an issue to a new ISIN, in order (first rule that gives exactly one match):
1. 'isin': the ISIN in NSE's per-issue JSON first appears after bidding closed;
2. 'symbol': a new ISIN, first seen within MATCH_WINDOW_DAYS after the close, whose
   first-day symbol is the list symbol or the JSON's symbol;
3. 'base_price': the only new EQ/BE ISIN in that window whose first-day previous close
   equals the list issue price; 'base_price_band_high' if the list has no issue price
   and the upper end of the price band is used instead. Both flagged for review.
An issue whose list symbol traded before its bid opened, and that matches no new ISIN, is
'already_listed' (a follow-on offer the list does not label as one).
"""

import io
import zipfile
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from nsealgo.data.calendar import IST

BHAV_COLS = [
    "session_date",
    "symbol",
    "series",
    "isin",
    "open",
    "high",
    "low",
    "close",
    "prev_close",
]
OLD_FORMAT = {
    "SYMBOL": "symbol",
    "SERIES": "series",
    "ISIN": "isin",
    "OPEN": "open",
    "HIGH": "high",
    "LOW": "low",
    "CLOSE": "close",
    "PREVCLOSE": "prev_close",
    "TIMESTAMP": "session_date",
}
UDIFF_FORMAT = {
    "TckrSymb": "symbol",
    "SctySrs": "series",
    "ISIN": "isin",
    "OpnPric": "open",
    "HghPric": "high",
    "LwPric": "low",
    "ClsPric": "close",
    "PrvsClsgPric": "prev_close",
    "TradDt": "session_date",
}
LISTING_SERIES = ("EQ", "BE")
MATCH_WINDOW_DAYS = 45
LISTING_COLS = [
    "issue_id",
    "listing_date",
    "symbol",
    "isin",
    "series",
    "list_open",
    "list_high",
    "list_low",
    "list_close",
    "base_price",
    "match_method",
]


def _file_day(text: str) -> date:
    """A bhavcopy's own date: '12-JUL-2016', '13-Jul-20' (some old files) or '2024-09-16'."""
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), fmt).replace(tzinfo=IST).date()
        except ValueError:
            continue
    raise ValueError(f"unparseable bhavcopy date {text!r}")


def read_bhavcopy(path: Path, day: date) -> pd.DataFrame:
    """One bhavcopy zip (either format) for session `day` (from its file name) ->
    BHAV_COLS, every series. Fails if the file's own date is not `day`."""
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"{path.name}: expected one CSV, got {names}")
        raw = pd.read_csv(io.BytesIO(zf.read(names[0])), dtype=str)
    raw.columns = [c.strip() for c in raw.columns]
    old = "SYMBOL" in raw.columns
    cols = OLD_FORMAT if old else UDIFF_FORMAT
    if not old:
        raw = raw[raw["Sgmt"].str.strip() == "CM"]
    df = raw[list(cols)].rename(columns=cols)
    for c in ("symbol", "series", "isin"):
        df[c] = df[c].str.strip()
    for c in ("open", "high", "low", "close", "prev_close"):
        df[c] = pd.to_numeric(df[c].str.strip(), errors="raise")
    stamps = {_file_day(s) for s in df["session_date"].unique()}
    if stamps != {day}:
        raise ValueError(f"{path.name}: file dates {sorted(stamps)} are not {day}")
    df["session_date"] = day
    return df[BHAV_COLS].reset_index(drop=True)


def first_seen(sessions: Iterable[pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, date]]:
    """From bhavcopies in ascending session order: each ISIN's first row (BHAV_COLS, first
    session it appears in, preferring an EQ/BE row that day) and each symbol's first date."""
    isin_rows: list[pd.DataFrame] = []
    seen_isin: set[str] = set()
    symbol_first: dict[str, date] = {}
    last_day: date | None = None
    for df in sessions:
        day = df["session_date"].iloc[0]
        if last_day is not None and day <= last_day:
            raise ValueError(f"sessions out of order at {day}")
        last_day = day
        new = df[~df["isin"].isin(seen_isin)].copy()
        new["_rank"] = (~new["series"].isin(LISTING_SERIES)).astype(int)
        new = new.sort_values(["isin", "_rank"]).drop_duplicates("isin").drop(columns="_rank")
        seen_isin.update(new["isin"])
        isin_rows.append(new)
        for sym in df["symbol"].unique():
            symbol_first.setdefault(sym, day)
    rows = pd.concat(isin_rows, ignore_index=True) if isin_rows else pd.DataFrame(columns=BHAV_COLS)
    return rows, symbol_first


def _listing_row(issue_id: str, row: pd.Series, method: str) -> dict:
    return {
        "issue_id": issue_id,
        "listing_date": row["session_date"],
        "symbol": row["symbol"],
        "isin": row["isin"],
        "series": row["series"],
        "list_open": row["open"],
        "list_high": row["high"],
        "list_low": row["low"],
        "list_close": row["close"],
        "base_price": row["prev_close"],
        "match_method": method,
    }


def match_listing(issue: pd.Series, new_isins: pd.DataFrame, symbol_first: dict[str, date]) -> dict:
    """Listing row (LISTING_COLS) for one issue (issues_frame columns), or a dict with
    only issue_id and match_method in ('already_listed', 'not_found')."""
    close = issue["issue_close"]
    days = new_isins["session_date"]
    window = new_isins[(days > close) & (days <= close + timedelta(days=MATCH_WINDOW_DAYS))]
    if pd.notna(issue["meta_isin"]):
        hit = window[window["isin"] == issue["meta_isin"]]
        if len(hit) == 1:
            return _listing_row(issue["issue_id"], hit.iloc[0], "isin")
    hit = window[window["symbol"] == issue["list_symbol"]]
    if len(hit) == 1:
        return _listing_row(issue["issue_id"], hit.iloc[0], "symbol")
    seen = symbol_first.get(issue["list_symbol"])
    if seen is not None and seen < issue["issue_open"]:
        return {"issue_id": issue["issue_id"], "match_method": "already_listed"}
    price, method = issue["issue_price_list"], "base_price"
    if pd.isna(price):
        price, method = issue.get("price_band_high"), "base_price_band_high"
    if pd.notna(price):
        eq = window[window["series"].isin(LISTING_SERIES)]
        hit = eq[(eq["prev_close"] - price).abs() < 0.005]
        if len(hit) == 1:
            return _listing_row(issue["issue_id"], hit.iloc[0], method)
    return {"issue_id": issue["issue_id"], "match_method": "not_found"}


def listings_frame(
    issues: pd.DataFrame, new_isins: pd.DataFrame, symbol_first: dict[str, date]
) -> pd.DataFrame:
    """match_listing for every issue -> LISTING_COLS (NaN where not listed)."""
    rows = [match_listing(r, new_isins, symbol_first) for _, r in issues.iterrows()]
    out = pd.DataFrame(rows).reindex(columns=LISTING_COLS)
    dup = out["isin"].dropna().duplicated()
    if dup.any():
        raise ValueError(f"one ISIN matched to two issues: {out['isin'].dropna()[dup].tolist()}")
    return out
