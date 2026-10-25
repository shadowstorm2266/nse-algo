from datetime import date

import pandas as pd

from nsealgo.data.quality import (
    bad_print_mask,
    nonpositive_mask,
    ohlc_inconsistent_mask,
    out_of_line_days,
    overnight_moves,
)
from tests.data_helpers import session_bars

DAY = date(2024, 1, 3)


def _bad(bars: pd.DataFrame) -> pd.Series:
    return bad_print_mask(bars, max_dev=0.10, lookaround=5)


def test_nonpositive_rows_detected():
    b = session_bars("X", DAY)
    b.loc[[3, 7], "low"] = 0.0
    b.loc[9, "close"] = -1.0
    assert list(b.index[nonpositive_mask(b)]) == [3, 7, 9]


def test_ohlc_inconsistency_detected():
    b = session_bars("X", DAY)
    b.loc[5, "high"] = b.loc[5, "close"] - 1
    b.loc[6, "low"] = b.loc[6, "open"] + 1
    assert list(b.index[ohlc_inconsistent_mask(b)]) == [5, 6]


def test_single_bar_spike_is_bad_print():
    b = session_bars("X", DAY)
    b.loc[100, ["high", "close"]] = 400.0
    assert list(b.index[_bad(b)]) == [100]


def test_spike_on_first_and_last_bar_of_session():
    b = session_bars("X", DAY)
    b.loc[0, ["open", "high"]] = 555.0
    b.loc[374, ["high", "close"]] = 2136.0
    assert list(b.index[_bad(b)]) == [0, 374]


def test_genuine_sustained_jump_is_not_bad_print():
    b = session_bars("X", DAY)
    later = b.index >= 200
    for col in ("open", "high", "low", "close"):
        b.loc[later, col] *= 1.25
    b.loc[200, ["open", "low"]] = b.loc[199, "close"]  # jump bar opens at the old level
    assert not _bad(b).any()


def test_overnight_move_and_out_of_line():
    daily = pd.DataFrame(
        {
            "session_date": pd.bdate_range("2024-01-01", periods=80).date,
            "open": 100.0,
            "close": 100.0,
        }
    )
    daily.loc[40, ["open", "close"]] = 300.0  # one day way out of line
    moves = overnight_moves(daily, 0.15)
    assert list(moves.index) == [40, 41]
    lines = out_of_line_days(daily, 60, 0.7, 1.4)
    assert list(lines.index) == [40]
