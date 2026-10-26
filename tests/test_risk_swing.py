from decimal import Decimal

import pytest

from nsealgo.costs import fill_charges
from nsealgo.engine.risk import RiskGovernor
from nsealgo.engine.sessions import TradingCalendar, session_close
from nsealgo.engine.types import (
    ExitReason,
    Order,
    OrderRole,
    OrderType,
    Product,
    Rejection,
    RejectReason,
    Side,
)
from tests.data_helpers import business_days
from tests.engine_helpers import (
    cost_config,
    entry,
    exit_,
    margins,
    pos_view,
    risk_config,
    snap,
    ts,
    view,
    working_order,
)

D = Decimal
CNC = Product.CNC
DAYS = business_days("2024-01-01", 6)  # Mon 1 .. Mon 8 Jan
NO_TRADE = DAYS[2]  # Wed 3 Jan


def governor(mode: str = "backtest", **swing) -> RiskGovernor:
    return RiskGovernor(
        risk_config(swing=swing),
        margins(),
        TradingCalendar(DAYS, [NO_TRADE]),
        cost_config(),
        "shoonya",
        product=CNC,
        mode=mode,
    )


def buy(symbol: str = "A", rank: int | None = 1, **kw):
    return entry(symbol, Side.BUY, product=CNC, rank=rank, **kw)


def review(gov, intent, day_i: int = 0, marks=None, **kw):
    now = ts(DAYS[day_i], "15:30")
    return gov.review(intent, snap(now, marks=marks or {"A": 100.0}, **kw), now)


def reason(result):
    return result.reason if isinstance(result, Rejection) else None


def test_equal_weight_slot_after_estimated_buy_charges():
    cfg = cost_config()
    est = 4 * fill_charges("CNC", "BUY", D(5000), cfg.rates, cfg.broker.delivery).total
    assert est == D("23.76")  # 4 x 5.94
    order = review(governor(), buy())
    assert isinstance(order, Order)
    assert order.qty == 49  # floor(((20000 - 23.76) / 4) / 100) = floor(49.94)
    assert (order.order_type, order.role, order.rank) == (OrderType.MARKET, OrderRole.ENTRY, 1)
    assert order.not_before == DAYS[1]  # the next session's open
    assert order.expires_at == session_close(DAYS[1])


def test_slot_uses_current_equity_in_paper_and_capital_in_backtests():
    # Buy charges on 6000 are 7.12, so the slot is (24000 - 4 x 7.12) / 4 = 5992.88.
    assert review(governor(mode="paper"), buy(), equity="24000").qty == 59
    # Backtests size off the fixed 20000 capital (sizing_basis.backtest: fixed_capital).
    assert review(governor(), buy(), equity="24000").qty == 49


def test_one_share_when_the_slot_buys_none_but_it_fits_the_cap():
    order = review(governor(), buy(), marks={"A": 5500.0})  # slot ~4994 < 5500 <= 6000
    assert isinstance(order, Order) and order.qty == 1


def test_skip_when_one_share_is_above_the_cap_and_log_price_and_rank():
    r = review(governor(), buy(rank=3), marks={"A": 6500.0})
    assert reason(r) == RejectReason.PRICE_ABOVE_POSITION_CAP
    assert (r.price, r.rank) == (6500.0, 3)
    assert "6500" in r.detail and "6000" in r.detail


def test_gross_cap_counts_held_and_pending():
    held = tuple(pos_view(s, 60, "100", product=CNC) for s in "BCD")  # 18000 of 20000
    r = review(governor(), buy(), marks={"A": 2500.0}, positions=held)
    assert reason(r) == RejectReason.QTY_BELOW_ONE  # 1 share would take gross to 20500


def test_max_positions_and_a_pending_full_exit_frees_its_slot():
    held = tuple(pos_view(s, 10, "100", product=CNC) for s in "BCDE")
    assert reason(review(governor(), buy(), positions=held)) == RejectReason.MAX_POSITIONS
    sell_e = working_order(
        "E",
        Side.SELL,
        10,
        "100",
        when=ts(DAYS[0], "15:30"),
        role=OrderRole.EXIT,
        product=CNC,
        reason=ExitReason.STRATEGY,
    )
    order = review(governor(), buy(), positions=held, orders=(view(1, sell_e),))
    assert isinstance(order, Order)
    partial = working_order(
        "E",
        Side.SELL,
        5,
        "100",
        when=ts(DAYS[0], "15:30"),
        role=OrderRole.EXIT,
        product=CNC,
        reason=ExitReason.STRATEGY,
    )
    r = review(governor(), buy(), positions=held, orders=(view(1, partial),))
    assert reason(r) == RejectReason.MAX_POSITIONS


def test_max_orders_per_day():
    today = ts(DAYS[0], "15:30")
    placed = tuple(
        view(i, working_order(s, Side.BUY, 1, "1", when=today, product=CNC))
        for i, s in enumerate("BCDEFGHI")
    )
    assert reason(review(governor(max_positions=20), buy(), orders=placed)) == (
        RejectReason.MAX_ORDERS_PER_DAY
    )
    assert isinstance(review(governor(max_positions=20), buy(), orders=placed[:7]), Order)


def test_fill_session_skips_no_trade_days():
    order = review(governor(), buy(), day_i=1)  # Tue decision; Wed is no_trade
    assert order.not_before == DAYS[3]
    held = (pos_view("A", 10, "100", product=CNC),)
    sell = review(governor(), exit_("A", product=CNC), day_i=1, positions=held)
    assert (sell.side, sell.not_before, sell.qty) == (Side.SELL, DAYS[3], 10)


def test_no_next_session_at_the_end_of_the_calendar():
    assert reason(review(governor(), buy(), day_i=5)) == RejectReason.NO_NEXT_SESSION


@pytest.mark.parametrize(
    ("intent", "expected"),
    [
        (entry("A", Side.SELL, product=CNC), RejectReason.SHORT_NOT_ALLOWED),
        (buy(order_type=OrderType.LIMIT, price=99.0), RejectReason.INVALID_INTENT),
        (buy(stop=90.0), RejectReason.INVALID_INTENT),
        (buy(target=120.0), RejectReason.INVALID_INTENT),
        (buy(group="g"), RejectReason.INVALID_INTENT),
        (entry("A", Side.BUY, product=Product.MIS, stop=99.0), RejectReason.WRONG_PRODUCT),
    ],
)
def test_swing_intent_shape(intent, expected):
    assert reason(review(governor(), intent)) == expected


def test_swing_disabled():
    assert reason(review(governor(enabled=False), buy())) == RejectReason.SWING_DISABLED


def test_no_daily_loss_stop_for_swing():
    assert isinstance(review(governor(), buy(), equity="19000", start="20000"), Order)


def test_position_exists():
    held = (pos_view("A", 10, "100", product=CNC),)
    assert reason(review(governor(), buy(), positions=held)) == RejectReason.POSITION_EXISTS
