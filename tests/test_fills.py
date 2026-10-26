from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from nsealgo.brokers.fills import Bar, bracket_exit, first_leg, limit_ref, slip, stop_ref
from nsealgo.data.calendar import IST
from nsealgo.engine.types import ExitReason, Order, OrderRole, OrderType, Product, Side

D = Decimal
TS = pd.Timestamp("2024-01-02 10:00", tz=IST)


def bar(o: float, h: float, low: float, c: float) -> Bar:
    return Bar("X", TS, date(2024, 1, 2), o, h, low, c)


def test_slippage_is_against_us():
    assert slip(D(500), Side.BUY, D(3)) == D("500.15")
    assert slip(D(510), Side.SELL, D(3)) == D("509.847")
    assert slip(D(510), Side.SELL, D(0)) == D(510)


def test_sell_stop_fills_at_stop_when_bar_trades_through_it():
    assert stop_ref(Side.SELL, D(95), bar(97, 98, 94, 96)) == D(95)


def test_sell_stop_touch_triggers_and_miss_does_not():
    assert stop_ref(Side.SELL, D(95), bar(97, 98, 95, 96)) == D(95)
    assert stop_ref(Side.SELL, D(95), bar(97, 98, 95.01, 96)) is None


def test_gap_through_stop_fills_at_open():
    # Long stopped out: the bar opens below the stop, so the fill is the open, not the stop.
    assert stop_ref(Side.SELL, D(95), bar(93, 94, 92, 93.5)) == D(93)
    # Short (buy stop) gapping up.
    assert stop_ref(Side.BUY, D(105), bar(106, 107, 105.5, 106)) == D(106)


def test_limit_needs_trade_through_not_touch():
    assert limit_ref(Side.BUY, D(100), bar(101, 102, 100, 101)) is None
    assert limit_ref(Side.BUY, D(100), bar(101, 102, 99.95, 101)) == D(100)
    assert limit_ref(Side.SELL, D(110), bar(108, 110, 107, 109)) is None
    assert limit_ref(Side.SELL, D(110), bar(108, 110.05, 107, 109)) == D(110)


def test_limit_opening_through_fills_at_the_better_open():
    assert limit_ref(Side.BUY, D(100), bar(99, 101, 98, 100)) == D(99)
    assert limit_ref(Side.SELL, D(110), bar(111, 112, 109, 111)) == D(111)


def test_same_bar_stop_and_target_stop_fills_first():
    b = bar(100, 106, 94, 101)
    assert bracket_exit(Side.SELL, D(95), D(105), b, check_target=True) == (ExitReason.STOP, D(95))
    # Short position: buy stop above, buy-limit target below.
    assert bracket_exit(Side.BUY, D(105), D(95), b, check_target=True) == (ExitReason.STOP, D(105))


def test_target_alone_and_entry_bar_rule():
    b = bar(100, 106, 99, 105)
    assert bracket_exit(Side.SELL, D(95), D(105), b, check_target=True) == (
        ExitReason.TARGET,
        D(105),
    )
    assert bracket_exit(Side.SELL, D(95), D(105), b, check_target=False) is None
    assert bracket_exit(Side.SELL, None, None, b, check_target=True) is None


def _leg(side: Side, trigger: str) -> Order:
    return Order("X", Product.MIS, side, 10, OrderType.STOP, OrderRole.ENTRY, TS, price=D(trigger))


def test_oco_legs_nearer_trigger_fills_first():
    legs = [(1, _leg(Side.BUY, "105")), (2, _leg(Side.SELL, "96"))]
    assert first_leg(legs, bar(100, 106, 95, 100)) == (2, D(96))  # 4 from the open vs 5


def test_oco_gapped_leg_counts_as_distance_zero():
    legs = [(1, _leg(Side.BUY, "105")), (2, _leg(Side.SELL, "96"))]
    assert first_leg(legs, bar(106, 107, 95, 100)) == (1, D(106))


def test_oco_exact_tie_goes_to_earlier_submission():
    legs = [(7, _leg(Side.SELL, "96")), (3, _leg(Side.BUY, "104"))]
    assert first_leg(legs, bar(100, 105, 95, 100)) == (3, D(104))


def test_oco_untriggered_legs_give_none():
    legs = [(1, _leg(Side.BUY, "105")), (2, _leg(Side.SELL, "96"))]
    assert first_leg(legs, bar(100, 104, 97, 100)) is None


@pytest.mark.parametrize("side", [Side.BUY, Side.SELL])
def test_market_like_open_ref_is_the_open(side):
    leg = Order("X", Product.MIS, side, 1, OrderType.MARKET, OrderRole.ENTRY, TS)
    assert first_leg([(1, leg)], bar(100.05, 101, 99, 100)) == (1, D("100.05"))
