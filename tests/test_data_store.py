from datetime import date

import pandas as pd
import pytest

from nsealgo.data.calendar import IST, build_calendar
from nsealgo.data.features import daily_bars, daily_features, rvol_profile
from nsealgo.data.resample import resample_bars, with_available_at
from nsealgo.data.store import connect, write_bars, write_calendar, write_symbol_table
from tests.data_helpers import business_days, many_sessions

DAYS = business_days("2023-12-01", 25)  # spans a year boundary


@pytest.fixture
def con(tmp_path):
    bars = many_sessions("X", DAYS)
    write_bars(with_available_at(bars, 1), tmp_path, "1m")
    for m in (5, 15):
        write_bars(resample_bars(bars, m), tmp_path, f"{m}m")
    daily = daily_bars(bars)
    write_symbol_table(daily_features(daily, DAYS), tmp_path, "features")
    write_symbol_table(rvol_profile(resample_bars(bars, 5), DAYS), tmp_path, "rvol")
    write_calendar(build_calendar(daily[["symbol", "session_date", "n_bars"]], {}, set()), tmp_path)
    return connect(tmp_path)


def test_views_round_trip_counts_and_partitions(con, tmp_path):
    assert con.execute("SELECT count(*) FROM bars_1m").fetchone()[0] == 25 * 375
    assert con.execute("SELECT count(*) FROM bars_5m").fetchone()[0] == 25 * 75
    assert con.execute("SELECT count(*) FROM bars_15m").fetchone()[0] == 25 * 25
    assert con.execute("SELECT count(*) FROM calendar").fetchone()[0] == 25
    assert (tmp_path / "1m" / "symbol=X" / "year=2024").is_dir()


def test_timestamps_stay_tz_aware_ist(con):
    df = con.sql("SELECT ts, available_at, session_date FROM bars_15m ORDER BY ts LIMIT 1").df()
    assert str(df["ts"].dt.tz) == "Asia/Kolkata"
    assert df.at[0, "ts"] == pd.Timestamp("2023-12-01 09:15", tz=IST)
    assert df.at[0, "available_at"] == pd.Timestamp("2023-12-01 09:30", tz=IST)
    assert df.at[0, "session_date"] == pd.Timestamp(date(2023, 12, 1))


def test_rvol_view_joins_on_bucket_start(con):
    df = con.sql(
        "SELECT * FROM bars_5m_rvol WHERE session_date = DATE '2023-12-29' ORDER BY ts"
    ).df()
    assert len(df) == 75
    assert df["avg_volume_20d"].notna().all()
    assert (df["rvol"] - df["volume"] / df["avg_volume_20d"]).abs().max() < 1e-9


def test_connect_requires_built_store(tmp_path):
    with pytest.raises(FileNotFoundError):
        connect(tmp_path)
