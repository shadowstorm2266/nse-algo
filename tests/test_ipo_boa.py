"""Basis-of-allotment adverts (IPO track step 1): the retail-section parser on synthetic
advert text, and the build's 1-lot chance rules and advert sanity checks."""

from datetime import date

import pandas as pd
import pytest

from nsealgo.data.ipo import parse_long_date
from nsealgo.data.ipo_boa import parse_retail_boa, parse_row

TABLE = """\
A. Allotment to Retail Individual Bidders (after rejections) (including ASBA Applications)
Category  No. of Applications  % of Total  Total No. of Shares  % to Total  Allotted  Ratio  Total
   1    214    4,738,356    80.78    1,014,008,184    45.92    214    496:2125    236,676,404
   2    428      470,811     8.03      201,507,108     9.12    214    197:844      23,512,128
             1 ADDITIONAL SHARE FOR CATEGORY 428    1    52 : 99
   TOTAL         5,865,849   100.00    2,208,417,298   100.00
B. Allotment to Non-Institutional Bidders
   1   2,996        100    50.00       299,600    50.00    2,996     1:1     299,600
"""


PROSE = """\
The Basis of Allotment was finalized in consultation with the Designated Stock Exchange,
being NSE on September 13, 2024.
A. Allotment to Retail Individual Bidders (after rejections) (including ASBA Applications)
The Basis of Allotment to the Retail Individual Bidders, who have bid at the Cut-Off Price
or at the Offer Price of Rs 70 per Equity Share (Retail Discount of Rs 2 per Equity Share),
was finalized in consultation with the NSE. This category has been subscribed to the extent
of 7.53726 times. The total number of Equity Shares Allotted in Retail Portion is
293,000,000 Equity Shares to 1,369,158 successful Retail Individual Bidders.
B. Allotment to Non-Institutional Bidders
This category has been subscribed to the extent of 41.5 times.
"""


def test_retail_boa_fields_from_a_synthetic_advert():
    r = parse_retail_boa(PROSE, TABLE)
    assert r is not None
    assert r.retail_sub_boa == pytest.approx(7.53726)
    assert (r.retail_shares_allotted, r.retail_allottees) == (293_000_000, 1_369_158)
    assert r.retail_valid_applications == 5_865_849
    assert (r.min_bid_shares, r.min_bid_applications) == (214, 4_738_356)
    assert (r.min_bid_ratio_num, r.min_bid_ratio_den, r.min_bid_allotted_shares) == (496, 2125, 214)
    assert (r.retail_offer_price, r.retail_discount) == (70.0, 2.0)
    assert (r.allotment_date, r.designated_exchange) == (date(2024, 9, 13), "NSE")


def test_row_parser_needs_the_product_identity_and_percent_cells():
    assert parse_row(
        "   1    20    18,97,063   84.71   3,79,41,260   49.87   20   1:1  3,79,41,260"
    )
    assert parse_row("on July 1, 2025 the Company allotted 2025 shares") is None
    assert parse_row("   1    20    18,97,063   84.71   3,79,41,261   49.87   20   1:1") is None
    assert parse_retail_boa("no retail section here", "") is None


def test_long_dates():
    assert parse_long_date("September 14, 2020") == date(2020, 9, 14)
    assert parse_long_date("10th October, 2019") == date(2019, 10, 10)
    assert parse_long_date("Thursday, July, 22, 2021") == date(2021, 7, 22)
    assert parse_long_date("May 04, 2022") == date(2022, 5, 4)
    assert parse_long_date("sometime in 2022") is None
    assert parse_long_date("Decided on 4, 2022") is None  # no month name, only a prefix


def test_boa_probe_dates_start_the_day_before_listing_and_stay_after_the_close():
    from nsealgo.data.ipo_boa import boa_probe_dates

    close, listing = date(2024, 9, 11), date(2024, 9, 16)
    days = boa_probe_dates(close, listing)
    assert days[:4] == [date(2024, 9, 15), date(2024, 9, 14), date(2024, 9, 13), listing]
    assert days[4:] == [date(2024, 9, 12), date(2024, 9, 17)]
    assert len(days) == len(set(days)) and min(days) > close


def test_one_lot_chance_prefers_the_ratio_and_checks_the_lottery_identity():
    from nsealgo.data.ipo_build import _p_one_lot

    b = {
        "min_bid_ratio_num": 496,
        "min_bid_ratio_den": 2125,
        "min_bid_allotted_shares": 214,
        "min_bid_shares": 214,
        "retail_allottees": 1_369_158,
        "retail_valid_applications": 5_865_849,
    }
    p, method, agree, dropped = _p_one_lot(b, 7.54)
    assert p == pytest.approx(496 / 2125) and method == "min_bid_ratio" and agree and not dropped
    # the ratio row allots more than one lot: not a 1-lot chance, fall back to the identity
    p, method, _, _ = _p_one_lot(b | {"min_bid_allotted_shares": 428})
    assert method == "allottees_over_applications" and p == pytest.approx(1_369_158 / 5_865_849)
    assert _p_one_lot(b | {"retail_allottees": 2_000_000})[2] is False
    assert _p_one_lot({}) == (None, None, None, False)
    # DEEDEV 2024: a 53:92 ratio at 24.9x is another table's row; nothing else to use
    p, method, _, dropped = _p_one_lot(
        {
            "min_bid_ratio_num": 53,
            "min_bid_ratio_den": 92,
            "min_bid_allotted_shares": 73,
            "min_bid_shares": 73,
        },
        24.89,
    )
    assert (p, method, dropped) == (None, None, True)
    # INDOFARM 2024: the ratio is out of bounds at 102.6x, the identity is not
    p, method, _, dropped = _p_one_lot(
        b
        | {
            "min_bid_ratio_num": 5,
            "min_bid_ratio_den": 37,
            "retail_allottees": 61_370,
            "retail_valid_applications": 4_580_440,
        },
        102.57,
    )
    assert method == "allottees_over_applications" and dropped
    assert p == pytest.approx(61_370 / 4_580_440)


def test_p_bounds():
    from nsealgo.data.ipo_build import p_bounds

    assert p_bounds(None) == (0.0, 1.0)
    assert p_bounds(0.44) == (1.0, 1.0)  # undersubscribed: every valid application is allotted
    lo, hi = p_bounds(60.3)
    assert lo == pytest.approx(0.9 / 60.3) and hi == pytest.approx(6 / 60.3)


def test_an_advert_found_under_another_isin_is_not_used():
    from nsealgo.data.ipo_build import _boa_fields

    parsed = parse_retail_boa(PROSE, TABLE)
    boa = {"X_20240909": ("ADV_INE111_13SEP2024.pdf", "INE111", True, parsed)}
    row = pd.Series({"issue_id": "X_20240909", "isin": "INE111"})
    assert _boa_fields(row, boa)["retail_allottees"] == 1_369_158
    moved = _boa_fields(row.copy().replace({"INE111": "INE222"}), boa)
    assert moved["boa_file"] is None and moved["retail_allottees"] is None


def test_allottee_sentence_with_a_spillover_note_and_total_row_must_fit_the_rows():
    prose = PROSE.replace(
        "293,000,000 Equity Shares to 1,369,158 successful",
        "293,000,000 Equity Shares (includes under subscribed portion of 29,022 Equity Shares "
        "spilled over from Employee Category) to 1,369,158successful",
    )
    # a TOTAL line of another table first: too few applications for the 1-lot row
    table = TABLE.replace("   TOTAL ", "   TOTAL  2,671   100.00   9,000\n   TOTAL ", 1)
    r = parse_retail_boa(prose, table)
    assert r.retail_allottees == 1_369_158 and r.retail_valid_applications == 5_865_849


def test_unreadable_text_is_detected():
    from nsealgo.data.ipo_boa import text_is_readable

    assert text_is_readable(PROSE * 10)
    assert not text_is_readable("\x0c")  # a scan: no text layer
    assert not text_is_readable("\ufffd" * 2000 + "a" * 600)  # font without a char map


def test_one_lot_row_is_the_largest_of_the_smallest_category():
    from nsealgo.data.ipo_boa import BoaRow, one_lot_row

    employee = BoaRow(37, 164, 37 * 164, 37, 1, 1)
    retail = BoaRow(37, 460_611, 37 * 460_611, 37, 47, 155)
    two_lots = BoaRow(74, 22_989, 74 * 22_989, 37, 47, 155)
    assert one_lot_row([employee, retail, two_lots]) is retail
    assert one_lot_row([]) is None


def test_a_ratio_above_one_is_not_a_draw_ratio():
    row = parse_row(
        "   1   30   41,15,879   78.99   12,34,76,370   41.79   30   59:24   1,48,76,970"
    )
    assert row is not None and row.ratio_num is None and row.ratio_den is None


def test_allottee_count_that_the_shares_cannot_cover_is_rejected():
    from nsealgo.data.ipo_build import allottees_plausible

    # NOVAAGRI 2024: 1,22,76,493 shares at 365 a lot cover at most 33,634 allottees
    b = {
        "retail_allottees": 2_059_808,
        "retail_valid_applications": 2_059_808,
        "retail_shares_allotted": 12_276_493,
        "min_bid_shares": 365,
    }
    assert not allottees_plausible(b)
    assert allottees_plausible(b | {"retail_allottees": 33_630})
    assert not allottees_plausible(b | {"retail_allottees": 3_000_000, "min_bid_shares": None})
    assert allottees_plausible({})


def test_nse_lot_picks_the_one_lot_row_and_share_counts_tolerate_a_dot_typo():
    from nsealgo.data.ipo_boa import BoaRow, _share_count, one_lot_row

    stray = BoaRow(20, 900, 20 * 900, 20, 1, 1)  # another table's smaller category
    retail = BoaRow(126, 86_676, 126 * 86_676, 126, 67, 924)
    assert one_lot_row([stray, retail]) is stray
    assert one_lot_row([stray, retail], lot=126) is retail
    assert one_lot_row([stray], lot=126) is None
    assert _share_count("5,31,14,865") == 53_114_865
    assert _share_count("616.107") == 616_107  # Affle 2019 advert
    assert _share_count("616.1") is None


def test_a_one_lot_row_far_too_small_for_the_book_is_rejected():
    from nsealgo.data.ipo_build import one_lot_row_big_enough

    # SMARTWORKS 2025: 65 applications x 36 shares against 49.8 lakh shares at 3.58x
    b = {"min_bid_applications": 65, "min_bid_shares": 36, "retail_shares_allotted": 4_981_433}
    assert not one_lot_row_big_enough(b, 3.58)
    # undersubscribed (CANHLIFE 2025): 3,677 x 140 against 3.27 crore shares allotted in full
    canara = {
        "min_bid_applications": 3677,
        "min_bid_shares": 140,
        "retail_shares_allotted": 32_739_280,
    }
    assert not one_lot_row_big_enough(canara, 0.396)
    real = b | {"min_bid_applications": 300_000}  # 300,000 x 36 = 61% of 1.78 crore applied
    assert one_lot_row_big_enough(real, 3.58)
    assert one_lot_row_big_enough({}, 3.58)


def test_allotment_date_falls_back_to_the_taken_on_record_sentence():
    prose = PROSE.replace(
        "The Basis of Allotment was finalized in consultation with the Designated Stock Exchange,\n"
        "being NSE on September 13, 2024.",
        "The IPO Committee of our Company at its meeting held on September 03, 2026 has taken on "
        "record the Basis of Allotment of Equity Shares approved by the Designated Stock "
        "Exchange, being BSE and has allotted the Equity Shares to various successful Bidders.",
    )
    r = parse_retail_boa(prose, TABLE)
    assert (r.allotment_date, r.allotment_date_src, r.designated_exchange) == (
        date(2026, 9, 3),
        "taken_on_record",
        "BSE",
    )
    r = parse_retail_boa(
        PROSE.replace("Allotment was", "Allotment (except Anchor Investors) was"), TABLE
    )
    assert (r.allotment_date, r.allotment_date_src) == (date(2024, 9, 13), "finalized")


def test_an_undersubscribed_retail_book_gives_a_one_lot_chance_of_one():
    from nsealgo.data.ipo_build import _p_one_lot

    assert _p_one_lot({"retail_sub_boa": 0.396}, 0.396) == (
        1.0,
        "retail_undersubscribed",
        None,
        False,
    )
    assert _p_one_lot({"retail_sub_boa": 1.2}, 1.2)[0] is None
    assert _p_one_lot({}, 0.5)[0] is None  # exchange bid book only: no advert, no chance
