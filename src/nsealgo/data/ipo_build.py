"""Mainboard IPO dataset: assemble the clean table and run the per-row checks.

Inputs come from ipo_read.py; the parsing is in ipo.py (NSE JSON), ipo_listing.py
(bhavcopies) and ipo_boa.py (allotment adverts). Every output field has a source column;
nothing is filled from an aggregator here.
"""

from datetime import date, timedelta

import pandas as pd

from nsealgo.data.ipo_read import BoaMap

P_TOLERANCE = 0.02  # relative gap allowed between the 1-lot ratio and allottees/applications
PENDING_DAYS = 30  # an unmatched issue that closed this recently may simply not be listed yet


def _status(row: pd.Series, last_session: date, exceptions: dict[str, str]) -> str:
    if row["issue_id"] in exceptions:
        return exceptions[row["issue_id"]]
    if pd.notna(row["listing_date"]):
        return "listed"
    if row["match_method"] == "already_listed":
        return "already_listed"
    if row["list_status"] == "withdrawn":
        return "withdrawn"
    if row["issue_close"] > last_session - timedelta(days=PENDING_DAYS):
        return "pending"
    return "not_found_on_nse"


def _issue_price(row: pd.Series) -> tuple[float | None, str]:
    """The list's issue price if the listing-day base price agrees. Otherwise whichever of
    the two lies inside the price band, the list price first (AU Small Finance Bank's
    2017 base price was not its issue price; Music Broadcast's and Anupam Rasayan's list
    prices were overwritten by later corporate actions). Else nothing."""
    lst, base = row["issue_price_list"], row["base_price"]
    lo, hi = row["price_band_low"], row["price_band_high"]

    def in_band(v: float) -> bool:
        return bool(pd.notna(v) and pd.notna(lo) and lo - 0.005 <= v <= hi + 0.005)

    if pd.notna(base) and pd.notna(lst) and abs(base - lst) < 0.005:
        return lst, "nse_list=bhavcopy_base"
    if pd.isna(base) and pd.notna(lst):
        return lst, "nse_list(not_listed)"
    if in_band(lst):
        return lst, "nse_list(base_disagrees)"
    if in_band(base):
        missing = pd.isna(lst)
        return base, "bhavcopy_base(list_missing)" if missing else "bhavcopy_base(list_disagrees)"
    return None, "conflict"


def allottees_plausible(b: dict) -> bool:
    """False when the advert's 'to N successful' figure cannot be the allottee count: more
    than the valid applications, or more than the shares allotted cover at one lot each
    (NOVAAGRI 2024 prints its application count there)."""
    n, apps = b.get("retail_allottees"), b.get("retail_valid_applications")
    shares, lot = b.get("retail_shares_allotted"), b.get("min_bid_shares")
    if n is None:
        return True
    if apps is not None and n > apps:
        return False
    return not (shares is not None and lot and n * lot > shares * 1.01)  # 1%: rounding


MIN_ONE_LOT_SHARE = 0.10  # parsed adverts: 5th percentile 46%, median 72% (2026-10-31 build)


def one_lot_row_big_enough(b: dict, retail_sub: float | None) -> bool:
    """False when the parsed 1-lot row holds under MIN_ONE_LOT_SHARE of the shares applied
    for, estimated as shares allotted x max(subscription, 1) (an undersubscribed book is
    allotted in full): then it is another table's row. Undersubscribed books in the same
    build: 5th percentile 33%, median 61%."""
    apps, lot, shares = (
        b.get(k) for k in ("min_bid_applications", "min_bid_shares", "retail_shares_allotted")
    )
    if not (apps and lot and shares and retail_sub):
        return True
    return apps * lot >= MIN_ONE_LOT_SHARE * shares * max(retail_sub, 1.0)


def p_bounds(retail_sub: float | None) -> tuple[float, float]:
    """Range a 1-lot chance can take at retail subscription x. Under the lottery
    P = lots available / applications = Lbar / x (Lbar = average lots applied for, >= 1),
    capped at 1, so P >= 1/x; 0.9/x and 6/x leave room for rejections and large bids."""
    if retail_sub is None or not retail_sub > 0:
        return 0.0, 1.0
    return min(1.0, 0.9 / retail_sub), min(1.0, 6.0 / retail_sub)


def _p_one_lot(
    b: dict, retail_sub: float | None = None
) -> tuple[float | None, str | None, bool | None, bool]:
    """P(allotment) of a 1-lot retail application, its method, whether the 1-lot ratio and
    allottees/applications agree (None if not both available), and whether a candidate was
    dropped for falling outside p_bounds(retail_sub). The ratio is preferred. Allottee
    figures that fail allottees_plausible must already be removed from `b`."""
    ratio = None
    if b.get("min_bid_ratio_den") and b.get("min_bid_allotted_shares") == b.get("min_bid_shares"):
        ratio = b["min_bid_ratio_num"] / b["min_bid_ratio_den"]
    ident = None
    if b.get("retail_allottees") and b.get("retail_valid_applications"):
        ident = min(1.0, b["retail_allottees"] / b["retail_valid_applications"])
    agree = None
    if ratio is not None and ident is not None:
        agree = abs(ratio - ident) <= P_TOLERANCE * max(ident, 1e-9)
    lo, hi = p_bounds(retail_sub)
    dropped = False
    for value, method in ((ratio, "min_bid_ratio"), (ident, "allottees_over_applications")):
        if value is None:
            continue
        if lo - 1e-9 <= value <= hi + 1e-9:
            return value, method, agree, dropped
        dropped = True
    boa_sub = b.get("retail_sub_boa")
    if boa_sub is not None and boa_sub < 1:
        # an undersubscribed category is allotted in full to every valid bid. Only the
        # advert's own multiple is used: from the exchange bid book alone, years without
        # adverts would get a chance only for their undersubscribed issues.
        return 1.0, "retail_undersubscribed", agree, dropped
    return None, None, agree, dropped


CLEAN_COLS = [
    "issue_id",
    "status",
    "company",
    "symbol",
    "list_symbol",
    "isin",
    "series",
    "issue_open",
    "issue_close",
    "price_band_low",
    "price_band_high",
    "issue_price",
    "issue_price_src",
    "lot_size",
    "lot_size_src",
    "lot_value_at_cap",
    "retail_discount",
    "retail_sub",
    "retail_sub_src",
    "retail_sub_exch",
    "retail_sub_boa",
    "retail_valid_applications",
    "retail_shares_applied",
    "retail_allottees",
    "retail_shares_allotted",
    "retail_lots_allotted",
    "min_bid_applications",
    "min_bid_ratio",
    "p_1lot",
    "p_1lot_method",
    "allotment_date",
    "allotment_date_src",
    "designated_exchange",
    "boa_file",
    "listing_date",
    "list_open",
    "list_high",
    "list_low",
    "list_close",
    "base_price",
    "listing_match",
    "ret_open",
    "ret_close",
    "total_sub_exch",
    "registrar",
    "checks",
]


BOA_KEYS = (
    "retail_sub_boa",
    "retail_shares_allotted",
    "retail_allottees",
    "retail_valid_applications",
    "retail_shares_applied",
    "min_bid_shares",
    "min_bid_applications",
    "retail_offer_price",
    "retail_discount",
    "allotment_date",
    "allotment_date_src",
    "designated_exchange",
)
# the 1-lot row and the TOTAL that was checked against it
ONE_LOT_KEYS = (
    "min_bid_shares",
    "min_bid_applications",
    "min_bid_ratio_num",
    "min_bid_ratio_den",
    "min_bid_allotted_shares",
    "retail_valid_applications",
    "retail_shares_applied",
)


def _validated(b: dict, retail_sub: float | None) -> tuple[dict, bool, bool]:
    """Advert fields after one_lot_row_big_enough and allottees_plausible: a failing 1-lot
    row (with its TOTAL) or allottee count is set to None. Also returns both verdicts."""
    b = dict(b)
    row_ok = one_lot_row_big_enough(b, retail_sub)
    if not row_ok:
        b |= dict.fromkeys(ONE_LOT_KEYS)
    plausible = allottees_plausible(b)
    if not plausible:
        b["retail_allottees"] = None
    return b, row_ok, plausible


def _boa_fields(row: pd.Series, boa: BoaMap) -> dict:
    """Advert fields for one issue; an advert found under another ISIN is not used."""
    name, isin, readable, parsed = boa.get(row["issue_id"], (None, None, None, None))
    if name is not None and isin != row["isin"]:
        name, readable, parsed = None, None, None
    raw = parsed.as_dict() if parsed else {}
    exch = row.get("retail_sub_exch")
    sub = raw.get("retail_sub_boa") or (exch if pd.notna(exch) else None)
    b, row_ok, plausible = _validated(raw, sub)
    p, method, agree, p_dropped = _p_one_lot(b, sub)
    den = b.get("min_bid_ratio_den")
    return {
        "boa_file": name,
        "boa_readable": readable,
        "boa_parsed": parsed is not None,
        "p_1lot": p,
        "p_1lot_method": method,
        "p_agree": agree,
        "p_dropped": p_dropped,
        "allottees_plausible": plausible,
        "one_lot_row_ok": row_ok,
        "min_bid_ratio": f"{b['min_bid_ratio_num']}:{den}" if den else None,
    } | {k: b.get(k) for k in BOA_KEYS}


def _boa_checks(r: dict) -> list[str]:
    bad = []
    lot, first = r["lot_size_detail"], r["min_bid_shares"]
    if pd.notna(lot) and pd.notna(first) and lot != first:
        bad.append("lot_detail_vs_boa")
    if r["p_agree"] is False:
        bad.append("p_ratio_vs_allottees")
    if not r["one_lot_row_ok"]:
        bad.append("boa_one_lot_row_too_small")
    if r["p_dropped"]:
        bad.append("p_outside_subscription_bounds")
    if not r["allottees_plausible"]:
        bad.append("boa_allottees_implausible")
    if r["exch_snapshot_before_close"] is True:
        bad.append("exch_snapshot_before_close")  # its bids and times were dropped (ipo.py)
    if r["boa_file"] and not r["boa_readable"]:
        bad.append("boa_unreadable")
    elif r["boa_file"] and not r["boa_parsed"]:
        bad.append("boa_no_retail_section")
    elif r["boa_file"] and pd.isna(first):
        bad.append("boa_one_lot_row_missing")  # no table row with NSE's lot as its category
    return bad


def _price_checks(r: dict) -> list[str]:
    bad = []
    listed = r["status"] == "listed"
    if listed and r["issue_price_src"] != "nse_list=bhavcopy_base":
        bad.append("issue_price_list_vs_base")
    offer, price = r["retail_offer_price"], r["issue_price"]
    if pd.notna(offer) and pd.notna(price):
        # adverts quote either the offer price or the net retail price (LIC: 904 = 949 - 45)
        disc = r["retail_discount"] if pd.notna(r["retail_discount"]) else 0.0
        if min(abs(offer - price + d) for d in (0.0, disc)) > 0.005:
            bad.append("boa_price_vs_issue_price")
    ad, listing = r["allotment_date"], r["listing_date"]
    last = listing if pd.notna(listing) else ad
    if ad is not None and pd.notna(ad) and not r["issue_close"] <= ad <= last:
        bad.append("allotment_date_order")
    if listed:
        lo, hi = r["list_low"], r["list_high"]
        if (
            not lo
            <= min(r["list_open"], r["list_close"])
            <= max(r["list_open"], r["list_close"])
            <= hi
        ):
            bad.append("ohlc")
    return bad


def _checks(r: dict) -> str:
    """Semicolon-separated names of the cross-checks this row fails ('' if none)."""
    return ";".join(_boa_checks(r) + _price_checks(r))


def _derived(row: pd.Series, r: dict) -> dict:
    """Fields computed from one row's issue, listing and advert fields (r has
    issue_price already)."""
    lot = row["lot_size"] if pd.notna(row["lot_size"]) else r["min_bid_shares"]
    exch, boa_sub = row["retail_sub_exch"], r["retail_sub_boa"]
    price, shares = r["issue_price"], r["retail_shares_allotted"]

    def ret(col: str) -> float | None:
        return row[col] / price - 1 if price and pd.notna(row[col]) else None

    return {
        "lot_size_detail": row["lot_size"],
        "lot_size": lot,
        "lot_size_src": "nse_detail"
        if pd.notna(row["lot_size"])
        else ("boa_min_bid" if pd.notna(lot) else None),
        "lot_value_at_cap": lot * row["price_band_high"] if pd.notna(lot) else None,
        "retail_sub": boa_sub if pd.notna(boa_sub) else exch,
        "retail_sub_src": "nse_boa"
        if pd.notna(boa_sub)
        else ("nse_detail_bids" if pd.notna(exch) else None),
        "retail_lots_allotted": shares / lot if pd.notna(lot) and shares else None,
        "symbol": row["symbol"] if pd.notna(row["symbol"]) else row["list_symbol"],
        "listing_match": row["match_method"],
        "ret_open": ret("list_open"),
        "ret_close": ret("list_close"),
    }


def assemble(
    issues: pd.DataFrame,
    listings: pd.DataFrame,
    boa: BoaMap,
    last_session: date,
    exceptions: dict[str, str] | None = None,
) -> pd.DataFrame:
    """The clean table (CLEAN_COLS), one row per issue, sorted by open date.
    `exceptions` (load_exceptions) overrides the status of the issues it names."""
    exceptions = exceptions or {}
    df = issues.merge(listings, on="issue_id", how="left", validate="one_to_one")
    out = []
    for _, row in df.iterrows():
        r = row.to_dict() | _boa_fields(row, boa)
        r["status"] = _status(row, last_session, exceptions)
        r["issue_price"], r["issue_price_src"] = _issue_price(row)
        r |= _derived(row, r)
        r["checks"] = _checks(r)
        out.append(r)
    clean = pd.DataFrame(out)[CLEAN_COLS]
    return clean.sort_values(["issue_open", "issue_id"], ignore_index=True)
