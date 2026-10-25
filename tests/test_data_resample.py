from datetime import date

import pandas as pd
import pytest

from nsealgo.data.calendar import IST
from nsealgo.data.resample import resample_bars, with_available_at
from tests.data_helpers import session_bars

DAY = date(2024, 1, 3)


def ist(hhmmss: str, day: date = DAY) -> pd.Timestamp:
    return pd.Timestamp(f"{day.isoformat()} {hhmmss}", tz=IST)


def test_first_15m_bar_covers_0915_to_092959_and_is_available_at_0930():
    bars = session_bars("X", DAY)
    out = resample_bars(bars, 15)
    first = out.iloc[0]
    assert first["ts"] == ist("09:15:00")
    assert first["available_at"] == ist("09:30:00")
    assert first["n_bars"] == 15
    # Exactly the 1m bars starting 09:15..09:29, so the data ends by 09:29:59.
    inside = bars[(bars["ts"] >= ist("09:15:00")) & (bars["ts"] < ist("09:30:00"))]
    assert inside["ts"].max() + pd.Timedelta(minutes=1) - pd.Timedelta(seconds=1) == ist("09:29:59")
    assert first["open"] == inside["open"].iloc[0]
    assert first["high"] == inside["high"].max()
    assert first["low"] == inside["low"].min()
    assert first["close"] == inside["close"].iloc[-1]
    assert first["volume"] == inside["volume"].sum()
    # The 09:30 1m bar starts the second bar, not the first.
    assert out.iloc[1]["ts"] == ist("09:30:00")


@pytest.mark.parametrize(("minutes", "count", "last"), [(5, 75, "15:25:00"), (15, 25, "15:15:00")])
def test_full_session_bucket_count_and_last_bar(minutes, count, last):
    out = resample_bars(session_bars("X", DAY), minutes)
    assert len(out) == count
    assert (out["n_bars"] == minutes).all()
    assert out.iloc[-1]["ts"] == ist(last)
    assert out.iloc[-1]["available_at"] == ist("15:30:00")
    assert out["ts"].dt.tz is not None


def test_buckets_never_cross_sessions_and_symbols():
    d2 = date(2024, 1, 4)
    bars = pd.concat(
        [session_bars("A", DAY), session_bars("A", d2, base=200), session_bars("B", DAY, base=50)]
    )
    out = resample_bars(bars.sample(frac=1, random_state=1), 15)  # unsorted input
    assert len(out) == 75
    a2 = out[(out["symbol"] == "A") & (out["session_date"] == d2)].iloc[0]
    assert a2["ts"] == ist("09:15:00", d2)
    assert a2["open"] == pytest.approx(200.0)


def test_missing_minutes_are_aggregated_without_filling():
    bars = session_bars("X", DAY)
    bars = bars[~bars["ts"].between(ist("09:16:00"), ist("09:29:00"))]  # only 09:15 left
    out = resample_bars(bars, 15)
    assert out.iloc[0]["n_bars"] == 1
    assert out.iloc[0]["close"] == bars.iloc[0]["close"]


def test_rejects_length_that_does_not_divide_session():
    with pytest.raises(ValueError):
        resample_bars(session_bars("X", DAY), 7)


def test_1m_available_at_is_one_minute_after_start():
    out = with_available_at(session_bars("X", DAY), 1)
    assert (out["available_at"] - out["ts"] == pd.Timedelta(minutes=1)).all()
