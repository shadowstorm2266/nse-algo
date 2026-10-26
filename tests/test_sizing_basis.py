"""Sizing basis: backtests size every session off the fixed `capital` (no compounding);
paper and live size off current equity. Drawdown halt and daily loss use real equity."""

import math
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from nsealgo.brokers.fills import Bar
from nsealgo.brokers.sim import SimBroker
from nsealgo.engine.portfolio import Portfolio
from nsealgo.engine.risk import RiskGovernor
from nsealgo.engine.sessions import TradingCalendar
from nsealgo.engine.types import (
    Order,
    OrderRole,
    OrderStatus,
    OrderType,
    Product,
    Rejection,
    RejectReason,
    Side,
)
from nsealgo.reporting.metrics import compute_metrics, equity_metrics
from tests.data_helpers import business_days
from tests.engine_helpers import (
    ScriptedStrategy,
    cost_config,
    entry,
    make_fill,
    margins,
    risk_config,
    run_frames,
    session_frame,
    snap,
    ts,
)

D = Decimal
DAYS = business_days("2024-01-01", 10)
DAY, DAY2 = DAYS[1], DAYS[2]
CURRENT = {"backtest": "current_equity", "paper": "current_equity", "live": "current_equity"}
DRAINED_TODAY_UP = {"equity": "10000", "start": "9000", "peak": "20000"}


def gov(product: Product, mode: str = "backtest", **risk) -> RiskGovernor:
    return RiskGovernor(
        risk_config(**risk),
        margins("25"),
        TradingCalendar(DAYS),
        cost_config(),
        "shoonya",
        product=product,
        mode=mode,
    )


def qty(g: RiskGovernor, intent, hhmm: str = "10:00", **snap_kw) -> int | Rejection:
    now = ts(DAY, hhmm)
    out = g.review(intent, snap(now, marks={"Y": 100.0}, **snap_kw), now)
    return out if isinstance(out, Rejection) else out.qty


# --- config ---


def test_backtests_fixed_capital_paper_and_live_current_equity():
    sb = risk_config().sizing_basis
    assert (sb.backtest, sb.paper, sb.live) == ("fixed_capital", "current_equity", "current_equity")
    assert gov(Product.MIS).sizing_basis == "fixed_capital"
    assert gov(Product.MIS, mode="paper").sizing_basis == "current_equity"
    assert gov(Product.CNC, mode="live").sizing_basis == "current_equity"
    for mode in ("paper", "live"):
        with pytest.raises(ValidationError):
            risk_config(sizing_basis={**CURRENT, mode: "fixed_capital"})


# --- RiskGovernor: MIS ---

MARGIN_BOUND = entry("Y", Side.BUY, order_type=OrderType.STOP, price=100.0, stop=99.9)


def test_mis_fixed_capital_sizes_a_drained_account_like_a_fresh_one():
    g = gov(Product.MIS, max_gross_exposure_rupees=200000)  # by_risk 1000, exposure 2000
    assert qty(g, MARGIN_BOUND) == 800  # margin-bound: 20000 / (100 x 25%)
    assert qty(g, MARGIN_BOUND, equity="1000", peak="20000") == 800
    current = gov(Product.MIS, max_gross_exposure_rupees=200000, sizing_basis=CURRENT)
    assert qty(current, MARGIN_BOUND, equity="1000", peak="20000") == 40


def test_mis_fixed_capital_keeps_the_sessions_own_pnl():
    g = gov(Product.MIS, max_gross_exposure_rupees=200000)
    # The session opened at 1000 (rebased to 20000) and has lost 100 since.
    assert qty(g, MARGIN_BOUND, equity="900", start="1000", peak="20000") == 796  # 19900 / 25
    # The daily loss limit still uses real equity.
    out = qty(g, MARGIN_BOUND, equity="690", start="1000", peak="20000")
    assert isinstance(out, Rejection) and out.reason is RejectReason.DAILY_LOSS_LIMIT


# --- RiskGovernor: CNC ---

SWING_BUY = entry("Y", Side.BUY, product=Product.CNC)


def test_cnc_fixed_capital_sizes_off_capital_exactly():
    g = gov(Product.CNC)
    fresh = qty(g, SWING_BUY, "15:30")
    assert fresh == 49  # slot (20000 - est. charges) / 4 at 100
    # Decided after the close for the next open: today's P&L is not carried either.
    assert qty(g, SWING_BUY, "15:30", **DRAINED_TODAY_UP) == fresh
    assert qty(g, SWING_BUY, "15:30", equity="21000", start="20000", peak="21000") == fresh
    current = gov(Product.CNC, sizing_basis=CURRENT)
    assert qty(current, SWING_BUY, "15:30", **DRAINED_TODAY_UP) == 24


# --- Portfolio and broker cash check ---


def _lost_12000(basis: str) -> Portfolio:
    pf = Portfolio(D(20000), margins("25"), basis)
    pf.start_session(DAY)
    when = ts(DAY, "10:00")
    pf.apply_fill(make_fill(Side.BUY, 100, "200", "200", symbol="Z", when=when))
    pf.apply_fill(make_fill(Side.SELL, 100, "80", "80", symbol="Z", role=OrderRole.EXIT, when=when))
    pf.end_session()
    pf.start_session(DAY2)
    return pf


@pytest.mark.parametrize(("basis", "power"), [("fixed_capital", 20000), ("current_equity", 8000)])
def test_cnc_cash_check_uses_the_rebased_account(basis, power):
    pf = _lost_12000(basis)
    assert pf.free_cash() == D(8000) and pf.equity() == D(8000)  # real accounting
    assert pf.buying_power() == D(power)
    broker = SimBroker(cost_config(), "shoonya", D(3), funds=pf, on_fill=pf.apply_fill)
    order = Order(
        "A", Product.CNC, Side.BUY, 120, OrderType.MARKET, OrderRole.ENTRY, ts(DAY, "15:30")
    )
    order_id = broker.place(order)  # ~12,000: fits 20,000, not 8,000
    broker.process({"A": Bar("A", ts(DAY2, "09:15"), DAY2, 100.0, 101.0, 99.0, 100.0)})
    rejected = [
        e for e in broker.events if e.order_id == order_id and e.status is OrderStatus.REJECTED
    ]
    if basis == "fixed_capital":
        assert not rejected and pf.positions["A"].qty == 120
    else:
        assert "INSUFFICIENT_CASH" in rejected[0].reason and "A" not in pf.positions


# --- through the Backtester ---


def _gap_down_then_flat() -> tuple[pd.DataFrame, dict]:
    """Day 1: long at 10:00, the 10:30 bar gaps to 50 through the stop. Day 2: flat 100."""
    d1 = session_frame("Y", DAY, 5, lambda t: 100.0 if t < ts(DAY, "10:30") else 50.0, spread=0.05)
    d2 = session_frame("Y", DAY2, 5, 100.0, spread=0.05)
    script = {ts(d, "10:00"): [entry("Y", Side.BUY, stop=99.6)] for d in (DAY, DAY2)}
    return pd.concat([d1, d2], ignore_index=True), script


@pytest.mark.parametrize(("basis", "day2_qty"), [("fixed_capital", 200), ("current_equity", 99)])
def test_backtester_day_two_size(basis, day2_qty):
    bars, script = _gap_down_then_flat()
    strategy = ScriptedStrategy(Product.MIS, "5m", script)
    overrides = {} if basis == "fixed_capital" else {"sizing_basis": CURRENT}
    result, bt = run_frames(strategy, bars, [DAY, DAY2], margin_pct="100", **overrides)
    first, second = bt.portfolio.trades
    assert first.qty == 200 and first.exit_reason == "stop"  # margin-bound: 20000 / 100
    assert second.qty == day2_qty
    assert float(first.net_pnl) < -9900
    # The equity curve is the real account either way.
    eq = result.equity["equity"].tolist()
    assert eq[0] == pytest.approx(20000 + float(first.net_pnl))
    assert eq[1] == pytest.approx(eq[0] + float(second.net_pnl))


# --- metrics ---


def test_fixed_capital_returns_are_pnl_over_capital():
    eq = pd.DataFrame({"equity": [19000.0, 18000.0, 19000.0]})
    m = equity_metrics(eq, 20000.0, return_base=20000.0)
    rets = np.array([-0.05, -0.05, 0.05])
    sharpe = rets.mean() / rets.std(ddof=1) * math.sqrt(252)
    assert m["sharpe_daily_annualized"] == pytest.approx(sharpe)
    assert m["total_return_pct"] == pytest.approx(-5.0)
    neg = equity_metrics(pd.DataFrame({"equity": [10000.0, -5000.0, -4000.0]}), 20000.0, 20000.0)
    assert neg["total_return_pct"] == pytest.approx(-120.0)
    assert neg["max_drawdown_rs"] == pytest.approx(25000.0)
    assert math.isfinite(neg["sharpe_daily_annualized"])


def test_fixed_capital_drawdown_pct_is_of_capital():
    eq = pd.DataFrame({"equity": [19000.0, 25000.0, 15000.0]})
    fixed = equity_metrics(eq, 20000.0, return_base=20000.0)
    assert fixed["max_drawdown_rs"] == pytest.approx(10000.0)
    assert fixed["max_drawdown_pct"] == pytest.approx(50.0)  # 10,000 of 20,000 capital
    assert equity_metrics(eq, 20000.0)["max_drawdown_pct"] == pytest.approx(40.0)  # of 25,000
    below_zero = equity_metrics(pd.DataFrame({"equity": [-1000.0, -6000.0]}), 20000.0, 20000.0)
    assert below_zero["max_drawdown_pct"] == pytest.approx(130.0)  # 26,000 of 20,000
    logged = compute_metrics(pd.DataFrame(), eq, 20000.0, sizing_basis="fixed_capital")
    assert logged["max_drawdown_pct"] == pytest.approx(50.0)


def test_compute_metrics_records_the_basis():
    eq = pd.DataFrame({"equity": [19000.0, 18000.0, 19000.0]})
    fixed = compute_metrics(pd.DataFrame(), eq, 20000.0, sizing_basis="fixed_capital")
    current = compute_metrics(pd.DataFrame(), eq, 20000.0, sizing_basis="current_equity")
    assert fixed["sizing_basis"] == "fixed_capital"
    assert fixed["sharpe_daily_annualized"] != current["sharpe_daily_annualized"]
