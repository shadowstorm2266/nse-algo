from datetime import date

import pandas as pd
import pytest

from nsealgo.data.calendar import IST
from nsealgo.reporting.breakdown import (
    breakdown,
    cap_skips,
    entry_year,
    holding_days,
    legs_from_fills,
    legs_from_trades,
    yearly_activity,
    yearly_equity,
)


def _trades() -> pd.DataFrame:
    rows = [
        # trade_id, symbol, side, entry_time, gross, slippage, costs, net, notional
        (1, "AAA", "long", "2016-03-01 10:00", 30.0, 2.0, 3.0, 25.0, 10_000.0),
        (2, "AAA", "short", "2016-06-01 10:00", -20.0, 2.0, 3.0, -25.0, 10_000.0),
        (3, "BBB", "long", "2017-01-02 10:00", 10.0, 1.0, 1.0, 8.0, 5_000.0),
        (3, "BBB", "long", "2017-01-02 10:00", 5.0, 1.0, 2.0, 2.0, 5_000.0),  # partial exit
    ]
    cols = ["trade_id", "symbol", "side", "entry_time", "gross_pnl", "slippage", "costs"]
    df = pd.DataFrame(rows, columns=[*cols, "net_pnl", "notional"])
    df["entry_time"] = pd.to_datetime(df["entry_time"]).dt.tz_localize(IST)
    return df


def test_breakdown_by_year_side_and_symbol():
    t = _trades()
    by_year = breakdown(t, entry_year(t))
    assert list(by_year.index) == [2016, 2017]
    assert list(by_year["trades"]) == [2, 1]  # the partial exits are one trade
    assert by_year.loc[2016, "win_rate"] == 0.5 and by_year.loc[2016, "profit_factor"] == 1.0
    assert by_year.loc[2017, "net_pnl"] == 10.0
    assert by_year.loc[2017, "net_expectancy_bps"] == pytest.approx(10.0)  # 10 / 10,000
    by_side = breakdown(t, "side")
    assert list(by_side.index) == ["long", "short"] and list(by_side["trades"]) == [2, 1]
    assert breakdown(t, "symbol").loc["AAA", "net_pnl"] == 0.0


def test_yearly_equity_starts_each_year_from_the_last_close():
    eq = pd.DataFrame(
        {
            "session_date": [date(2016, 1, 4), date(2016, 1, 5), date(2017, 1, 2)],
            "equity": [20_100.0, 19_900.0, 20_895.0],
        }
    )
    y = yearly_equity(eq, 20_000.0, fixed_capital=False)
    assert y.loc[2016, "total_return_pct"] == pytest.approx(-0.5)
    assert y.loc[2016, "max_drawdown_rs"] == pytest.approx(200.0)
    assert y.loc[2017, "total_return_pct"] == pytest.approx(5.0)  # from 19,900
    assert y.loc[2017, "sessions"] == 1
    fixed = yearly_equity(eq, 20_000.0, fixed_capital=True)
    assert fixed.loc[2017, "total_return_pct"] == pytest.approx(4.975)  # 995 over 20,000
    assert fixed.loc[2016, "total_return_pct"] == pytest.approx(-0.5)


def test_yearly_drawdown_over_capital_when_a_year_starts_below_zero():
    eq = pd.DataFrame(
        {
            "session_date": [date(2016, 1, 4), date(2017, 1, 2), date(2017, 1, 3)],
            "equity": [-1_000.0, -500.0, -3_500.0],
        }
    )
    y = yearly_equity(eq, 20_000.0, fixed_capital=True)
    assert y.loc[2016, "max_drawdown_pct"] == pytest.approx(105.0)  # 21,000 of 20,000
    assert y.loc[2017, "max_drawdown_rs"] == pytest.approx(3_000.0)  # peak -500 to -3,500
    assert y.loc[2017, "max_drawdown_pct"] == pytest.approx(15.0)


def _fills() -> pd.DataFrame:
    rows = [
        # ts, side, value, charges, dp_charge, slippage
        ("2016-11-01 09:15", "BUY", 5_000.0, 6.0, 0.0, 1.5),
        ("2016-11-01 09:15", "BUY", 4_000.0, 5.0, 0.0, 1.2),
        ("2016-12-01 09:15", "SELL", 5_500.0, 16.0, 9.0, 1.6),
        ("2017-01-02 09:15", "SELL", 3_800.0, 15.0, 9.0, 1.1),
    ]
    df = pd.DataFrame(rows, columns=["ts", "side", "value", "charges", "dp_charge", "slippage"])
    df["ts"] = pd.to_datetime(df["ts"]).dt.tz_localize(IST)
    return df


def test_yearly_activity_from_fills_is_by_fill_year():
    y = yearly_activity(legs_from_fills(_fills()), 20_000.0)
    assert list(y.index) == [2016, 2017]
    assert y.loc[2016, "buys_rs"] == 9_000.0 and y.loc[2016, "sells_rs"] == 5_500.0
    assert y.loc[2016, "turnover_x"] == pytest.approx(14_500 / 2 / 20_000)
    assert y.loc[2016, "costs_rs"] == pytest.approx(27.0 + 4.3)
    assert y.loc[2016, "costs_pct_capital"] == pytest.approx(31.3 / 20_000 * 100)
    assert y.loc[2017, "dp_rs"] == 9.0 and y.loc[2017, "buys_rs"] == 0.0


def test_legs_from_trades_put_round_trip_costs_on_the_exit():
    t = pd.DataFrame(
        {
            "trade_id": [1, 2],
            "side": ["long", "short"],
            "qty": [10, 5],
            "entry_time": pd.to_datetime(["2016-03-01 10:00", "2016-12-30 10:00"]),
            "exit_time": pd.to_datetime(["2016-03-01 14:00", "2017-01-02 10:00"]),
            "entry_price": [100.0, 200.0],
            "exit_price": [101.0, 190.0],
            "costs": [2.0, 3.0],
            "slippage": [0.5, 0.25],
        }
    )
    y = yearly_activity(legs_from_trades(t), 20_000.0)
    assert y.loc[2016, "buys_rs"] == 1_000.0 and y.loc[2016, "sells_rs"] == 1_010.0 + 1_000.0
    assert y.loc[2017, "buys_rs"] == 950.0 and y.loc[2017, "costs_rs"] == 3.25
    assert y["dp_rs"].isna().all()  # not separable from trades


def test_cap_skips_by_decision_and_holding_days():
    rej = pd.DataFrame(
        {
            "now": pd.to_datetime(["2017-10-31 15:30", "2017-10-31 15:30", "2017-11-30 15:30"]),
            "symbol": ["MARUTI", "X", "MARUTI"],
            "reason": ["PRICE_ABOVE_POSITION_CAP", "MAX_POSITIONS", "PRICE_ABOVE_POSITION_CAP"],
            "price": [8220.0, 10.0, 8300.0],
            "rank": [2, 5, 3],
        }
    )
    skips = cap_skips(rej)
    assert list(skips["symbol"]) == ["MARUTI", "MARUTI"] and list(skips["rank"]) == [2, 3]
    assert skips["decision"].nunique() == 2
    assert cap_skips(rej.iloc[0:0]).empty
    t = pd.DataFrame(
        {
            "trade_id": [1, 1, 2],
            "entry_time": pd.to_datetime(["2017-01-02", "2017-01-02", "2017-03-01"]),
            "exit_time": pd.to_datetime(["2017-01-12", "2017-02-01", "2017-03-02"]),
        }
    )
    assert holding_days(t).tolist() == [30.0, 1.0]  # last exit of a trade
