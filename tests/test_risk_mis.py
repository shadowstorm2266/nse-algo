from datetime import date
from decimal import Decimal

import pytest

from nsealgo.engine.risk import RiskGovernor
from nsealgo.engine.sessions import TradingCalendar
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
    make_fill,
    margins,
    pos_view,
    risk_config,
    snap,
    ts,
    view,
    working_order,
)

D = Decimal
DAYS = business_days("2024-01-01", 10)
DAY, NO_TRADE_DAY = DAYS[1], DAYS[2]  # Tue 2024-01-02, Wed 2024-01-03
MARKS = {"X": 500.0, "Y": 100.0}


def governor(margin_pct: str = "25", kill_file=None, **risk) -> RiskGovernor:
    return RiskGovernor(
        risk_config(**risk),
        margins(margin_pct),
        TradingCalendar(DAYS, [NO_TRADE_DAY]),
        cost_config(),
        "shoonya",
        product=Product.MIS,
        mode="backtest",
        kill_file=kill_file,
    )


def at(hhmm: str, day: date = DAY):
    return ts(day, hhmm)


def review(gov, intent, hhmm="10:00", day=DAY, **snap_kw):
    now = at(hhmm, day)
    return gov.review(intent, snap(now, marks=MARKS, **snap_kw), now)


def reason(result) -> RejectReason | None:
    return result.reason if isinstance(result, Rejection) else None


LONG = entry("X", Side.BUY, stop=495.0)  # ref 500 -> 5 rupees of risk per share


@pytest.mark.parametrize(
    ("hhmm", "expected"),
    [
        ("09:40", RejectReason.BEFORE_ENTRY_START),
        ("09:45", None),
        ("14:00", None),
        ("14:05", RejectReason.AFTER_ENTRY_END),
        ("14:50", RejectReason.AFTER_ENTRY_END),
    ],
)
def test_entry_window(hhmm, expected):
    assert reason(review(governor(), LONG, hhmm)) == expected


def test_rejects_beyond_daily_loss():
    assert reason(review(governor(), LONG, equity="19700", start="20000")) == (
        RejectReason.DAILY_LOSS_LIMIT
    )
    assert reason(review(governor(), LONG, equity="19700.01", start="20000")) is None


def test_rejects_beyond_max_trades():
    two = (
        make_fill(Side.BUY, 1, "1", "1", symbol="A"),
        make_fill(Side.BUY, 1, "1", "1", symbol="B"),
    )
    assert reason(review(governor(), LONG, fills=two)) == RejectReason.MAX_TRADES_PER_DAY
    one_and_working = (view(9, working_order("Y", Side.BUY, 5, "100", when=at("09:50"))),)
    r = review(governor(), LONG, fills=two[:1], orders=one_and_working)
    assert reason(r) == RejectReason.MAX_TRADES_PER_DAY
    assert reason(review(governor(), LONG, fills=two[:1])) is None


def test_exit_fills_today_do_not_count_as_trades():
    fills = (
        make_fill(Side.BUY, 1, "1", "1", symbol="A"),
        make_fill(Side.SELL, 1, "1", "1", symbol="A", role=OrderRole.EXIT),
    )
    assert reason(review(governor(), LONG, fills=fills)) is None


@pytest.mark.parametrize(
    "intent",
    [
        entry("X", Side.BUY, stop=350.0),  # 100 / 150 per share -> 0
        entry("Y", Side.BUY, stop=99.0),
    ],
)
def test_rejects_qty_below_one(intent):
    gov = governor(max_gross_exposure_rupees=50) if intent.symbol == "Y" else governor()
    r = review(gov, intent)
    assert reason(r) == RejectReason.QTY_BELOW_ONE
    assert "by_risk" in r.detail and "by_exposure" in r.detail and "by_margin" in r.detail


def test_rejects_on_no_trade_day():
    assert reason(review(governor(), LONG, day=NO_TRADE_DAY)) == RejectReason.NO_TRADE_SESSION


def test_rejects_with_kill_file_but_still_allows_exits(tmp_path):
    kill = tmp_path / "KILL"
    gov = governor(kill_file=kill)
    assert reason(review(gov, LONG)) is None
    kill.write_text("", encoding="utf-8")
    assert reason(review(gov, LONG)) == RejectReason.KILL_SWITCH
    held = (pos_view("X", 10, "500"),)
    assert isinstance(review(gov, exit_("X"), positions=held), Order)


def test_one_position_per_symbol():
    held = (pos_view("X", 10, "500"),)
    assert reason(review(governor(), LONG, positions=held)) == RejectReason.POSITION_EXISTS
    pending = (view(3, working_order("X", Side.BUY, 5, "500", when=at("09:50"))),)
    assert reason(review(governor(), LONG, orders=pending)) == RejectReason.POSITION_EXISTS


@pytest.mark.parametrize(
    "intent",
    [
        entry("X", Side.BUY, stop=None),
        entry("X", Side.BUY, stop=505.0),
        entry("X", Side.SELL, stop=495.0),
        entry("X", Side.BUY, stop=500.0),
    ],
)
def test_bad_stops_rejected(intent):
    assert reason(review(governor(), intent)) == RejectReason.INVALID_STOP


def test_no_price_rejected():
    assert reason(review(governor(), entry("Z", Side.BUY, stop=1.0))) == RejectReason.NO_PRICE


@pytest.mark.parametrize(
    ("intent", "margin", "qty"),
    [
        (entry("X", Side.BUY, stop=495.0), "25", 20),  # risk 100/5; exposure 120; margin 160
        (entry("X", Side.BUY, stop=499.9), "25", 120),  # exposure 60000/500 binds
        (entry("X", Side.BUY, stop=499.9), "100", 40),  # margin 20000/(500 x 100%) binds
        (entry("X", Side.SELL, stop=510.0), "25", 10),  # short: 100/10
    ],
)
def test_qty_is_min_of_risk_exposure_and_margin(intent, margin, qty):
    order = review(governor(margin), intent)
    assert isinstance(order, Order)
    assert order.qty == qty
    assert order.ref_price == D("500.0")
    assert order.expires_at == at("14:00")


def test_stop_entry_sizes_on_its_trigger_price():
    intent = entry("X", Side.BUY, order_type=OrderType.STOP, price=510.0, stop=505.0)
    order = review(governor(), intent)
    assert (order.qty, order.price, order.ref_price) == (20, D("510.0"), D("510.0"))


def test_open_positions_use_exposure_and_free_margin():
    held = (pos_view("Y", 300, "100"),)  # 30000 of exposure, 7500 margin used at 25%
    order = review(governor(), entry("X", Side.BUY, stop=499.9), positions=held, margin_used="7500")
    assert order.qty == 60  # (60000 - 30000) / 500 = 60; margin (20000-7500)/125 = 100


def test_exit_reviews():
    held = (pos_view("X", -10, "500"),)
    assert reason(review(governor(), exit_("X"))) == RejectReason.NO_POSITION
    order = review(governor(), exit_("X"), "15:00", positions=held)
    assert (order.side, order.qty, order.role, order.exit_reason) == (
        Side.BUY,
        10,
        OrderRole.EXIT,
        ExitReason.STRATEGY,
    )
    assert reason(review(governor(), exit_("X", qty=11), positions=held)) == (
        RejectReason.INVALID_INTENT
    )
    pending = (
        view(4, working_order("X", Side.BUY, 10, "500", when=at("09:50"), role=OrderRole.EXIT)),
    )
    r = review(governor(), exit_("X"), positions=held, orders=pending)
    assert reason(r) == RejectReason.DUPLICATE_EXIT


def test_wrong_product_rejected():
    assert reason(review(governor(), entry("X", product=Product.CNC))) == (
        RejectReason.WRONG_PRODUCT
    )


def test_forced_exits_at_flat_by():
    gov = governor()
    held = (pos_view("X", 10, "500"), pos_view("Y", -5, "100"))
    strategy_exit = view(
        5, working_order("X", Side.SELL, 10, "500", when=at("14:45"), role=OrderRole.EXIT)
    )
    stale_entry = view(6, working_order("Z", Side.BUY, 5, "50", when=at("13:00")))
    before = snap(at("14:45"), positions=held, orders=(strategy_exit, stale_entry))
    assert gov.forced_exits(before, at("14:45")) == ([], [])
    s = snap(at("14:50"), positions=held, orders=(strategy_exit, stale_entry))
    orders, cancels = gov.forced_exits(s, at("14:50"))
    assert sorted(cancels) == [5, 6]
    assert {(o.symbol, o.side, o.qty, o.exit_reason) for o in orders} == {
        ("X", Side.SELL, 10, ExitReason.FLAT_BY),
        ("Y", Side.BUY, 5, ExitReason.FLAT_BY),
    }
    assert all(o.order_type is OrderType.MARKET for o in orders)
    flat_x = view(7, orders[0])
    again = snap(at("14:51"), positions=held[:1], orders=(flat_x,))
    assert gov.forced_exits(again, at("14:51")) == ([], [])


# --- OCO entry groups ---

BUY_LEG = entry("X", Side.BUY, order_type=OrderType.STOP, price=500.0, stop=499.0, group="g1")
SELL_LEG = entry("X", Side.SELL, order_type=OrderType.STOP, price=400.0, stop=401.0, group="g1")


def _placed(order: Order, order_id: int):
    return view(order_id, order)


def test_group_counts_as_one_trade_and_one_slot():
    gov = governor()
    fills = (make_fill(Side.BUY, 1, "1", "1", symbol="A"),)
    leg1 = review(gov, BUY_LEG, fills=fills)
    assert isinstance(leg1, Order)
    leg2 = review(gov, SELL_LEG, fills=fills, orders=(_placed(leg1, 1),))
    assert isinstance(leg2, Order)  # same slot, same trade
    both = (_placed(leg1, 1), _placed(leg2, 2))
    r = review(gov, entry("Y", Side.BUY, stop=99.0), fills=fills, orders=both)
    assert reason(r) == RejectReason.MAX_TRADES_PER_DAY
    r = review(gov, entry("X", Side.BUY, stop=495.0), orders=both)
    assert reason(r) == RejectReason.POSITION_EXISTS


def test_group_exposure_and_margin_count_the_larger_leg():
    # Legs: 20 x 500 = 10000 and 30 x 400 = 12000 notional -> 12000 counts.
    legs = (
        view(
            1,
            working_order(
                "X", Side.BUY, 20, "500", when=at("09:50"), order_type=OrderType.STOP, group="g1"
            ),
        ),
        view(
            2,
            working_order(
                "X", Side.SELL, 30, "400", when=at("09:50"), order_type=OrderType.STOP, group="g1"
            ),
        ),
    )
    y = entry("Y", Side.BUY, stop=99.9)  # risk allows 1000
    assert review(governor("25"), y, orders=legs).qty == 480  # (60000-12000)/100; margin 680
    assert review(governor("100"), y, orders=legs).qty == 80  # (20000-12000)/100


def test_second_leg_is_sized_without_its_sibling():
    gov = governor("100")
    leg1 = review(gov, BUY_LEG)
    assert leg1.qty == 40  # margin 20000/500
    leg2 = review(gov, SELL_LEG, orders=(_placed(leg1, 1),))
    assert leg2.qty == 50  # margin 20000/400, the sibling's 20000 is not added


def test_screen_groups_rejects_malformed_groups():
    gov = governor()
    now = at("10:00")
    s = snap(now, marks=MARKS)
    third = entry("X", Side.BUY, order_type=OrderType.LIMIT, price=450.0, stop=440.0, group="g1")
    market = entry("X", Side.BUY, stop=495.0, group="g2")
    mixed = entry("Y", Side.SELL, order_type=OrderType.STOP, price=90.0, stop=91.0, group="g3")
    mixed_x = entry("X", Side.BUY, order_type=OrderType.STOP, price=510.0, stop=505.0, group="g3")
    ok, rejected = gov.screen_groups(
        [BUY_LEG, SELL_LEG, third, market, mixed, mixed_x, LONG], s, now
    )
    assert ok == [LONG]
    assert {r.reason for r in rejected} == {RejectReason.INVALID_GROUP}
    assert len(rejected) == 6
    ok, rejected = gov.screen_groups([BUY_LEG, SELL_LEG], s, now)
    assert ok == [BUY_LEG, SELL_LEG] and not rejected
    earlier = snap(
        now,
        marks=MARKS,
        orders=(view(1, working_order("X", Side.BUY, 5, "500", when=at("09:50"), group="g1")),),
    )
    ok, rejected = gov.screen_groups([SELL_LEG], earlier, now)
    assert not ok and rejected[0].reason is RejectReason.INVALID_GROUP
