"""Mainboard IPO dataset (phase 2, IPO track step 1): NSE list and JSON parsing, listing-day
matching against bhavcopies, and the basis-of-allotment advert parser, on synthetic input."""

from datetime import date

import pandas as pd
import pytest

from nsealgo.data.ipo import (
    issues_frame,
    list_row_kind,
    parse_issue_period,
    parse_lot,
    parse_nse_date,
    parse_price_range,
    parse_snapshot_date,
)
from nsealgo.data.ipo_listing import BHAV_COLS, first_seen, listings_frame


def test_nse_dates_in_every_format_seen():
    assert parse_nse_date("02-JAN-2025") == date(2025, 1, 2)
    assert parse_nse_date("09-Sept-2024") == date(2024, 9, 9)
    assert parse_nse_date("2024-09-16") == date(2024, 9, 16)
    assert parse_nse_date("-") is None and parse_nse_date(None) is None
    with pytest.raises(ValueError):
        parse_nse_date("09-Sepx-2024")


def test_price_band_lot_and_period():
    assert parse_price_range("Rs.204 to Rs.215 ") == (204, 215)
    assert parse_price_range("Rs. 300/- to Rs. 315/- ") == (300, 315)
    assert parse_price_range("Rs.1000") == (1000, 1000)
    assert parse_price_range("Rs. 1,585 to Rs. 1,665 per Equity Share") == (1585, 1665)
    assert parse_lot("108  Equity Shares and in multiples thereof") == 108
    assert parse_lot(None) is None
    assert parse_lot("Minimum 132 Equity shares and in multiples thereof") == 132
    assert parse_issue_period("09-Sept-2024 to 11-Sept-2024") == (
        date(2024, 9, 9),
        date(2024, 9, 11),
    )
    assert parse_issue_period('"08-May-2017, 09-May-2017 and 11-May-2017"') == (
        date(2017, 5, 8),
        date(2017, 5, 11),
    )
    assert parse_issue_period("19-Jan-2024 to 24-Jan-2024 (Excluding 22-Jan-2024)") == (
        date(2024, 1, 19),
        date(2024, 1, 24),
    )
    assert parse_issue_period('"September 29, 2020 to October 1, 2020"') == (
        date(2020, 9, 29),
        date(2020, 10, 1),
    )
    with pytest.raises(ValueError):
        parse_issue_period("11-Sep-2024 to 09-Sep-2024")


def _row(sym, name, start="09-MAR-2026", end="11-MAR-2026", sec="EQ", listing="19-MAR-2026"):
    return {
        "symbol": sym,
        "company": name,
        "ipoStartDate": start,
        "ipoEndDate": end,
        "securityType": sec,
        "issuePrice": "122",
        "priceRange": "Rs.116 to Rs.122",
        "listingDate": listing,
    }


def test_list_rows_that_are_not_ipos():
    assert list_row_kind(_row("YESBANK", "Yes Bank Limited - FPO")) == "fpo"
    assert list_row_kind(_row("ITI", "ITI Limited FPO - Issue Withdrawn")) == "fpo"
    assert list_row_kind(_row("RSL", "Rajputana Stainless Limited-Special Withdrawal Option")) == (
        "withdrawal_window"
    )
    assert list_row_kind(_row("ADANIENPP1", "Adani Enterprises Limited")) == "partly_paid"
    assert list_row_kind(_row("X", "X Limited", sec="DEBT")) == "not_equity"
    assert list_row_kind(_row("PKH", "PKH Ventures Limited - Issue Withdrawn")) == "withdrawn"
    assert list_row_kind(_row("RSL", "Rajputana Stainless Limited")) == "ipo"
    ncd = _row("RHFL", "Reliance Home Finance Limited", sec="BE") | {"htmSym": "rhflncd1"}
    assert list_row_kind(ncd) == "ncd"


def _detail(period, lot="40 Equity Shares and in multiples thereof", isin="INE000A01011"):
    return {
        "metaInfo": {"isin": isin, "listingDate": "2026-03-19"},
        "issueInfo": {
            "dataList": [
                {"title": "Issue Period", "value": period},
                {"title": "Bid Lot", "value": lot},
            ]
        },
        "activeCat": {
            "dataList": [
                {
                    "category": "Category",
                    "noOfShareOffered": "x",
                    "noOfSharesBid": "y",
                    "noOfTotalMeant": "z",
                },
                {
                    "category": "Retail Individual Investors(RIIs) ",
                    "noOfShareOffered": "1000",
                    "noOfSharesBid": "7040",
                    "noOfTotalMeant": "7.04",
                },
                {
                    "category": "Total",
                    "noOfShareOffered": "3000",
                    "noOfSharesBid": "60000",
                    "noOfTotalMeant": "20.0",
                },
            ]
        },
    }


def test_issues_frame_dedupes_keeps_withdrawn_twin_and_uses_matching_json_only():
    rows = [
        _row("RSL", "Rajputana Stainless Limited"),
        _row("RSL", "Rajputana Stainless Limited"),  # same row in two yearly lists
        _row("RSL", "Rajputana Stainless Limited-Special Withdrawal Option", start="12-MAR-2026"),
        _row("PKH", "PKH Ventures Limited - Issue Withdrawn", listing="-"),
        _row("PKH", "PKH Ventures Limited", listing="-"),
        _row("AWH", "Antony", start="21-DEC-2020", end="23-DEC-2020", listing="01-JAN-2021"),
    ]
    details = {
        "RSL": _detail("09-Mar-2026 to 11-Mar-2026"),
        "AWH": _detail("04-Mar-2020 to 16-Mar-2020"),
    }  # the earlier attempt's JSON
    df = issues_frame(rows, details).set_index("list_symbol")
    assert sorted(df.index) == ["AWH", "PKH", "RSL"]
    assert df.loc["PKH", "list_status"] == "withdrawn"
    rsl = df.loc["RSL"]
    assert rsl["detail_used"] and rsl["lot_size"] == 40 and rsl["retail_sub_exch"] == 7.04
    assert rsl["total_sub_exch"] == 20.0 and rsl["meta_isin"] == "INE000A01011"
    assert not df.loc["AWH", "detail_used"] and pd.isna(df.loc["AWH", "lot_size"])


def test_snapshot_stamps_in_every_format_seen():
    assert parse_snapshot_date("Updated as on 11-Sep-2024 19:00:00") == date(2024, 9, 11)
    assert parse_snapshot_date("Updated as on 09-Sept-2024 19:00:00") == date(2024, 9, 9)
    assert parse_snapshot_date("Updated as on 09th Dec 2021 at 1700 hrs") == date(2021, 12, 9)
    assert parse_snapshot_date("Updated as on 13th December 2021 at 1700 hrs") == date(2021, 12, 13)
    assert parse_snapshot_date("Updated as on 1st Nov 2021 at 1700 hrs") == date(2021, 11, 1)
    assert parse_snapshot_date("Updated as on null") is None
    assert parse_snapshot_date("") is None and parse_snapshot_date(None) is None
    with pytest.raises(ValueError):
        parse_snapshot_date("Updated as on sometime")


def test_exchange_bids_stamped_before_the_close_are_dropped():
    # ADANI WILMAR 2022: the JSON kept a day-1 12:27 snapshot of a 27-31 Jan book
    rows = [
        _row("EARLY", "Early Ltd", start="27-JAN-2022", end="31-JAN-2022"),
        _row("CLOSE", "Close Ltd", start="27-JAN-2022", end="31-JAN-2022"),
        _row("NULL", "Null Ltd", start="27-JAN-2022", end="31-JAN-2022"),
    ]

    def stamped(text):
        d = _detail("27-Jan-2022 to 31-Jan-2022")
        d["activeCat"]["updateTime"] = text
        return d

    details = {
        "EARLY": stamped("Updated as on 27-Jan-2022 12:27:00"),
        "CLOSE": stamped("Updated as on 31-Jan-2022 17:00:00"),
        "NULL": stamped("Updated as on null"),
    }
    df = issues_frame(rows, details).set_index("list_symbol")
    early = df.loc["EARLY"]
    assert early["exch_snapshot_before_close"]
    assert pd.isna(early["retail_sub_exch"]) and pd.isna(early["total_sub_exch"])
    assert pd.isna(early["retail_shares_bid_exch"])
    assert early["retail_shares_offered_exch"] == 1000  # the reserved size is kept
    for sym in ("CLOSE", "NULL"):
        assert not df.loc[sym, "exch_snapshot_before_close"]
        assert df.loc[sym, "retail_sub_exch"] == 7.04


def test_conflicting_list_rows_without_a_withdrawn_twin_fail():
    with pytest.raises(ValueError, match="conflicting"):
        issues_frame([_row("A", "A Ltd"), _row("A", "A Limited")], {})


def _bhav(day, rows):
    return pd.DataFrame([(day, *r) for r in rows], columns=BHAV_COLS)


def _issue(sym, open_, close, price, meta_isin=None):
    return {
        "issue_id": f"{sym}_{open_:%Y%m%d}",
        "list_symbol": sym,
        "issue_open": open_,
        "issue_close": close,
        "issue_price_list": price,
        "meta_isin": meta_isin,
    }


def test_listing_by_isin_symbol_base_price_and_already_listed():
    d0, d1, d2, d3 = date(2020, 3, 2), date(2020, 3, 20), date(2020, 3, 23), date(2020, 3, 24)
    days = [
        _bhav(d0, [("OLD", "EQ", "INE001", 10, 11, 9, 10, 10)]),
        _bhav(
            d1,
            [
                ("OLD", "EQ", "INE001", 10, 11, 9, 10, 10),
                ("NEWA", "EQ", "INE00A", 120, 130, 110, 125, 100),
            ],
        ),
        _bhav(
            d2,
            [
                ("NEWA", "EQ", "INE00A", 125, 126, 120, 121, 125),
                ("RENAMED", "BE", "INE00B", 55, 56, 50, 52, 50),
                ("NEWC", "EQ", "INE00C", 70, 71, 69, 70, 66),
            ],
        ),
        _bhav(d3, [("NEWA", "EQ", "INE00A", 121, 122, 119, 120, 121)]),
    ]
    new, sym_first = first_seen(days)
    assert list(new["isin"]) == ["INE001", "INE00A", "INE00B", "INE00C"]
    issues = pd.DataFrame(
        [
            _issue("NEWA", date(2020, 3, 10), date(2020, 3, 12), 100.0),
            _issue("NEWB", date(2020, 3, 11), date(2020, 3, 13), 50.0),  # listed as RENAMED
            _issue("NEWC", date(2020, 3, 11), date(2020, 3, 13), 66.0, meta_isin="INE00C"),
            _issue("OLD", date(2020, 3, 10), date(2020, 3, 12), 10.0),  # an unlabelled FPO
            _issue("GONE", date(2020, 3, 10), date(2020, 3, 12), 99.0),
        ]
    )
    out = listings_frame(issues, new, sym_first).set_index("issue_id")
    a = out.loc["NEWA_20200310"]
    assert (a["listing_date"], a["list_open"], a["list_close"], a["base_price"]) == (
        d1,
        120,
        125,
        100,
    )
    assert a["match_method"] == "symbol"
    b = out.loc["NEWB_20200311"]
    assert (b["symbol"], b["series"], b["match_method"]) == ("RENAMED", "BE", "base_price")
    assert out.loc["NEWC_20200311", "match_method"] == "isin"
    assert out.loc["OLD_20200310", "match_method"] == "already_listed"
    assert out.loc["GONE_20200310", "match_method"] == "not_found"


def test_isin_rule_respects_the_window_so_a_withdrawn_attempt_does_not_steal_it():
    d1 = date(2021, 1, 1)
    new, sym_first = first_seen([_bhav(d1, [("AWH", "EQ", "INE0AW", 436, 440, 400, 410, 315)])])
    issues = pd.DataFrame(
        [
            _issue("AWH", date(2020, 3, 4), date(2020, 3, 16), 300.0, meta_isin="INE0AW"),
            _issue("AWH", date(2020, 12, 21), date(2020, 12, 23), 315.0, meta_isin="INE0AW"),
        ]
    )
    out = listings_frame(issues, new, sym_first)
    assert list(out["match_method"]) == ["not_found", "isin"]


def test_issue_price_needs_the_listing_base_price_to_agree():
    from nsealgo.data.ipo_build import _issue_price

    row = {
        "issue_price_list": 70.0,
        "base_price": 70.0,
        "price_band_low": 66.0,
        "price_band_high": 70.0,
    }
    assert _issue_price(pd.Series(row)) == (70.0, "nse_list=bhavcopy_base")
    # list price corrupted by a later corporate action (seen for RADIOCITY, ANURAS)
    assert _issue_price(pd.Series(row | {"issue_price_list": 100.0})) == (
        70.0,
        "bhavcopy_base(list_disagrees)",
    )
    assert _issue_price(pd.Series(row | {"issue_price_list": 100.0, "base_price": 90.0}))[1] == (
        "conflict"
    )
    # base price off the issue price while the list price is in the band (AUBANK 2017)
    assert _issue_price(pd.Series(row | {"base_price": 150.0})) == (
        70.0,
        "nse_list(base_disagrees)",
    )


def test_repo_exception_file_loads_and_every_entry_is_sourced():
    from nsealgo.data.ipo_read import load_exceptions

    assert load_exceptions() == {"CAMS_20200921": "not_listed_on_nse_at_ipo"}


def test_sequential_and_concurrent_intervals():
    from nsealgo.data.ipo_stats import _overlapping, max_concurrent, max_sequential

    d = lambda day: date(2024, 1, day)  # noqa: E731
    ivs = [(d(1), d(5)), (d(5), d(8)), (d(6), d(9)), (d(10), d(12))]
    # d(5) is both an end and a start: funds released on day 5 are not reused that day
    assert max_sequential(ivs) == 3  # 1-5, 6-9, 10-12; 5-8 cannot follow 1-5
    assert max_sequential([(d(1), d(4)), (d(5), d(8))]) == 2
    assert max_concurrent(ivs) == 2 and max_concurrent([(d(1), d(3))] * 3) == 3
    assert _overlapping(ivs) == 3


def test_overlap_per_year_drops_lots_above_the_block_and_falls_back_to_listing():
    from nsealgo.data.ipo_stats import overlap_per_year

    base = {"status": "listed", "retail_discount": None, "lot_size": 100}
    df = pd.DataFrame(
        [
            base
            | {
                "issue_id": "A",
                "issue_open": date(2024, 1, 1),
                "issue_close": date(2024, 1, 3),
                "allotment_date": date(2024, 1, 4),
                "listing_date": date(2024, 1, 8),
                "price_band_high": 140.0,
            },
            base
            | {
                "issue_id": "B",
                "issue_open": date(2024, 1, 2),
                "issue_close": date(2024, 1, 5),
                "allotment_date": None,
                "listing_date": date(2024, 1, 10),
                "price_band_high": 150.0,
            },
            base
            | {
                "issue_id": "C",
                "issue_open": date(2024, 1, 2),
                "issue_close": date(2024, 1, 4),
                "allotment_date": date(2024, 1, 5),
                "listing_date": date(2024, 1, 9),
                "price_band_high": 151.0,
            },  # 15,100 > 15,000
        ]
    )
    row = overlap_per_year(df, 15_000).loc[2024]
    assert (row["listed"], row["lot_cost_above_block"], row["fit_block"]) == (3, 1, 2)
    assert row["end_is_listing_date"] == 1
    assert (row["overlap_full"], row["one_block_full"]) == (2, 1)
    # applying on the last day: A blocks 3-4 Jan, B 5-10 Jan, so one block takes both
    assert (row["overlap_last_day"], row["one_block_last_day"]) == (0, 2)


def test_retail_times_is_bid_over_offered_when_the_json_omits_it():
    from nsealgo.data.ipo import category_bids

    detail = {
        "activeCat": {
            "dataList": [
                {
                    "category": "Retail Individual Investors(RIIs) ",
                    "noOfShareOffered": "69380826",
                    "noOfSharesBid": "97372260",
                    "noOfTotalMeant": None,
                }
            ]
        }
    }
    _, _, times = category_bids(detail, "Retail Individual")
    assert times == pytest.approx(97372260 / 69380826)


def test_ipo_rows_lost_from_the_equity_list_are_recovered_from_the_unfiltered_list():
    from nsealgo.data.ipo import overwritten_ipo_rows

    ntpc = {
        "company": "NTPC Green Energy Limited",
        "htmSym": "ntpcgreen",
        "ipoStartDate": "19-NOV-2024",
        "ipoEndDate": "22-NOV-2024",
        "issuePrice": "######",
        "listingDate": "13-JUL-2026",
        "priceRange": "Rs.102 to Rs.108",
        "securityType": "N0",
        "symbol": "727NGEL36",
    }
    reit = ntpc | {
        "company": "Knowledge Realty Trust",
        "htmSym": "krt",
        "securityType": "RR",
        "symbol": "KRT",
        "priceRange": "Rs.95 to Rs.100",
    }
    ncd = ntpc | {"htmSym": "aelncd2", "priceRange": "Rs.1000", "symbol": "ADANIENPP1"}
    sme = ntpc | {"securityType": "SME", "symbol": "SMEX", "htmSym": "smex"}
    listed = _row("RSL", "Rajputana Stainless Limited")
    out = overwritten_ipo_rows([ntpc, ntpc, reit, ncd, sme, listed], [listed])
    assert len(out) == 1
    r = out[0]
    assert (r["symbol"], r["securityType"], r["listingDate"], r["issuePrice"]) == (
        "NTPCGREEN",
        "EQ",
        "-",
        "-",
    )
    assert r["overwritten"] and r["priceRange"] == "Rs.102 to Rs.108"
    df = issues_frame(out, {})
    assert df.loc[0, "list_row_overwritten"] and df.loc[0, "issue_id"] == "NTPCGREEN_20241119"
