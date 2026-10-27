from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from nsealgo.engine.backtest import Backtester, validate_strategy
from nsealgo.engine.types import OrderStatus, OrderType, Product, Side
from tests.engine_helpers import (
    ScriptedStrategy,
    daily_frame,
    entry,
    exit_,
    risk_config,
    run_frames,
    session_frame,
    ts,
)

D = Decimal
DAY = date(2024, 1, 2)
MIS, CNC = Product.MIS, Product.CNC


def reasons(result) -> list[str]:
    return list(result.rejections["reason"])


def working(bt: Backtester) -> list:
    return [v for v in bt.broker.orders() if v.status is OrderStatus.WORKING]


def test_known_answer_buy_1000_sell_1100():
    # 1m bars: price 500.00 until 10:29, 510.00 from 10:30 (high/low +/- 0.50).
    # 10:00 decision sees the 09:59 close 500.00 -> stop 495 -> qty floor(100/5) = 20
    #   (exposure 60000/500 = 120, margin 20000/(500 x 25%) = 160).
    # Buy fills at the 10:00 bar open: 500.00 x 1.0003 = 500.15 -> value 10003.00.
    #   Charges (shoonya MIS): brokerage min(5, 3.0009) 3.00, txn 0.30, SEBI 0.01,
    #   stamp 0.30, GST 18% x 3.3079921 = 0.60 -> 4.21.
    # Sell fills at the 11:00 bar open: 510.00 x 0.9997 = 509.847 -> value 10196.94.
    #   Charges: brokerage 3.06, STT 2.55, txn 0.30, SEBI 0.01, GST 0.61 -> 6.53.
    # Gross 20 x (510 - 500) = 200.00; slippage 20 x (0.15 + 0.153) = 6.06;
    # net = 200.00 - 6.06 - 10.74 = 183.20.
    bars = session_frame("X", DAY, 1, lambda t: 500.0 if t < ts(DAY, "10:30") else 510.0)
    strat = ScriptedStrategy(
        MIS,
        "1m",
        {
            ts(DAY, "10:00"): [entry("X", Side.BUY, stop=495.0)],
            ts(DAY, "11:00"): [exit_("X")],
        },
    )
    result, bt = run_frames(strat, bars, [DAY])
    (trade,) = bt.portfolio.trades
    assert (trade.qty, trade.entry_price, trade.exit_price) == (20, D("500.15"), D("509.847"))
    assert (trade.gross_pnl, trade.slippage, trade.costs) == (D(200), D("6.06"), D("10.74"))
    assert trade.net_pnl == D("183.20")
    assert (trade.entry_time, trade.exit_time) == (ts(DAY, "10:00"), ts(DAY, "11:00"))
    assert trade.exit_reason == "strategy"
    assert bt.portfolio.ledger == D("20183.20")
    row = result.trades.iloc[0]
    assert row["net_pnl"] == pytest.approx(183.20) and row["exit_reason"] == "strategy"
    assert result.equity["equity"].tolist() == pytest.approx([20183.20])


def test_fill_becomes_visible_only_after_its_bar_completes():
    bars = session_frame("X", DAY, 1, 500.0)
    strat = ScriptedStrategy(MIS, "1m", {ts(DAY, "10:00"): [entry("X", Side.BUY, stop=495.0)]})
    run_frames(strat, bars, [DAY])
    seen = {c.now: c for c in strat.seen}
    at_10, at_1001 = seen[ts(DAY, "10:00")], seen[ts(DAY, "10:01")]
    assert not at_10.positions and not at_10.fills_today
    assert len(at_10.bars("X")) == 45  # 09:15 .. 09:59
    assert at_1001.positions["X"].qty == 20 and len(at_1001.fills_today) == 1
    assert at_1001.bars("X").ts[-1] == ts(DAY, "10:00")


def test_forced_exit_at_the_open_of_the_1450_bar():
    bars = session_frame("X", DAY, 5, 500.0, overrides={"14:50": (503.0, 503.5, 502.5, 503.0)})
    strat = ScriptedStrategy(
        MIS,
        "5m",
        {
            ts(DAY, "10:00"): [entry("X", Side.BUY, stop=495.0)],
            ts(DAY, "14:55"): [entry("X", Side.BUY, stop=495.0)],
        },
    )
    result, bt = run_frames(strat, bars, [DAY])
    (trade,) = bt.portfolio.trades
    assert trade.exit_reason == "flat_by"
    assert trade.exit_time == ts(DAY, "14:50")
    assert trade.exit_ref == D("503.0") and trade.exit_price == D("503.0") * D("0.9997")
    assert not bt.portfolio.positions and not working(bt)
    assert reasons(result) == ["AFTER_ENTRY_END"]
    assert result.fallback_exits == 0


def test_no_orders_on_a_no_trade_day():
    bars = session_frame("X", DAY, 5, 500.0)
    strat = ScriptedStrategy(MIS, "5m", {ts(DAY, "10:00"): [entry("X", Side.BUY, stop=495.0)]})
    result, bt = run_frames(strat, bars, [DAY], no_trade=(DAY,))
    assert reasons(result) == ["NO_TRADE_SESSION"]
    assert not bt.broker.orders() and not bt.portfolio.trades
    assert strat.seen[0].session_no_trade


def test_oco_group_with_a_rejected_leg_leaves_nothing_working():
    bars = session_frame("X", DAY, 5, 500.0)
    good = entry("X", Side.BUY, order_type=OrderType.STOP, price=505.0, stop=500.0, group="g")
    bad = entry("X", Side.SELL, order_type=OrderType.STOP, price=495.0, stop=490.0, group="g")
    strat = ScriptedStrategy(MIS, "5m", {ts(DAY, "10:00"): [good, bad]})
    result, bt = run_frames(strat, bars, [DAY])
    assert reasons(result) == ["INVALID_STOP", "GROUP_LEG_REJECTED"]
    assert not working(bt) and not bt.portfolio.trades
    cancelled = [e for e in bt.broker.events if e.status is OrderStatus.CANCELLED]
    assert cancelled[0].reason == "OCO group leg rejected"


def test_oco_group_fills_one_leg_and_cancels_the_other():
    bars = session_frame("X", DAY, 5, 500.0, overrides={"10:30": (501.0, 506.0, 500.5, 505.0)})
    buy = entry("X", Side.BUY, order_type=OrderType.STOP, price=505.0, stop=490.0, group="g")
    sell = entry("X", Side.SELL, order_type=OrderType.STOP, price=495.0, stop=500.0, group="g")
    strat = ScriptedStrategy(MIS, "5m", {ts(DAY, "10:00"): [buy, sell]})
    _, bt = run_frames(strat, bars, [DAY])
    (trade,) = bt.portfolio.trades
    assert (trade.side, trade.entry_ref, trade.group_id) == ("long", D("505.0"), "g")
    assert trade.exit_reason == "flat_by"


def test_record_mode_keeps_trading_and_reports_when_the_halt_would_fire():
    day2 = date(2024, 1, 3)
    crash = session_frame("X", DAY, 5, 500.0, overrides={"10:30": (300.0, 300.5, 299.5, 300.0)})
    after = session_frame("X", day2, 5, 300.0)
    bars = pd.concat([crash, after], ignore_index=True)
    strat = ScriptedStrategy(
        MIS,
        "5m",
        {
            ts(DAY, "10:00"): [entry("X", Side.BUY, stop=495.0)],
            ts(day2, "10:00"): [entry("X", Side.BUY, stop=297.0)],
        },
    )
    result, bt = run_frames(strat, bars, [DAY, day2])
    assert result.halt is not None and result.halt.date == DAY
    assert result.halt.drawdown_pct == pytest.approx(20.0, abs=0.2)  # gap to 300 on 20 shares
    assert len(bt.portfolio.trades) == 2  # still trading on day 2


def test_latch_mode_stops_new_entries():
    day2 = date(2024, 1, 3)
    crash = session_frame("X", DAY, 5, 500.0, overrides={"10:30": (300.0, 300.5, 299.5, 300.0)})
    bars = pd.concat([crash, session_frame("X", day2, 5, 300.0)], ignore_index=True)
    strat = ScriptedStrategy(
        MIS,
        "5m",
        {
            ts(DAY, "10:00"): [entry("X", Side.BUY, stop=495.0)],
            ts(day2, "10:00"): [entry("X", Side.BUY, stop=297.0)],
        },
    )
    result, bt = run_frames(strat, bars, [DAY, day2], mode="paper")
    assert reasons(result) == ["DRAWDOWN_HALT"] and len(bt.portfolio.trades) == 1


# --- swing ---

D0, D1, D2, D3, D4 = (date(2024, 1, d) for d in (1, 2, 3, 4, 5))


def _daily(symbol: str, price: float, days=(D0, D1, D2, D3, D4)) -> pd.DataFrame:
    return daily_frame(symbol, {d: (price, price + 1, price - 1, price) for d in days})


def test_swing_decision_fills_next_open_and_skips_no_trade_days():
    bars = _daily("A", 100.0)
    strat = ScriptedStrategy(
        CNC,
        "1d",
        {
            ts(D0, "15:30"): [entry("A", Side.BUY, product=CNC, rank=1)],
            ts(D1, "15:30"): [exit_("A", product=CNC)],  # D2 is no_trade -> fills D3
        },
    )
    result, bt = run_frames(strat, bars, [D0, D1, D2, D3, D4], no_trade=(D2,))
    (trade,) = bt.portfolio.trades
    assert trade.qty == 49  # floor(0.99 x ((20000 - 23.76) / 4) / 100)
    assert (trade.entry_time, trade.exit_time) == (ts(D1, "09:15"), ts(D3, "09:15"))
    assert trade.exit_reason == "strategy"
    assert len(strat.seen[1].bars("A")) == 2  # D0 and D1 visible at D1 15:30
    assert len(result.equity) == 5


def test_context_next_session_is_the_next_calendar_session():
    # The calendar (exchange holiday list) is known in advance; no_trade days are sessions.
    strat = ScriptedStrategy(CNC, "1d", {})
    run_frames(strat, _daily("A", 100.0, days=(D0, D1, D2, D3)), [D0, D1, D2, D3], no_trade=(D2,))
    assert [(c.session_date, c.next_session, c.next_tradeable_session) for c in strat.seen] == [
        (D0, D1, D1),
        (D1, D2, D3),
        (D2, D3, D3),
        (D3, None, None),
    ]


@pytest.mark.parametrize(("buffer_pct", "rejected"), [(1, []), (0, ["D"])])
def test_cash_buffer_absorbs_a_one_pct_opening_gap(buffer_pct, rejected):
    # Four buys at a 50 close fill the account; the next open gaps up 1% to 50.5.
    # Without the buffer: 99 shares each, ~5,007 with slippage and charges, so the
    # fourth buy is short of cash. With 1%: 98 shares each, ~4,956.
    names = ("A", "B", "C", "D")
    rows = {D0: (50, 51, 49, 50), D1: (50.5, 51, 50, 50.5), D2: (50.5, 51, 50, 50.5)}
    bars = pd.concat([daily_frame(s, rows) for s in names], ignore_index=True)
    buys = [entry(s, Side.BUY, product=CNC, rank=i) for i, s in enumerate(names, start=1)]
    strat = ScriptedStrategy(CNC, "1d", {ts(D0, "15:30"): buys})
    result, bt = run_frames(strat, bars, [D0, D1, D2], swing={"cash_buffer_pct": buffer_pct})
    cash = result.rejections[result.rejections["reason"] == "INSUFFICIENT_CASH"]
    assert list(cash["symbol"]) == rejected
    qty = 98 if buffer_pct else 99
    assert {t.qty for t in bt.portfolio.trades} == {qty}
    assert len(bt.portfolio.trades) == 4 - len(rejected)


def test_fills_frame_has_every_fill_with_charges_slippage_and_dp():
    bars = _daily("A", 100.0)
    strat = ScriptedStrategy(
        CNC,
        "1d",
        {
            ts(D0, "15:30"): [entry("A", Side.BUY, product=CNC, rank=1)],
            ts(D1, "15:30"): [exit_("A", product=CNC)],
        },
    )
    result, bt = run_frames(strat, bars, [D0, D1, D2])
    (trade,) = bt.portfolio.trades
    f = result.fills
    assert list(f["side"]) == ["BUY", "SELL"] and list(f["role"]) == ["ENTRY", "EXIT"]
    assert list(f["session_date"]) == [D1, D2] and list(f["qty"]) == [49, 49]
    assert f["price"].tolist() == pytest.approx([100.03, 99.97])
    assert f["value"].tolist() == pytest.approx([100.03 * 49, 99.97 * 49])
    assert f["dp_charge"].tolist() == [0.0, 9.0]  # shoonya, before GST, on the sale
    assert f["charges"].sum() == pytest.approx(float(trade.costs))
    assert f["slippage"].sum() == pytest.approx(float(trade.slippage))
    assert f["exit_reason"].isna().tolist() == [True, False]
    assert f["exit_reason"].iloc[1] == "strategy"


def test_swing_skips_unaffordable_rank_and_takes_the_next():
    bars = pd.concat([_daily("A", 7000.0), _daily("B", 100.0), _daily("C", 50.0)])
    picks = [
        entry("C", Side.BUY, product=CNC, rank=3),
        entry("A", Side.BUY, product=CNC, rank=1),
        entry("B", Side.BUY, product=CNC, rank=2),
    ]
    strat = ScriptedStrategy(CNC, "1d", {ts(D0, "15:30"): picks})
    result, bt = run_frames(strat, bars, [D0, D1, D2], swing={"max_positions": 2})
    rej = result.rejections.iloc[0]
    assert (rej["symbol"], rej["reason"], rej["price"], rej["rank"]) == (
        "A",
        "PRICE_ABOVE_POSITION_CAP",
        7000.0,
        1,
    )
    assert {t.symbol for t in bt.portfolio.trades} == {"B", "C"}  # closed at end of run


def test_swing_open_position_is_closed_at_the_end_of_the_run():
    bars = _daily("A", 100.0)
    strat = ScriptedStrategy(CNC, "1d", {ts(D0, "15:30"): [entry("A", Side.BUY, product=CNC)]})
    result, bt = run_frames(strat, bars, [D0, D1, D2])
    (trade,) = bt.portfolio.trades
    assert trade.exit_reason == "end_of_run" and not bt.portfolio.positions
    assert result.equity["equity"].iloc[-1] == pytest.approx(float(bt.portfolio.ledger))


@pytest.mark.parametrize(
    ("product", "timeframe", "message"),
    [
        (MIS, "15m", "not on the 15m bar grid"),
        (MIS, "1d", "intraday timeframe"),
        (CNC, "5m", "daily bars"),
        (MIS, "2m", "unknown timeframe"),
    ],
)
def test_invalid_strategy_setups(product, timeframe, message):
    with pytest.raises(ValueError, match=message):
        validate_strategy(ScriptedStrategy(product, timeframe, {}), risk_config())
