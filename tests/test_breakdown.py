from datetime import date

import pandas as pd
import pytest

from nsealgo.data.calendar import IST
from nsealgo.reporting.breakdown import breakdown, entry_year, yearly_equity


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
    y = yearly_equity(eq, 20_000.0)
    assert y.loc[2016, "total_return_pct"] == pytest.approx(-0.5)
    assert y.loc[2016, "max_drawdown_rs"] == pytest.approx(200.0)
    assert y.loc[2017, "total_return_pct"] == pytest.approx(5.0)  # from 19,900
    assert y.loc[2017, "sessions"] == 1
