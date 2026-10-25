from datetime import date

import pandas as pd
import pytest

from nsealgo.data.calendar import (
    IST,
    build_calendar,
    classify_short_sessions,
    full_sessions,
    load_holidays,
    tradeable_sessions,
)
from nsealgo.data.config import load_data_config
from nsealgo.data.raw import normalize, read_raw
from nsealgo.settings import REPO_ROOT

RAW_CSV = """date,open,high,low,close,volume
2015-12-31 09:15:00,1,1,1,1,1
2016-01-01 09:14:00,1,1,1,1,1
2016-01-01 09:15:00,10,11,9,10,100
2016-01-01 09:15:30,10,11,9,10,100
2016-01-01 15:29:00,10,11,9,10,100
2016-01-01 15:30:00,10,11,9,10,100
2016-01-02 18:15:00,10,11,9,10,100
2016-01-04 09:15:00,10,11,9,10,100
"""


@pytest.fixture
def raw(tmp_path) -> pd.DataFrame:
    (tmp_path / "X_minute.csv").write_text(RAW_CSV)
    return read_raw(tmp_path, "X")


def test_read_raw_localizes_to_ist(raw):
    assert str(raw["ts"].dt.tz) == "Asia/Kolkata"
    assert raw["ts"].iloc[2] == pd.Timestamp("2016-01-01 09:15", tz=IST)


def test_normalize_keeps_regular_session_in_range(raw):
    n = normalize(raw, "X", date(2016, 1, 1), date(2016, 1, 3), excluded={date(2016, 1, 2)})
    assert list(n.bars["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")) == [
        "2016-01-01 09:15:00",
        "2016-01-01 15:29:00",
    ]
    assert list(n.bars.columns[:3]) == ["ts", "symbol", "session_date"]
    assert n.out_of_session["n_rows"].sum() == 2  # 09:14 and 15:30
    assert n.off_grid["n_rows"].sum() == 1  # 09:15:30
    # raw counts include the excluded session, so it can be listed as short
    assert dict(
        zip(n.raw_session_bars["session_date"], n.raw_session_bars["n_raw_bars"], strict=True)
    ) == {
        date(2016, 1, 1): 5,
        date(2016, 1, 2): 1,
    }


def test_normalize_rejects_duplicates(raw):
    dup = pd.concat([raw, raw.iloc[[2]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        normalize(dup, "X", date(2016, 1, 1), date(2016, 1, 4), excluded=set())


def _session_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["A", "B", "A", "B"],
            "session_date": [date(2021, 2, 23)] * 2 + [date(2021, 2, 24)] * 2,
            "n_bars": [375, 374, 149, 140],
        }
    )


def test_calendar_marks_no_trade_and_tradeable_sessions_exclude_it():
    cal = build_calendar(_session_bars(), {date(2021, 2, 24): "nse_outage"}, set())
    assert list(cal["max_bars"]) == [375, 149]
    assert list(cal["no_trade"]) == [False, True]
    assert tradeable_sessions(cal) == [date(2021, 2, 23)]


def test_calendar_rejects_holiday_with_data():
    with pytest.raises(ValueError, match="holidays"):
        build_calendar(_session_bars(), {}, {date(2021, 2, 23)})


def test_short_sessions_classified_and_full_excluded_session_rejected():
    raw = _session_bars().rename(columns={"n_bars": "n_raw_bars"})
    short = classify_short_sessions(raw, {}, {date(2021, 2, 24): "nse_outage"}, 300)
    assert short.to_dict("records") == [
        {
            "session_date": date(2021, 2, 24),
            "max_raw_bars": 149,
            "status": "no_trade",
            "reason": "nse_outage",
        }
    ]
    with pytest.raises(ValueError, match="full data"):
        classify_short_sessions(raw, {date(2021, 2, 23): "muhurat"}, {}, 300)


def test_repo_configs_load():
    cfg = load_data_config()
    assert cfg.clean_start == date(2016, 1, 1)
    assert cfg.clean_end == date(2026, 4, 7)
    assert date(2025, 10, 21) in cfg.excluded()
    assert cfg.no_trade() == {
        date(2017, 7, 10): "nse_outage",
        date(2021, 2, 24): "nse_outage",
        date(2021, 2, 25): "prev_session_outage_close",
    }
    assert load_holidays(REPO_ROOT / "config" / "holidays.csv") == set()


def test_day_after_early_close_outage_is_no_trade_but_full():
    cfg = load_data_config()
    bars = pd.DataFrame(
        {
            "symbol": ["A", "A", "A"],
            "session_date": [date(2021, 2, 23), date(2021, 2, 24), date(2021, 2, 25)],
            "n_bars": [375, 149, 375],
        }
    )
    cal = build_calendar(bars, cfg.no_trade(), set()).set_index("session_date")
    after = date(2021, 2, 25)
    assert cal.at[after, "no_trade"]
    assert cal.at[after, "no_trade_reason"] == "prev_session_outage_close"
    assert tradeable_sessions(cal.reset_index()) == [date(2021, 2, 23)]
    # Still a full session: it stays in volume-average windows; the outage day does not.
    assert full_sessions(cal.reset_index(), 300) == [date(2021, 2, 23), after]
