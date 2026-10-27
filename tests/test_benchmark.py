"""Equal-weight buy-and-hold benchmark and single-symbol attribution (reporting only)."""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from nsealgo.costs import fill_charges
from nsealgo.reporting.benchmark import buy_and_hold, symbol_contribution, without_symbols
from tests.engine_helpers import cost_config

D = Decimal
D0, D1, D2 = date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)


def bars(rows: dict[str, dict[date, tuple[float, float]]]) -> pd.DataFrame:
    """Daily bars from {symbol: {day: (open, close)}}."""
    return pd.DataFrame(
        [
            {"symbol": s, "session_date": d, "open": o, "close": c}
            for s, days in rows.items()
            for d, (o, c) in days.items()
        ]
    )


def hold(frame: pd.DataFrame, capital: float = 20000.0, bps: str = "3") -> pd.DataFrame:
    cfg = cost_config()
    return buy_and_hold(frame, capital, cfg.rates, cfg.broker.delivery, D(bps))


# --- buy and hold ---


def test_equal_weight_fractional_buy_at_the_first_open_with_buy_costs():
    frame = bars(
        {
            "A": {D0: (100.0, 110.0), D1: (110.0, 120.0), D2: (120.0, 90.0)},
            "B": {D0: (40.0, 40.0), D1: (40.0, 44.0), D2: (44.0, 50.0)},
        }
    )
    eq = hold(frame)
    cfg = cost_config()
    charges = fill_charges("CNC", "BUY", D(10000), cfg.rates, cfg.broker.delivery).total
    value = 10000 - float(charges)  # each symbol's share, less its buy charges
    qty_a, qty_b = value / (100 * 1.0003), value / (40 * 1.0003)
    cash = 2 * (10000 - value) - 2 * float(
        fill_charges("CNC", "BUY", D(str(value)), cfg.rates, cfg.broker.delivery).total
    )
    assert 0 <= cash < 0.05  # a few paise left over
    assert list(eq["session_date"]) == [D0, D1, D2]
    expected = [cash + qty_a * a + qty_b * b for a, b in ((110, 40), (120, 44), (90, 50))]
    assert eq["equity"].tolist() == pytest.approx(expected)
    # No rebalancing: A's weight drifts with its price.
    assert qty_a * 120 / (qty_a * 120 + qty_b * 44) > 0.5


def test_costs_come_out_of_the_capital():
    frame = bars({"A": {D0: (100.0, 100.0)}})
    free = hold(frame, bps="0")["equity"].iloc[0]
    paid = hold(frame)["equity"].iloc[0]
    assert free < 20000 and paid < free  # charges, then charges + 3 bps slippage
    assert 20000 - paid == pytest.approx(20000 * (0.0012 + 0.0003), rel=0.1)


def test_a_missing_bar_marks_at_the_last_close():
    frame = bars(
        {
            "A": {D0: (100.0, 100.0), D1: (100.0, 100.0), D2: (100.0, 100.0)},
            "B": {D0: (50.0, 50.0), D2: (50.0, 60.0)},
        }
    )
    eq = hold(frame, bps="0")["equity"].tolist()
    assert eq[0] == pytest.approx(eq[1])  # B carried at 50 on D1
    assert eq[2] > eq[1]


def test_every_symbol_needs_a_bar_on_the_first_session():
    frame = bars({"A": {D0: (100.0, 100.0), D1: (100.0, 100.0)}, "B": {D1: (50.0, 50.0)}})
    with pytest.raises(ValueError, match="B"):
        hold(frame)


# --- removing one symbol's trades from a run ---


def fills() -> pd.DataFrame:
    rows = [
        ("X", "BUY", 10, D0, 1000.0, 1.0),  # 10 at 100
        ("Y", "BUY", 5, D0, 500.0, 0.5),
        ("X", "SELL", 10, D1, 1200.0, 1.2),  # 10 at 120
    ]
    cols = ["symbol", "side", "qty", "session_date", "value", "charges"]
    return pd.DataFrame(rows, columns=cols)


def closes() -> pd.DataFrame:
    return bars(
        {
            "X": {D0: (100.0, 110.0), D1: (120.0, 130.0), D2: (130.0, 140.0)},
            "Y": {D0: (100.0, 100.0), D1: (100.0, 104.0), D2: (104.0, 108.0)},
        }
    )


def test_symbol_contribution_is_its_cash_flows_plus_its_holding_at_the_close():
    x = symbol_contribution(fills(), closes(), "X", [D0, D1, D2])
    # D0: -1000 - 1 + 10 x 110; D1: sold for 1200 - 1.2; D2: nothing held.
    assert x.tolist() == pytest.approx([99.0, 197.8, 197.8])
    y = symbol_contribution(fills(), closes(), "Y", [D0, D1, D2])
    assert y.tolist() == pytest.approx([-0.5, 19.5, 39.5])


def test_without_symbols_subtracts_their_contribution_from_equity():
    equity = pd.DataFrame({"session_date": [D0, D1, D2], "equity": [20098.5, 20217.3, 20237.3]})
    out = without_symbols(equity, fills(), closes(), ["X"])
    assert out["equity"].tolist() == pytest.approx([19999.5, 20019.5, 20039.5])
    assert list(out["session_date"]) == [D0, D1, D2]
    both = without_symbols(equity, fills(), closes(), ["X", "Y"])
    assert both["equity"].tolist() == pytest.approx([20000.0] * 3)
