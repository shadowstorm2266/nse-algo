from decimal import Decimal

import pytest

from nsealgo.engine.portfolio import Portfolio
from nsealgo.engine.types import ExitReason, OrderRole, Product, Side
from tests.engine_helpers import make_fill, margins

D = Decimal


@pytest.fixture
def pf() -> Portfolio:
    return Portfolio(D(20000), margins("25"))


def test_long_mis_round_trip_ledger_margin_and_trade(pf):
    pf.apply_fill(make_fill(Side.BUY, 20, "500.15", "500", cost="4.21", stop="495"))
    assert pf.ledger == D("19995.79")
    assert pf.margin_used() == D("2500.7500")  # 20 x 500.15 x 25%
    pf.mark("X", 505.0)
    assert pf.unrealized() == D("97.000")  # (505 - 500.15) x 20
    assert pf.equity() == D("20092.790")
    assert pf.free_cash() == D("17495.0400")  # unrealized gains are not spendable
    trade = pf.apply_fill(
        make_fill(
            Side.SELL,
            20,
            "509.847",
            "510",
            cost="6.53",
            role=OrderRole.EXIT,
            reason=ExitReason.STRATEGY,
        )
    )
    assert trade is not None
    assert (trade.gross_pnl, trade.slippage, trade.costs) == (D(200), D("6.060"), D("10.74"))
    assert trade.net_pnl == D("183.200")
    assert trade.r_multiple == pytest.approx(183.2 / (5.15 * 20))
    assert pf.ledger == D("20183.200")
    assert not pf.positions and pf.margin_used() == 0


def test_short_mis_pnl_and_losses_reduce_free_cash(pf):
    pf.apply_fill(make_fill(Side.SELL, 10, "199.94", "200", cost="1"))
    pf.mark("X", 210.0)
    assert pf.unrealized() == D("-100.600")  # (210 - 199.94) x -10
    assert pf.free_cash() == pf.ledger - D("100.600") - pf.margin_used()
    trade = pf.apply_fill(make_fill(Side.BUY, 10, "190.057", "190", cost="1", role=OrderRole.EXIT))
    assert trade.side == "short"
    assert trade.gross_pnl == D(100)  # (190 - 200) x 10 x -1
    assert trade.slippage == D("1.170")  # 0.06 x 10 + 0.057 x 10
    assert trade.net_pnl == D("96.830")
    assert pf.ledger == D(20000) + D("96.830")


def test_partial_exits_share_entry_costs_pro_rata_and_sum_exactly(pf):
    pf.apply_fill(make_fill(Side.BUY, 30, "100", "100", cost="1.00"))
    parts = [
        pf.apply_fill(make_fill(Side.SELL, 10, "101", "101", role=OrderRole.EXIT)) for _ in range(3)
    ]
    assert [t.costs for t in parts] == [D("0.33"), D("0.33"), D("0.34")]
    assert sum(t.net_pnl for t in parts) == D(30) - D("1.00")


def test_no_pyramiding_and_no_flip(pf):
    pf.apply_fill(make_fill(Side.BUY, 10, "100", "100"))
    with pytest.raises(ValueError):
        pf.apply_fill(make_fill(Side.BUY, 5, "100", "100"))
    with pytest.raises(ValueError):
        pf.apply_fill(make_fill(Side.SELL, 11, "100", "100", role=OrderRole.EXIT))


def test_cnc_uses_full_cash_as_margin(pf):
    pf.apply_fill(make_fill(Side.BUY, 10, "100", "100", product=Product.CNC))
    assert pf.margin_used() == D(1000)


def test_cash_for_cnc_buys_ignores_holding_losses_but_not_mis_losses(pf):
    pf.apply_fill(make_fill(Side.BUY, 10, "100", "100", cost="1", product=Product.CNC))
    pf.mark("X", 80.0)  # the delivery holding is down 200
    assert pf.unrealized() == D(-200)
    assert pf.cash() == D(20000) - 1 - 1000  # paid for in full: the loss moves no cash
    assert pf.buying_power() == pf.cash()
    assert pf.free_cash() == pf.cash() - 200  # MIS free margin still counts the loss
    pf.apply_fill(make_fill(Side.SELL, 10, "50", "50", symbol="Y", cost="1"))
    pf.mark("Y", 60.0)  # an MIS short down 100 is a cash loss
    assert pf.unrealized(Product.MIS) == D(-100)
    assert pf.cash() == pf.ledger - 100 - pf.margin_used()
    pf.mark("X", 130.0)  # gains are not spendable
    assert pf.cash() == pf.ledger - 100 - pf.margin_used()


def test_session_start_equity_and_peak(pf):
    pf.start_session(make_fill(Side.BUY, 1, "1", "1").session_date)
    assert pf.equity_at_session_start == D(20000)
    pf.apply_fill(make_fill(Side.BUY, 10, "100", "100", cost="5"))
    row = pf.end_session()
    assert row["equity"] == D(19995)
    assert pf.peak_equity == D(20000)  # running max of capital and session-end equity
