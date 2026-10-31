"""IPO v1 rules (research/ipo_strategy_plan.md): universe and exclusions, k and the
estimated 1-lot chance, blocking and release days, the blocked amount, and a hand-worked
net P&L through costs.py, on synthetic issues."""

from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import pytest
import yaml

from nsealgo.costs import load_cost_config, load_ipo_costs
from nsealgo.engine.ipo_sim import TradingDays
from nsealgo.settings import REPO_ROOT
from nsealgo.strategies.ipo_v1 import (
    IpoV1Config,
    allotted_pnl,
    issue_terms,
    k_by_year,
    one_lot_chance,
    select_universe,
)

with (REPO_ROOT / "config" / "strategies" / "ipo_v1.yaml").open(encoding="utf-8") as fh:
    CFG = IpoV1Config.model_validate(yaml.safe_load(fh))
COSTS = load_cost_config(REPO_ROOT / "config" / "costs.yaml")
IPO_COSTS = load_ipo_costs(REPO_ROOT / "config" / "costs.yaml")


def issue(issue_id: str, close: date, **kw) -> dict:
    row = {
        "issue_id": issue_id,
        "status": "listed",
        "issue_open": close - timedelta(days=2),
        "issue_close": close,
        "lot_size": 100.0,
        "price_band_high": 100.0,
        "issue_price": 100.0,
        "retail_discount": float("nan"),
        "p_1lot": 0.25,
        "retail_sub_exch": 4.0,
        "retail_shares_applied": None,
        "retail_valid_applications": None,
        "allotment_date": close + timedelta(days=1),
        "listing_date": close + timedelta(days=3),
        "list_open": 120.0,
        "list_close": 110.0,
    }
    return row | kw


def frame(*rows: dict) -> pd.DataFrame:
    return pd.DataFrame(list(rows))


def test_repo_config_holds_the_owners_parameters():
    assert CFG.capital_rupees == 20_000 and CFG.lots_per_application == 1
    assert (CFG.bid_close_from, CFG.bid_close_to) == (date(2019, 1, 1), date(2026, 10, 31))
    assert (CFG.monte_carlo.runs, CFG.monte_carlo.seed) == (10_000, 20261101)
    assert CFG.release.not_allotted_days_after_allotment == 1
    assert CFG.release.allotted_days_after_listing == 2
    slip = {k: float(v) for k, v in IPO_COSTS.listing_slippage_pct.items()}
    assert slip == {"none": 0.0, "base": 0.25, "stress1": 0.5, "stress2": 1.0}


def test_universe_keeps_listed_and_withdrawn_in_the_window_and_names_every_exclusion():
    d = date(2024, 3, 6)
    df = frame(
        issue("OK_1", d),
        issue("GONE_1", d, status="withdrawn", p_1lot=None),
        issue("CAMS_20200921", d, status="not_listed_on_nse_at_ipo"),
        issue("NEW_1", d, status="pending"),
        issue("NOLOT_1", d, lot_size=float("nan")),
        issue("NOP_1", d, p_1lot=None, retail_sub_exch=float("nan")),
        issue("EST_1", d, p_1lot=None),  # estimable from the exchange multiple
        issue("OLD_1", date(2018, 12, 31)),
        issue("LATE_1", date(2026, 11, 2)),
    )
    choices, excluded = select_universe(df, CFG)
    assert sorted(choices["issue_id"]) == ["EST_1", "GONE_1", "OK_1"]
    why = excluded.set_index("issue_id")["reason"]
    assert set(why.index) == {"CAMS_20200921", "NEW_1", "NOLOT_1", "NOP_1"}
    assert why["CAMS_20200921"].startswith("status not_listed_on_nse_at_ipo: BSE-only")
    assert why["NEW_1"] == "status pending"
    assert why["NOLOT_1"] == "data gap: no lot"
    assert why["NOP_1"] == "data gap: no 1-lot chance and no exchange multiple"


def test_k_is_the_years_median_lots_per_application_and_p_is_capped_at_one():
    d = date(2024, 3, 6)
    parsed = [
        issue(f"P{i}", d, retail_shares_applied=apps * lots * 100, retail_valid_applications=apps)
        for i, (apps, lots) in enumerate([(1000, 1.2), (500, 1.5), (800, 2.0)])
    ]
    other = issue("Q", date(2023, 5, 5), retail_shares_applied=900, retail_valid_applications=3)
    df = frame(*parsed, other)
    k = k_by_year(df)
    assert k[2024] == pytest.approx(1.5) and k[2023] == pytest.approx(3.0)
    est = frame(
        issue("E1", d, p_1lot=None, retail_sub_exch=6.0),
        issue("E2", d, p_1lot=None, retail_sub_exch=0.9),
        issue("W", d, status="withdrawn", p_1lot=None),
        issue("P", d, p_1lot=0.4),
    )
    p, estimated = one_lot_chance(est, k)
    assert p.tolist() == pytest.approx([0.25, 1.0, 0.0, 0.4])
    assert estimated.tolist() == [True, True, False, False]


def _days(start: date, n: int, holidays: set[date] = frozenset()) -> TradingDays:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5 and d not in holidays:
            out.append(d)
        d += timedelta(days=1)
    return TradingDays(out)


def test_release_days_follow_the_blocking_rule_in_trading_days():
    close = date(2024, 3, 6)  # Wed; Fri 8 Mar is a holiday
    days = _days(date(2024, 3, 1), 30, {date(2024, 3, 8)})
    row = issue("A", close, allotment_date=date(2024, 3, 7), listing_date=date(2024, 3, 12))
    t = issue_terms(frame(row), days, CFG).iloc[0]
    # not allotted: allotment +1 = Mon 11; free from Tue 12
    assert (t["release_not"], t["free_not"]) == (date(2024, 3, 11), date(2024, 3, 12))
    # allotted: listing (Tue 12) +2 = Thu 14; free from Fri 15
    assert (t["release_allot"], t["free_allot"]) == (date(2024, 3, 14), date(2024, 3, 15))
    assert not t["allotment_date_estimated"]
    assert t["block_paise"] == 1_000_000 and t["app_date"] == close


def test_a_missing_allotment_date_is_the_trading_day_before_listing():
    days = _days(date(2024, 3, 1), 30)
    row = issue("A", date(2024, 3, 6), allotment_date=None, listing_date=date(2024, 3, 11))
    t = issue_terms(frame(row), days, CFG).iloc[0]
    assert t["allotment_date_used"] == date(2024, 3, 8) and t["allotment_date_estimated"]
    assert t["release_not"] == date(2024, 3, 11)


def test_a_withdrawn_issue_is_released_after_its_last_bid_day():
    days = _days(date(2024, 3, 1), 30)
    row = issue("W", date(2024, 3, 6), status="withdrawn", listing_date=None, allotment_date=None)
    t = issue_terms(frame(row), days, CFG).iloc[0]
    assert t["release_not"] == date(2024, 3, 6) and t["free_not"] == date(2024, 3, 7)


def test_the_block_is_the_band_top_less_the_retail_discount():
    days = _days(date(2024, 3, 1), 30)
    row = issue("L", date(2024, 3, 6), lot_size=15.0, price_band_high=949.0, retail_discount=45.0)
    assert issue_terms(frame(row), days, CFG).iloc[0]["block_paise"] == 15 * 904 * 100


def test_hand_worked_net_pnl_of_an_allotted_application():
    # lot 100 at Rs 100, open Rs 120, base slippage 0.25%: sale 11,970.00
    # STT 11.97; transaction 0.355509 -> 0.36; SEBI 0.01197 -> 0.01; DP 9.00;
    # GST 18% x 9.367479 = 1.686146 -> 1.69; charges 23.03 -> P&L 1,946.97
    row = pd.Series(issue("A", date(2024, 3, 6)))
    slip = IPO_COSTS.listing_slippage_pct["base"]
    assert allotted_pnl(row, "list_open", slip, date(2024, 3, 7), COSTS, IPO_COSTS) == 194_697
    # before 1 Jul 2020 the allotment pays 0.015% stamp duty on Rs 10,000: 1.50
    assert allotted_pnl(row, "list_open", slip, date(2020, 6, 30), COSTS, IPO_COSTS) == 194_547
    # a retail discount lowers the price paid; the sale side is unchanged
    disc = pd.Series(issue("B", date(2024, 3, 6), retail_discount=2.0))
    assert allotted_pnl(disc, "list_open", slip, date(2024, 3, 7), COSTS, IPO_COSTS) == 214_697
    # the listing-day close as the sale price, no slippage: sale 11,000.00; STT 11.00,
    # transaction 0.3267 -> 0.33, SEBI 0.01, DP 9.00, GST 18% x 9.3377 -> 1.68: 22.02
    close = allotted_pnl(row, "list_close", Decimal(0), date(2024, 3, 7), COSTS, IPO_COSTS)
    assert close == 100_000 - 2_202
