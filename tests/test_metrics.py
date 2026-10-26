import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from nsealgo.engine.types import HaltRecord
from nsealgo.reporting.metrics import compute_metrics

CAPITAL = 20000.0


def _trades(rows: list[tuple[int, float, float, float, float]]) -> pd.DataFrame:
    """(trade_id, gross, charges, slippage, notional); net = gross - charges - slippage."""
    df = pd.DataFrame(rows, columns=["trade_id", "gross_pnl", "costs", "slippage", "notional"])
    df["net_pnl"] = df["gross_pnl"] - df["costs"] - df["slippage"]
    df["exit_reason"] = "strategy"
    return df


TRADES = _trades([(1, 120, 15, 5, 10000), (2, -40, 7, 3, 10000), (3, 40, 7, 3, 10000)])
EQUITY = pd.DataFrame(
    {"session_date": [date(2024, 1, d) for d in (1, 2, 3)], "equity": [20100.0, 20050.0, 20080.0]}
)


def test_trade_metrics_by_hand():
    m = compute_metrics(TRADES, EQUITY, CAPITAL)
    assert m["trades"] == 3
    assert m["win_rate"] == pytest.approx(2 / 3)
    assert (m["avg_win"], m["avg_loss"]) == (pytest.approx(65.0), pytest.approx(-50.0))
    assert m["net_expectancy_rs"] == pytest.approx(80 / 3)
    assert m["net_expectancy_bps"] == pytest.approx(80 / 3)  # Rs 10,000 notional: Rs 1 = 1 bp
    assert m["gross_bps_per_trade"] == pytest.approx(40.0)
    assert m["cost_bps_per_trade"] == pytest.approx(40 / 3)  # (20 + 10 + 10) / 3
    assert m["profit_factor"] == pytest.approx(130 / 50)
    assert m["cost_share_of_gross"] == pytest.approx(40 / 120)
    assert (m["net_pnl"], m["charges"], m["slippage"]) == (80.0, 29.0, 11.0)


def test_equity_metrics_from_daily_returns():
    m = compute_metrics(TRADES, EQUITY, CAPITAL)
    eq = np.array([20000.0, 20100.0, 20050.0, 20080.0])
    r = eq[1:] / eq[:-1] - 1
    assert m["sharpe_daily_annualized"] == pytest.approx(r.mean() / r.std(ddof=1) * math.sqrt(252))
    assert m["max_drawdown_rs"] == pytest.approx(50.0)
    assert m["max_drawdown_pct"] == pytest.approx(50 / 20100 * 100)
    assert m["final_equity"] == 20080.0 and m["sessions"] == 3


def test_partial_exits_count_as_one_trade():
    t = _trades([(1, 60, 7, 2, 5000), (1, 60, 8, 3, 5000), (2, -40, 7, 3, 10000)])
    m = compute_metrics(t, EQUITY, CAPITAL)
    assert m["trades"] == 2 and m["win_rate"] == 0.5
    assert m["avg_win"] == pytest.approx(100.0)


def test_empty_and_losing_runs_report_none_not_errors():
    empty = compute_metrics(TRADES.iloc[:0], EQUITY.iloc[:0], CAPITAL)
    assert empty["trades"] == 0 and empty["sharpe_daily_annualized"] is None
    losing = compute_metrics(_trades([(1, -10, 5, 1, 1000)]), EQUITY, CAPITAL)
    assert losing["cost_share_of_gross"] is None  # gross <= 0
    assert losing["profit_factor"] == 0.0
    winning = compute_metrics(_trades([(1, 50, 5, 1, 1000)]), EQUITY, CAPITAL)
    assert winning["profit_factor"] is None  # no losing trades


def test_halt_and_rejection_fields():
    halt = HaltRecord(date(2024, 1, 2), pd.Timestamp("2024-01-02 10:30"), 15.4, 0, 0)
    rej = pd.DataFrame({"reason": ["MAX_TRADES_PER_DAY", "MAX_TRADES_PER_DAY", "KILL_SWITCH"]})
    m = compute_metrics(TRADES, EQUITY, CAPITAL, halt=halt, rejections=rej, fallback_exits=1)
    assert (m["halt_would_fire_date"], m["halt_would_fire_drawdown_pct"]) == ("2024-01-02", 15.4)
    assert m["rejections_by_reason"] == {"MAX_TRADES_PER_DAY": 2, "KILL_SWITCH": 1}
    assert m["fallback_exits"] == 1
    assert compute_metrics(TRADES, EQUITY, CAPITAL)["halt_would_fire_date"] is None
