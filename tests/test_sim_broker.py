from datetime import date
from decimal import Decimal

import pytest

from nsealgo.brokers.fills import Bar
from nsealgo.brokers.sim import SimBroker
from nsealgo.engine.portfolio import Portfolio
from nsealgo.engine.types import (
    ExitReason,
    Order,
    OrderRole,
    OrderStatus,
    OrderType,
    Product,
    Side,
)
from tests.engine_helpers import cost_config, margins, ts

D = Decimal
DAY, DAY2, DAY3 = date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)


@pytest.fixture
def pf() -> Portfolio:
    p = Portfolio(D(20000), margins("25"))
    p.start_session(DAY)
    return p


@pytest.fixture
def broker(pf) -> SimBroker:
    return SimBroker(cost_config(), "shoonya", D(3), funds=pf, on_fill=pf.apply_fill)


def bar(hhmm: str, o, h, low, c, symbol="X", day=DAY) -> dict[str, Bar]:
    return {symbol: Bar(symbol, ts(day, hhmm), day, o, h, low, c)}


def mis_entry(
    side=Side.BUY,
    qty=20,
    *,
    kind=OrderType.MARKET,
    price=None,
    stop="495",
    target=None,
    group=None,
    created="09:59",
    expires="14:00",
) -> Order:
    return Order(
        "X",
        Product.MIS,
        side,
        qty,
        kind,
        OrderRole.ENTRY,
        ts(DAY, created),
        price=D(price) if price else None,
        ref_price=D(price or "500"),
        stop_loss=D(stop) if stop else None,
        target=D(target) if target else None,
        group_id=group,
        expires_at=ts(DAY, expires),
    )


def status(broker: SimBroker, order_id: int) -> OrderStatus:
    return next(v.status for v in broker.orders() if v.order_id == order_id)


def working_roles(broker: SimBroker) -> set[OrderRole]:
    return {v.order.role for v in broker.orders() if v.status is OrderStatus.WORKING}


def test_market_entry_fills_at_open_plus_slippage_with_charges(broker, pf):
    broker.place(mis_entry(target="520"))
    (f,) = broker.process(bar("10:00", 500, 501, 499, 500.5))
    assert (f.price, f.ref_price, f.qty) == (D("500.15000"), D("500.0"), 20)
    assert f.charges.total == D("4.21")
    assert pf.positions["X"].qty == 20
    assert working_roles(broker) == {OrderRole.STOP, OrderRole.TARGET}
    assert broker.positions()["X"].qty == 20


def test_children_live_on_market_entry_bar_and_stop_beats_target(broker, pf):
    broker.place(mis_entry(target="520"))
    fills = broker.process(bar("10:00", 500, 521, 494, 500))
    assert [f.exit_reason for f in fills] == [None, ExitReason.STOP]
    assert fills[1].ref_price == D(495)
    assert not pf.positions and working_roles(broker) == set()


def test_target_fills_and_cancels_stop(broker, pf):
    broker.place(mis_entry(target="520"))
    broker.process(bar("10:00", 500, 501, 499, 500))
    (f,) = broker.process(bar("10:01", 505, 521, 504, 519))
    assert (f.exit_reason, f.ref_price, f.role) == (ExitReason.TARGET, D(520), OrderRole.TARGET)
    assert f.price == D(520) * (1 - D(3) / 10000)
    stop_id = next(v.order_id for v in broker.orders() if v.order.role is OrderRole.STOP)
    assert status(broker, stop_id) is OrderStatus.CANCELLED


def test_gap_through_stop_fills_at_open(broker, pf):
    broker.place(mis_entry())
    broker.process(bar("10:00", 500, 501, 499, 500))
    (f,) = broker.process(bar("10:01", 490, 491, 489, 490))
    assert (f.exit_reason, f.ref_price) == (ExitReason.STOP, D("490.0"))


def test_stop_entry_fill_bar_checks_only_the_stop_child(broker, pf):
    broker.place(mis_entry(kind=OrderType.STOP, price="505", stop="500", target="507"))
    fills = broker.process(bar("10:00", 502, 508, 501, 506))
    assert len(fills) == 1 and fills[0].ref_price == D(505)  # target not taken on fill bar
    (f,) = broker.process(bar("10:01", 506, 508, 505, 507))
    assert f.exit_reason is ExitReason.TARGET


def test_stop_entry_can_be_stopped_on_its_fill_bar(broker, pf):
    broker.place(mis_entry(kind=OrderType.STOP, price="505", stop="500", target="507"))
    fills = broker.process(bar("10:00", 502, 508, 499, 503))
    assert [f.exit_reason for f in fills] == [None, ExitReason.STOP]


def test_oco_entry_group_sibling_cancelled_on_fill(broker, pf):
    buy_id = broker.place(mis_entry(kind=OrderType.STOP, price="505", stop="500", group="g"))
    sell_id = broker.place(
        mis_entry(Side.SELL, kind=OrderType.STOP, price="495", stop="500", group="g")
    )
    (f,) = broker.process(bar("10:00", 502, 506, 501, 505))  # stop child at 500 untouched
    assert f.order_id == buy_id and f.group_id == "g"
    assert status(broker, sell_id) is OrderStatus.CANCELLED


@pytest.mark.parametrize(
    ("o", "winner"),
    [(500, "buy"), (501, "buy"), (499, "sell"), (507, "buy"), (493, "sell")],
)
def test_oco_both_legs_triggered_in_one_bar(broker, pf, o, winner):
    # 500: tie (5 each) -> earlier submission; 501/499: nearer leg; 507/493: gap -> distance 0.
    buy_id = broker.place(mis_entry(kind=OrderType.STOP, price="505", stop="480", group="g"))
    sell_id = broker.place(
        mis_entry(Side.SELL, kind=OrderType.STOP, price="495", stop="520", group="g")
    )
    fills = broker.process(bar("10:00", o, 508, 492, 500))
    entries = [f for f in fills if f.role is OrderRole.ENTRY]
    assert len(entries) == 1
    assert entries[0].order_id == (buy_id if winner == "buy" else sell_id)
    loser = sell_id if winner == "buy" else buy_id
    assert status(broker, loser) is OrderStatus.CANCELLED


def test_entry_expires_after_its_window(broker, pf):
    oid = broker.place(mis_entry(expires="14:00"))
    assert broker.process(bar("14:05", 500, 501, 499, 500)) == []
    assert status(broker, oid) is OrderStatus.EXPIRED
    assert broker.events[-1].status is OrderStatus.EXPIRED


def test_exit_larger_than_position_is_rejected(broker, pf):
    broker.place(mis_entry(stop=None))
    broker.process(bar("10:00", 500, 501, 499, 500))
    too_big = Order(
        "X",
        Product.MIS,
        Side.SELL,
        21,
        OrderType.MARKET,
        OrderRole.EXIT,
        ts(DAY, "10:00"),
        exit_reason=ExitReason.STRATEGY,
    )
    oid = broker.place(too_big)
    assert broker.process(bar("10:01", 500, 501, 499, 500)) == []
    assert status(broker, oid) is OrderStatus.REJECTED


# --- CNC ---


def cnc(symbol: str, side: Side, qty: int, *, role=OrderRole.ENTRY, not_before=None) -> Order:
    reason = ExitReason.STRATEGY if role is OrderRole.EXIT else None
    return Order(
        symbol,
        Product.CNC,
        side,
        qty,
        OrderType.MARKET,
        role,
        ts(DAY, "15:30"),
        ref_price=D(100),
        exit_reason=reason,
        not_before=not_before,
    )


def daily(symbol: str, day: date, o: float) -> Bar:
    return Bar(symbol, ts(day, "09:15"), day, o, o + 1, o - 1, o)


def test_sells_fill_before_buys_and_fund_them(broker, pf):
    broker.place(cnc("A", Side.BUY, 100))
    broker.process({"A": daily("A", DAY2, 100)})
    assert pf.free_cash() < D(10000)  # 10000 of CNC cash blocked plus buy charges
    buy_id = broker.place(cnc("B", Side.BUY, 150))  # ~15022 with charges: needs A's proceeds
    sell_id = broker.place(cnc("A", Side.SELL, 100, role=OrderRole.EXIT))
    fills = broker.process({"A": daily("A", DAY3, 100), "B": daily("B", DAY3, 100)})
    assert [f.order_id for f in fills] == [sell_id, buy_id]
    assert pf.positions["B"].qty == 150 and "A" not in pf.positions


def test_cnc_buy_that_cash_cannot_cover_is_rejected_and_logged(broker, pf):
    oid = broker.place(cnc("B", Side.BUY, 200))  # 20000 + charges > 20000 free
    assert broker.process({"B": daily("B", DAY2, 100)}) == []
    assert status(broker, oid) is OrderStatus.REJECTED
    ev = broker.events[-1]
    assert ev.status is OrderStatus.REJECTED and ev.reason.startswith("INSUFFICIENT_CASH")
    assert not pf.positions


def test_cnc_buy_is_checked_against_cash_not_reduced_by_holding_losses(broker, pf):
    broker.place(cnc("A", Side.BUY, 100))
    broker.process({"A": daily("A", DAY2, 100)})
    pf.mark("A", 50.0)  # the holding is down 5,003 (bought at 100.03)
    cash = pf.ledger - pf.margin_used()  # ~9,985
    assert pf.buying_power() == cash and pf.free_cash() == cash - D("5003.00")
    oid = broker.place(cnc("B", Side.BUY, 95))  # ~9,514 with charges: fits cash, not free cash
    broker.process({"B": daily("B", DAY3, 100)})
    assert status(broker, oid) is OrderStatus.FILLED and pf.positions["B"].qty == 95


def test_dp_charge_once_per_scrip_per_sell_day(broker, pf):
    broker.place(cnc("A", Side.BUY, 30))
    broker.process({"A": Bar("A", ts(DAY, "10:00"), DAY, 100, 101, 99, 100)})
    dp = []
    for day, hhmm in ((DAY2, "10:00"), (DAY2, "11:00"), (DAY3, "10:00")):
        broker.place(cnc("A", Side.SELL, 10, role=OrderRole.EXIT))
        (f,) = broker.process({"A": Bar("A", ts(day, hhmm), day, 100, 101, 99, 100)})
        dp.append(f.charges.dp_charge)
        assert f.charges.total > 0
    assert dp == [D(9), D(0), D(9)]  # two parts on one day pay once; a second day pays again


def test_not_before_defers_a_cnc_order(broker, pf):
    oid = broker.place(cnc("B", Side.BUY, 10, not_before=DAY3))
    assert broker.process({"B": daily("B", DAY2, 100)}) == []
    assert status(broker, oid) is OrderStatus.WORKING
    (f,) = broker.process({"B": daily("B", DAY3, 100)})
    assert f.session_date == DAY3


def test_end_session_cancels_mis_expires_due_cnc_and_keeps_deferred(broker, pf):
    mis = broker.place(mis_entry())
    due = broker.place(cnc("B", Side.BUY, 10, not_before=DAY))
    later = broker.place(cnc("C", Side.BUY, 10, not_before=DAY3))
    broker.end_session(DAY)
    assert status(broker, later) is OrderStatus.WORKING
    assert {v.order_id for v in broker.orders()} == {later}
    statuses = {e.order_id: e.status for e in broker.events}
    assert statuses[mis] is OrderStatus.CANCELLED and statuses[due] is OrderStatus.EXPIRED


def test_force_close_fills_at_given_price_with_reason(broker, pf):
    broker.place(mis_entry(stop=None))
    broker.process(bar("10:00", 500, 501, 499, 500))
    f = broker.force_close("X", 510.0, ts(DAY, "15:29"), DAY, ExitReason.SESSION_END_FALLBACK)
    assert (f.ref_price, f.exit_reason, f.qty, f.side) == (
        D("510.0"),
        ExitReason.SESSION_END_FALLBACK,
        20,
        Side.SELL,
    )
    assert not pf.positions and not broker.positions()


def test_cancel(broker):
    oid = broker.place(mis_entry())
    assert broker.cancel(oid) and not broker.cancel(oid)
    assert status(broker, oid) is OrderStatus.CANCELLED
    assert (broker.events[-1].order_id, broker.events[-1].reason) == (oid, "cancelled")
