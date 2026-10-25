import numpy as np
import pandas as pd
import pytest

from nsealgo.data.calendar import IST
from nsealgo.data.features import daily_bars, daily_features, rvol_profile
from nsealgo.data.resample import resample_bars
from tests.data_helpers import business_days, many_sessions

DAYS = business_days("2024-01-01", 30)
FEATS = ["prev_high", "prev_low", "prev_close", "atr14", "zero_vol_share_20d"]


def _features(bars: pd.DataFrame) -> pd.DataFrame:
    return daily_features(daily_bars(bars), DAYS, warmup=20, atr_period=14, avg_window=20)


def _rvol(bars: pd.DataFrame) -> pd.DataFrame:
    return rvol_profile(resample_bars(bars, 5), DAYS, window=20)


def _poison_from(bars: pd.DataFrame, k: int) -> pd.DataFrame:
    """Wildly change every bar on session DAYS[k] and later."""
    out = bars.copy()
    later = out["session_date"] >= DAYS[k]
    for col in ("open", "high", "low", "close"):
        out.loc[later, col] *= 3.7
    out.loc[later, "volume"] = np.where(out.loc[later, "volume"].index % 2, 0, 99_999)
    return out


@pytest.fixture(scope="module")
def bars() -> pd.DataFrame:
    b = many_sessions("X", DAYS)
    b.loc[b.index % 50 == 0, "volume"] = 0  # some zero-volume bars
    return b


@pytest.mark.parametrize("k", [20, 21, 25, 29])
def test_feature_on_day_d_never_uses_day_d_or_later(bars, k):
    clean, poisoned = _features(bars), _features(_poison_from(bars, k))
    upto = clean["session_date"] <= DAYS[k]
    pd.testing.assert_frame_equal(clean[upto], poisoned[upto])
    # Sanity: the poison does reach later features, so the test can fail.
    if k < 29:
        assert not clean[~upto].equals(poisoned[~upto])


@pytest.mark.parametrize("k", [20, 25, 29])
def test_rvol_on_day_d_never_uses_day_d_or_later(bars, k):
    clean, poisoned = _rvol(bars), _rvol(_poison_from(bars, k))
    upto = clean["session_date"] <= DAYS[k]
    pd.testing.assert_frame_equal(clean[upto], poisoned[upto])


def test_nan_until_warmup_then_values(bars):
    f = _features(bars)
    early = f["prior_sessions"] < 20
    assert early.sum() == 20
    assert f.loc[early, FEATS].isna().all().all()
    assert f.loc[~early, FEATS].notna().all().all()


def test_values_match_hand_computation(bars):
    d = daily_bars(bars).set_index("session_date")
    f = _features(bars).set_index("session_date")
    day, prev = DAYS[25], DAYS[24]
    assert f.at[day, "prev_high"] == d.at[prev, "high"]
    assert f.at[day, "prev_low"] == d.at[prev, "low"]
    assert f.at[day, "prev_close"] == d.at[prev, "close"]
    tr = [
        max(
            d.at[DAYS[i], "high"] - d.at[DAYS[i], "low"],
            abs(d.at[DAYS[i], "high"] - d.at[DAYS[i - 1], "close"]),
            abs(d.at[DAYS[i], "low"] - d.at[DAYS[i - 1], "close"]),
        )
        for i in range(11, 25)
    ]
    assert f.at[day, "atr14"] == pytest.approx(np.mean(tr))
    window = d.loc[DAYS[5] : DAYS[24]]
    share = window["zero_vol_bars"].sum() / window["n_bars"].sum()
    assert f.at[day, "zero_vol_share_20d"] == pytest.approx(share)
    assert f.at[day, "available_at"] == pd.Timestamp(f"{day} 09:15", tz=IST)


def test_missing_session_gives_nan_not_fill(bars):
    gap = DAYS[22]
    f = _features(bars[bars["session_date"] != gap]).set_index("session_date")
    assert gap not in f.index
    nxt = DAYS[23]
    assert np.isnan(f.at[nxt, "prev_close"])  # previous calendar session is missing
    assert np.isnan(f.at[nxt, "atr14"])
    assert np.isnan(f.at[DAYS[29], "zero_vol_share_20d"])  # 20-session window still spans gap


def test_rvol_matches_mean_of_prior_20_sessions(bars):
    b5 = resample_bars(bars, 5)
    r = _rvol(bars)
    row = r[(r["session_date"] == DAYS[25]) & (r["tod"] == "10:00")].iloc[0]
    prior = b5[(b5["ts"].dt.strftime("%H:%M") == "10:00") & (b5["session_date"] >= DAYS[5])]
    prior = prior[prior["session_date"] <= DAYS[24]]
    assert len(prior) == 20
    assert row["avg_volume_20d"] == pytest.approx(prior["volume"].mean())
    assert row["ts"] == pd.Timestamp(f"{DAYS[25]} 10:00", tz=IST)
    assert r[r["session_date"] < DAYS[20]]["avg_volume_20d"].isna().all()


def test_rvol_skips_sessions_left_out_of_the_window(bars):
    keep = [d for d in DAYS if d != DAYS[10]]
    r = rvol_profile(resample_bars(bars, 5), keep, window=20)
    assert DAYS[10] not in set(r["session_date"])
    assert r[r["session_date"] == DAYS[21]]["avg_volume_20d"].notna().all()
