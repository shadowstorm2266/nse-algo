"""Strategy 1, the 30-minute Opening Range Breakout: known-answer tests on synthetic
sessions run through the real Backtester, and a look-ahead truncation check."""

from datetime import date

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from nsealgo.data.resample import resample_bars
from nsealgo.engine.config import load_strategy_params, merge_params
from nsealgo.engine.types import IntentKind, OrderStatus, OrderType, Side
from nsealgo.strategies import make_strategy
from nsealgo.strategies.orb import OrbStrategy
from tests.data_helpers import business_days, many_sessions
from tests.engine_helpers import run_frames, session_frame, ts

DAY = date(2024, 3, 5)  # a Tuesday
MONDAY = date(2024, 3, 4)
BUY_TRIGGER = 100.5 * 1.0005
SELL_TRIGGER = 99.5 * 0.9995


def orb(**overrides) -> OrbStrategy:
    return OrbStrategy(**load_strategy_params("orb", overrides))


def bars(symbol: str = "AAA", day: date = DAY, **overrides) -> pd.DataFrame:
    """Flat 100 (high/low +/- 0.2) with an opening range of 99.5 .. 100.5 (width 1%)."""
    ohlc = {"09:20": (100.0, 100.5, 99.5, 100.0), **overrides}
    return session_frame(symbol, day, 5, 100.0, spread=0.2, overrides=ohlc)


def feats(symbol: str = "AAA", day: date = DAY, **values) -> pd.DataFrame:
    row = {"prev_high": 101.0, "prev_low": 99.0, "prev_close": 100.0, "atr14": 2.0} | values
    return pd.DataFrame(
        [
            {
                "symbol": symbol,
                "session_date": day,
                "available_at": ts(day, "09:15"),
                "prior_sessions": 30,
                **row,
                "zero_vol_share_20d": 0.0,
            }
        ]
    )


def run(strategy, b, f, days=(DAY,), **risk):
    return run_frames(strategy, b, list(days), features=f, **risk)


def intents(strategy, b, f, **risk):
    result, _ = run(strategy, b, f, **risk)
    return result.intents


# --- parameters ---


def test_yaml_defaults():
    p = orb().params()
    assert p["timeframe"] == "5m" and p["range_minutes"] == 30 and p["buffer_pct"] == 0.05
    assert p["stop"] == "full" and p["target_r"] == 2.0 and p["time_exit"] == "14:30:00"
    assert p["rank_order"] == "narrowest_first"
    f = p["filters"]
    assert f["range_width"] == {"enabled": True, "min_pct": 0.25, "max_pct": 2.5}
    assert f["gap"] == {"enabled": True, "max_abs_pct": 0.8}
    assert not f["prev_day_confluence"]["enabled"] and not f["nifty_direction"]["enabled"]
    assert f["day_of_week"] == {"enabled": False, "skip_weekdays": []}


def test_registry_and_merge():
    s = make_strategy("orb", load_strategy_params("orb", {"filters": {"gap": {"enabled": False}}}))
    assert s.params()["filters"]["gap"] == {"enabled": False, "max_abs_pct": 0.8}
    assert merge_params({"a": {"b": 1, "c": 2}, "d": 3}, {"a": {"b": 9}}) == {
        "a": {"b": 9, "c": 2},
        "d": 3,
    }


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"bogus": 1}, "bogus"),
        ({"stop": "half"}, "stop"),
        ({"filters": {"nifty_direction": {"enabled": True}}}, "not implemented"),
        ({"filters": {"day_of_week": {"enabled": True}}}, "skip_weekdays is empty"),
        ({"filters": {"day_of_week": {"skip_weekdays": [5]}}}, "Friday"),
        ({"filters": {"range_width": {"min_pct": 3.0}}}, "min_pct < max_pct"),
        ({"time_exit": "09:40"}, "time_exit"),
        ({"range_minutes": 32}, "whole number of bars"),
    ],
)
def test_bad_params_rejected(overrides, match):
    with pytest.raises(ValidationError, match=match):
        orb(**overrides)


def test_missing_param_rejected():
    params = load_strategy_params("orb", {})
    del params["buffer_pct"]
    with pytest.raises(ValidationError, match="buffer_pct"):
        OrbStrategy(**params)


# --- entries ---


def test_two_oco_legs_at_range_end_only():
    out = intents(orb(), bars(), feats())
    assert [t for t, _ in out] == [ts(DAY, "09:45")] * 2
    buy, sell = (i for _, i in out)
    assert buy.kind is IntentKind.ENTRY and buy.order_type is OrderType.STOP
    assert buy.side is Side.BUY and sell.side is Side.SELL
    assert buy.price == pytest.approx(BUY_TRIGGER) and buy.stop_loss == 99.5
    assert buy.target == pytest.approx(BUY_TRIGGER + 2 * (BUY_TRIGGER - 99.5))
    assert sell.price == pytest.approx(SELL_TRIGGER) and sell.stop_loss == 100.5
    assert sell.target == pytest.approx(SELL_TRIGGER - 2 * (100.5 - SELL_TRIGGER))
    assert buy.group_id == sell.group_id == "orb-2024-03-05-AAA"
    assert buy.rank == sell.rank == 1


def test_range_ignores_bars_from_0945():
    base = intents(orb(), bars(), feats())
    later = intents(orb(), bars(**{"09:45": (100.0, 100.3, 99.7, 100.0)}), feats())
    assert [i for t, i in later if t == ts(DAY, "09:45")] == [i for _, i in base]
    wider = intents(orb(), bars(**{"09:40": (100.0, 101.0, 99.9, 100.0)}), feats())
    assert wider[0][1].price == pytest.approx(101.0 * 1.0005)


def test_stop_mid_and_target_r():
    buy, sell = (i for _, i in intents(orb(stop="mid", target_r=1.5), bars(), feats()))
    assert buy.stop_loss == sell.stop_loss == 100.0
    assert buy.target == pytest.approx(BUY_TRIGGER + 1.5 * (BUY_TRIGGER - 100.0))
    assert sell.target == pytest.approx(SELL_TRIGGER - 1.5 * (100.0 - SELL_TRIGGER))


@pytest.mark.parametrize(("lo", "hi", "kept"), [(99.9, 100.1, False), (98.5, 101.5, False)])
def test_range_width_filter(lo, hi, kept):
    b = bars(**{"09:20": (100.0, hi, lo, 100.0)})
    b.loc[:, "high"] = b["high"].clip(upper=hi)
    b.loc[:, "low"] = b["low"].clip(lower=lo)
    assert bool(intents(orb(), b, feats())) is kept
    off = orb(filters={"range_width": {"enabled": False}})
    assert len(intents(off, b, feats())) == 2


@pytest.mark.parametrize(("prev_close", "kept"), [(99.0, False), (99.5, True), (np.nan, False)])
def test_gap_filter(prev_close, kept):
    # gap = 100 / prev_close - 1: 1.01% (out), 0.50% (in), unknown (out)
    assert bool(intents(orb(), bars(), feats(prev_close=prev_close))) is kept
    off = orb(filters={"gap": {"enabled": False}})
    assert len(intents(off, bars(), feats(prev_close=prev_close))) == 2


@pytest.mark.parametrize(
    ("prev_high", "prev_low", "sides"),
    [
        (100.4, 99.3, [Side.BUY]),  # long trigger clears PDH, short trigger above PDL
        (101.0, 99.6, [Side.SELL]),
        (100.4, 99.6, [Side.BUY, Side.SELL]),
        (101.0, 99.3, []),
    ],
)
def test_prev_day_confluence(prev_high, prev_low, sides):
    s = orb(filters={"prev_day_confluence": {"enabled": True}})
    out = intents(s, bars(), feats(prev_high=prev_high, prev_low=prev_low))
    assert [i.side for _, i in out] == sides


def test_day_of_week_filter():
    s = orb(filters={"day_of_week": {"enabled": True, "skip_weekdays": [0]}})
    result, _ = run(s, bars(day=MONDAY), feats(day=MONDAY), days=(MONDAY,))
    assert result.intents == []
    assert len(intents(s, bars(), feats())) == 2


def test_skips_without_features_or_a_complete_range():
    assert intents(orb(), bars(), feats().iloc[0:0]) == []
    assert intents(orb(), bars(), feats(atr14=np.nan)) == []
    gap = bars()
    gap = gap[gap["ts"] != ts(DAY, "09:25")]
    assert intents(orb(), gap, feats()) == []


def test_no_trade_session_emits_nothing():
    result, _ = run_frames(orb(), bars(), [DAY], no_trade=(DAY,), features=feats())
    assert result.intents == []


# --- ranking and the skip log ---


def three_symbols():
    b = pd.concat([bars(s) for s in ("AAA", "BBB", "CCC")], ignore_index=True)
    f = pd.concat(
        [feats("AAA", atr14=2.0), feats("BBB", atr14=1.0), feats("CCC", atr14=4.0)],
        ignore_index=True,
    )
    return b, f  # range 1.0, so range / ATR = 0.5, 1.0, 0.25


@pytest.mark.parametrize(
    ("order", "ranked"),
    [("narrowest_first", ["CCC", "AAA", "BBB"]), ("widest_first", ["BBB", "AAA", "CCC"])],
)
def test_rank_by_range_over_atr_and_log_skipped(order, ranked):
    b, f = three_symbols()
    result, _ = run(orb(rank_order=order), b, f)
    ranks = {i.symbol: i.rank for _, i in result.intents}
    assert sorted(ranks, key=ranks.get) == ranked
    # max_trades_per_day is 2: the top two groups were placed and expired unfilled at 14:00
    expired = [(e.symbol, e.ts) for e in result.events if e.status is OrderStatus.EXPIRED]
    assert sorted(expired) == sorted((s, ts(DAY, "14:05")) for s in ranked[:2] for _ in "ls")
    rej = result.rejections
    skipped = rej[rej["reason"] == "MAX_TRADES_PER_DAY"]
    assert list(skipped["symbol"]) == [ranked[2]] and list(skipped["rank"]) == [3]
    assert list(rej[rej["reason"] == "GROUP_LEG_REJECTED"]["symbol"]) == [ranked[2]]


# --- trade lifecycle through the engine ---

BREAKOUT = (100.2, 101.0, 100.1, 100.8)  # through the long trigger, above the stop
STOP_HIT = (100.0, 100.1, 99.0, 99.2)
UP_AGAIN = (100.2, 101.0, 100.1, 100.8)


def test_one_trade_per_symbol_per_day():
    b = bars(**{"10:00": BREAKOUT, "10:30": STOP_HIT, "11:00": STOP_HIT, "11:30": UP_AGAIN})
    result, bt = run(orb(), b, feats())
    assert [t for t, _ in result.intents] == [ts(DAY, "09:45")] * 2
    (trade,) = bt.portfolio.trades
    assert trade.side == "long" and trade.exit_reason == "stop"
    assert float(trade.entry_ref) == pytest.approx(BUY_TRIGGER) and float(trade.exit_ref) == 99.5
    assert trade.entry_time == ts(DAY, "10:00") and trade.exit_time == ts(DAY, "10:30")
    cancelled = [e for e in result.events if "OCO" in e.reason]
    assert len(cancelled) == 1  # the short leg


def test_target_exit():
    target = BUY_TRIGGER + 2 * (BUY_TRIGGER - 99.5)
    b = bars(**{"10:00": BREAKOUT, "11:00": (101.0, target + 0.5, 100.9, target)})
    (trade,) = run(orb(), b, feats())[1].portfolio.trades
    assert trade.exit_reason == "target" and float(trade.exit_ref) == pytest.approx(target)


@pytest.mark.parametrize(
    ("time_exit", "exit_at", "reason"),
    [("14:30", "14:30", "strategy"), ("14:45", "14:45", "strategy"), ("14:50", "14:50", "flat_by")],
)
def test_time_exit_then_flat_by(time_exit, exit_at, reason):
    result, bt = run(orb(time_exit=time_exit), bars(**{"10:00": BREAKOUT}), feats())
    (trade,) = bt.portfolio.trades
    assert trade.exit_time == ts(DAY, exit_at) and trade.exit_reason == reason
    assert "DUPLICATE_EXIT" not in set(result.rejections["reason"])


# --- look-ahead ---

LA_DAYS = business_days("2024-03-04", 4)
LA_SYMBOLS = ("AAA", "BBB", "CCC")


def _la_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    b = pd.concat(
        [resample_bars(many_sessions(s, LA_DAYS, seed=7 * i), 5) for i, s in enumerate(LA_SYMBOLS)],
        ignore_index=True,
    )
    rng = np.random.default_rng(3)
    rows = [
        {
            "symbol": s,
            "session_date": d,
            "available_at": ts(d, "09:15"),
            "prior_sessions": 30,
            "prev_high": 101 + i + rng.normal(0, 0.5),
            "prev_low": 99 + i + rng.normal(0, 0.5),
            "prev_close": 100 + i,
            "atr14": abs(rng.normal(2, 0.5)),
            "zero_vol_share_20d": 0.0,
        }
        for i, d in enumerate(LA_DAYS)
        for s in LA_SYMBOLS
    ]
    return b, pd.DataFrame(rows)


def _la_run(cut: pd.Timestamp | None) -> tuple[list, list]:
    b, f = _la_inputs()
    if cut is not None:
        b, f = b[b["available_at"] <= cut], f[f["available_at"] <= cut]
    s = orb(filters={"gap": {"enabled": False}, "range_width": {"enabled": False}})
    result, bt = run_frames(s, b.reset_index(drop=True), LA_DAYS, features=f.reset_index(drop=True))
    return result.intents, bt.portfolio.trades


@pytest.mark.parametrize(
    "cut",
    [
        ts(LA_DAYS[0], "09:40"),
        ts(LA_DAYS[0], "09:45"),
        ts(LA_DAYS[1], "11:35"),
        ts(LA_DAYS[2], "14:30"),
        ts(LA_DAYS[3], "15:30"),
    ],
)
def test_intents_unchanged_by_truncation(cut):
    full, trades = _la_run(None)
    assert len(full) >= 12 and len(trades) >= 3  # not vacuous
    cut_intents, _ = _la_run(cut)
    assert cut_intents == [(t, i) for t, i in full if t <= cut]
