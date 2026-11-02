"""Live IPO recorder (IPO track step 3, data only): parsing of NSE's current-issue rows and
per-issue JSON, file naming, append-only writes, and listing rows. Shapes copied from
NSE's responses of 2026-11-02 (BCSSL, the SME rows of the same list)."""

import json
from datetime import UTC, date, datetime

import pandas as pd
import pytest

from nsealgo.data.calendar import IST
from nsealgo.data.ipo_boa import advert_name
from nsealgo.data.ipo_live import (
    book_summary,
    current_issue_kind,
    detail_matches,
    file_stamp,
    issue_id,
    listing_name,
    listing_row,
    open_mainboard,
    parse_issue_id,
    parse_snapshot_name,
    parse_stamp,
    scan_issue_dir,
    snapshot_name,
    write_new,
)
from tests.ipo_live_helpers import current_rows, detail

# --- current-issue rows -------------------------------------------------------------------


def test_only_eq_series_rows_are_mainboard():
    rows = current_rows()
    assert current_issue_kind(rows[0]) == "mainboard"
    assert current_issue_kind(rows[1]) == "sme"
    assert current_issue_kind(rows[0] | {"series": "N1"}) == "not_equity"
    assert current_issue_kind(rows[0] | {"series": None}) == "not_equity"
    fpo = rows[0] | {"companyName": "Example Limited - FPO"}
    assert current_issue_kind(fpo) == "fpo"
    assert current_issue_kind(rows[0] | {"symbol": "BCSSLPP1"}) == "partly_paid"


def test_open_mainboard_keeps_rows_whose_bid_dates_contain_today():
    issues, other = open_mainboard(current_rows(), date(2026, 11, 2))
    assert [(i.issue_id, i.issue_open, i.issue_close) for i in issues] == [
        ("BCSSL_20261029", date(2026, 10, 29), date(2026, 11, 2))
    ]
    assert other == [{"symbol": "VPFL", "series": "SME", "status": "Active", "reason": "sme"}]
    issues, other = open_mainboard(current_rows(), date(2026, 11, 3))
    assert issues == [] and other[0]["reason"] == "not_open"


def test_unreadable_mainboard_rows_are_reported_not_dropped():
    bad = [
        current_rows()[0] | {"issueEndDate": "-"},
        current_rows()[0] | {"symbol": "../ETC"},
        current_rows()[0] | {"issueStartDate": "05-Nov-2026"},  # ends before it starts
    ]
    issues, other = open_mainboard(bad, date(2026, 11, 2))
    assert issues == []
    assert [o["reason"].split(":")[0] for o in other] == ["bad_row"] * 3


# --- per-issue JSON -----------------------------------------------------------------------


def test_parse_stamp_reads_the_live_format():
    assert parse_stamp("Updated as on 02-Nov-2026 11:24:00") == datetime(
        2026, 11, 2, 11, 24, tzinfo=IST
    )
    assert parse_stamp("Updated as on 2-Nov-2026 19:00") == datetime(2026, 11, 2, 19, tzinfo=IST)
    for empty in ("Updated as on null", "", None):
        assert parse_stamp(empty) is None
    with pytest.raises(ValueError):
        parse_stamp("Updated as on 09th Dec 2021 at 1700 hrs")


def test_book_summary_takes_retail_and_total_from_the_consolidated_book():
    s = book_summary(detail())
    assert s["stamp"] == "2026-11-02T11:24:00+05:30" and not s["stamp_unreadable"]
    assert (s["bid_open"], s["bid_close"], s["lot"]) == ("2026-10-29", "2026-11-02", 182)
    assert s["retail"] == [8214097.0, 73582418.0, 8.958065384423875]
    assert s["total"] == [16533012.0, 177421972.0, 10.731376230779968]
    assert s["isin"] is None
    odd = book_summary(detail(stamp="Updated as on sometime"))
    assert odd["stamp"] is None and odd["stamp_unreadable"]
    assert odd["stamp_raw"] == "Updated as on sometime"


def test_detail_matches_only_this_bid_period():
    assert detail_matches(detail(), date(2026, 10, 29))
    assert not detail_matches(detail(), date(2026, 10, 30))
    assert not detail_matches(detail(period=""), date(2026, 10, 29))
    assert not detail_matches(detail(period="soon"), date(2026, 10, 29))


# --- file naming --------------------------------------------------------------------------


def test_snapshot_names_are_the_ist_fetch_time():
    at = datetime(2026, 11, 2, 12, 0, 4, tzinfo=IST)
    assert file_stamp(at) == "20261102T120004+0530"
    assert snapshot_name(at) == "20261102T120004+0530.json"
    assert snapshot_name(at, final=True) == "final_20261102T120004+0530.json"
    assert snapshot_name(datetime(2026, 11, 2, 6, 30, 4, tzinfo=UTC)) == snapshot_name(at)
    with pytest.raises(ValueError):
        snapshot_name(datetime(2026, 11, 2, 12, 0, 4))  # noqa: DTZ001 - naive on purpose


def test_snapshot_names_parse_back():
    at = datetime(2026, 11, 2, 19, 30, 1, tzinfo=IST)
    assert parse_snapshot_name(snapshot_name(at)) == (False, at)
    assert parse_snapshot_name(snapshot_name(at, final=True)) == (True, at)
    for other in ("listing_20261105.json", "ADV_X_05NOV2026.pdf", "20261102T193001.json"):
        assert parse_snapshot_name(other) is None


def test_issue_ids_and_other_names():
    assert issue_id("BCSSL", date(2026, 10, 29)) == "BCSSL_20261029"
    assert issue_id("M&M-X1", date(2026, 1, 5)) == "M&M-X1_20260105"
    assert parse_issue_id("BCSSL_20261029") == ("BCSSL", date(2026, 10, 29))
    for bad in ("current_issue", "bhavcopy", "BCSSL", "run_log.jsonl"):
        assert parse_issue_id(bad) is None
    for bad_symbol in ("../ETC", "bcssl", "", "A B"):
        with pytest.raises(ValueError):
            issue_id(bad_symbol, date(2026, 10, 29))
    assert listing_name(date(2026, 11, 5)) == "listing_20261105.json"
    assert advert_name("INE0ABC01011", date(2026, 11, 4)) == "ADV_INE0ABC01011_04NOV2026.pdf"


def test_write_new_never_overwrites(tmp_path):
    path = tmp_path / "BCSSL_20261029" / "20261102T120004+0530.json"
    write_new(path, b"first")
    with pytest.raises(FileExistsError):
        write_new(path, b"second")
    assert path.read_bytes() == b"first"


# --- listing rows and the issue directory -------------------------------------------------


def bhav(rows: list[tuple[str, str, str, float]], day: date = date(2026, 11, 5)) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "session_date": day,
                "symbol": sym,
                "series": series,
                "isin": isin,
                "open": price,
                "high": price + 5,
                "low": price - 5,
                "close": price + 1,
                "prev_close": 82.0,
            }
            for sym, series, isin, price in rows
        ]
    )


def test_listing_row_by_isin_then_symbol():
    df = bhav([("BCSSL", "EQ", "INE0BC001010", 96.0), ("OTHER", "EQ", "INE0OT001010", 10.0)])
    row = listing_row(df, "BCSSL", "INE0BC001010")
    assert row is not None
    assert (row["match"], row["open"], row["close"], row["prev_close"]) == ("isin", 96, 97, 82)
    assert row["session_date"] == "2026-11-05"
    assert listing_row(df, "BCSSL", None)["match"] == "symbol"
    assert listing_row(df, "BCSSL", "INE0XX000000")["match"] == "symbol"
    assert listing_row(df, "NEWCO", None) is None
    assert listing_row(bhav([("BCSSL", "BL", "INE0BC001010", 96.0)]), "BCSSL", None) is None
    dup = bhav([("BCSSL", "EQ", "INE0BC001010", 96.0), ("BCSSL", "BE", "INE0BC001010", 96.0)])
    with pytest.raises(ValueError):
        listing_row(dup, "BCSSL", None)


def test_scan_issue_dir_reads_what_is_on_disk(tmp_path):
    d = tmp_path / "BCSSL_20261029"
    d.mkdir()
    (d / "20261029T120004+0530.json").write_text(
        json.dumps(detail(period="29-Oct-2026 to 31-Oct-2026"))
    )
    (d / "20261102T193002+0530.json").write_text(json.dumps(detail()))
    (d / "final_20261103T120003+0530.json").write_text(json.dumps(detail(isin="INE0BC001010")))
    (d / "listing_20261105.json").write_text(json.dumps({"listing_date": "2026-11-05"}))
    t = scan_issue_dir(d)
    assert t is not None
    assert (t.symbol, t.issue_open, t.issue_close) == (
        "BCSSL",
        date(2026, 10, 29),
        date(2026, 11, 2),
    )
    assert (t.snapshots, t.final, t.lot, t.isin, t.band) == (2, True, 182, "INE0BC001010", (78, 82))
    assert t.listing == {"listing_date": "2026-11-05"} and t.advert is None
    assert scan_issue_dir(tmp_path / "bhavcopy") is None


def test_scan_ignores_another_attempts_json(tmp_path):
    d = tmp_path / "BCSSL_20261029"
    d.mkdir()
    (d / "20261029T120004+0530.json").write_text(json.dumps(detail()))
    (d / "20261229T120004+0530.json").write_text(
        json.dumps(detail(period="29-Dec-2026 to 31-Dec-2026"))
    )
    t = scan_issue_dir(d)
    assert t is not None and t.issue_close == date(2026, 11, 2)
