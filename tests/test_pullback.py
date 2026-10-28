"""Strategy 3, pullback mean reversion (swing, CNC): known-answer tests on synthetic daily
bars run through the real Backtester, Wilder RSI known answers, a check against an
independent pandas computation with the YAML defaults, and a look-ahead truncation
check. Rules: research/strategy3_plan.md."""

from collections import defaultdict
from datetime import date

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from nsealgo.engine.config import load_strategy_params
from nsealgo.engine.types import IntentKind
from nsealgo.strategies import make_strategy
from nsealgo.strategies.indicators import wilder_rsi
from nsealgo.strategies.pullback import RSI_HISTORY, PullbackStrategy
from tests.data_helpers import business_days
from tests.engine_helpers import daily_frame, run_frames, ts

DAYS = business_days("2024-01-01", 70)  # DAYS[0] .. DAYS[69]
SMALL = {"trend_ma_sessions": 40}  # so 70 sessions of bars suffice
R = 4.0  # the uptrend rises Rs 4 a session


def pullback(**overrides) -> PullbackStrategy:
    return PullbackStrategy(**load_strategy_params("pullback", overrides))


def small(**overrides) -> PullbackStrategy:
    return pullback(**(SMALL | overrides))


def path(drop: float, after: float = -0.5, n: int = len(DAYS)) -> list[float]:
    """Close: 100 + R x i on days 0..49 (296 on day 49), two drops of `drop` (days 50
    and 51), then `after` a session. RSI(2) on day 51 is 100 R / (R + 3 drop): gains
    R -> R/2 -> R/4, losses 0 -> drop/2 -> 3 drop/4. The 40-session average on day 51
    is (9028 - 3 drop) / 40, under the close 296 - 2 drop for any drop < 36.5."""
    up = [100 + R * i for i in range(50)]
    down = [up[-1] - drop, up[-1] - 2 * drop]
    return up + down + [down[-1] + after * k for k in range(1, n - 51)]


def frame(symbol: str, closes: list[float], days=DAYS) -> pd.DataFrame:
    """Open = the previous close, so a next-open fill is at the decision close."""
    opens = [closes[0], *closes[:-1]]
    rows = {
        d: (o, max(o, c) + 1, min(o, c) - 1, c) for d, o, c in zip(days, opens, closes, strict=True)
    }
    return daily_frame(symbol, rows)


def bars(**paths: list[float]) -> pd.DataFrame:
    return pd.concat([frame(s, p) for s, p in paths.items()], ignore_index=True)


FLAT = [100.0] * len(DAYS)  # never a candidate (no RSI), keeps every session alive


def run(strategy, frames: pd.DataFrame, days=DAYS, **kw):
    return run_frames(strategy, frames.reset_index(drop=True), days, **kw)


def decisions(result) -> dict[date, list[tuple[str, str, int | None]]]:
    out: dict[date, list] = defaultdict(list)
    for t, i in result.intents:
        out[t.date()].append((i.kind.value, i.symbol, i.rank))
    return dict(out)


def trades(bt) -> list[tuple[str, date, date, str]]:
    return [
        (t.symbol, t.entry_time.date(), t.exit_time.date(), t.exit_reason)
        for t in bt.portfolio.trades
    ]


def tags(result) -> dict[date, list[str]]:
    out: dict[date, list] = defaultdict(list)
    for t, i in result.intents:
        out[t.date()].append(i.tag)
    return dict(out)


# --- parameters ---


def test_yaml_defaults_and_registry():
    s = make_strategy("pullback", load_strategy_params("pullback", {}))
    assert isinstance(s, PullbackStrategy) and s.name == "pullback" and s.version == "1"
    assert s.params() == {
        "trend_ma_sessions": 200,
        "rsi_sessions": 2,
        "rsi_entry_below": 10.0,
        "exit_ma_sessions": 5,
        "max_hold_sessions": 10,
    }
    assert (s.product.value, s.timeframe) == ("CNC", "1d")
    assert s.reference_symbols == ()
    assert s.lookback_sessions == 200 and RSI_HISTORY == 100


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"trend_ma_sessions": 1}, "greater than 1"),
        ({"rsi_sessions": 0}, "greater than 0"),
        ({"rsi_sessions": 99}, "less than 99"),
        ({"rsi_entry_below": 0}, "greater than 0"),
        ({"rsi_entry_below": 100}, "less than 100"),
        ({"exit_ma_sessions": 1}, "greater than 1"),
        ({"max_hold_sessions": 0}, "greater than 0"),
        ({"extra": 1}, "Extra inputs"),
    ],
)
def test_bad_params_rejected(overrides, match):
    with pytest.raises(ValidationError, match=match):
        pullback(**overrides)


def test_missing_param_rejected():
    params = load_strategy_params("pullback", {})
    del params["max_hold_sessions"]
    with pytest.raises(ValidationError, match="max_hold_sessions"):
        PullbackStrategy(**params)


# --- Wilder RSI ---


def test_wilder_rsi_known_answer():
    # Changes +1, -0.5, -0.5, -1. Seed: gain (1 + 0) / 2 = 0.5, loss (0 + 0.5) / 2 = 0.25.
    # Then gain 0.25, 0.125; loss (0.25 + 0.5) / 2 = 0.375, (0.375 + 1) / 2 = 0.6875.
    assert wilder_rsi(np.array([10, 11, 10.5, 10, 9]), 2) == pytest.approx(100 * 0.125 / 0.8125)
    assert wilder_rsi(np.array([1.0, 2, 3, 4]), 2) == 100.0
    assert wilder_rsi(np.array([4.0, 3, 2, 1]), 2) == 0.0


def test_wilder_rsi_undefined_cases():
    assert wilder_rsi(np.array([10.0, 11]), 2) is None  # fewer than 2 changes
    assert wilder_rsi(np.array([10.0, 10, 10, 10]), 2) is None  # no gains, no losses


def reference_rsi(close: pd.Series, n: int = 2) -> pd.Series:
    """Wilder RSI over the whole series: SMA seed of the first n changes, then an EWM
    with alpha 1/n; RSI = 100 - 100 / (1 + RS). Indexed by close date from close n."""
    change = close.diff().iloc[1:]

    def smooth(x: pd.Series) -> pd.Series:
        seq = pd.Series([x.iloc[:n].mean(), *x.iloc[n:]], index=x.index[n - 1 :])
        return seq.ewm(alpha=1 / n, adjust=False).mean()

    gain, loss = smooth(change.clip(lower=0)), smooth((-change).clip(lower=0))
    return 100 - 100 / (1 + gain / loss)


def test_wilder_rsi_on_the_last_100_closes_equals_the_full_history():
    rng = np.random.default_rng(3)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 600))))
    full = reference_rsi(close)
    for end in (150, 333, 600):
        window = close.iloc[max(0, end - RSI_HISTORY) : end].to_numpy()
        assert wilder_rsi(window, 2) == pytest.approx(full.loc[end - 1], abs=1e-9)


# --- entries and ranking ---


def test_ranks_candidates_by_lowest_rsi_then_symbol_and_buys_four():
    # Day 51 RSI(2): C 7.69, A = B 8.70, E 8.93, D 9.43, F exactly 10 (not below).
    # G is flat then falls: RSI 0, but its close is below its 40-session average.
    drops = {"A": 14, "B": 14, "C": 16, "D": 12.8, "E": 13.6, "F": 12}
    g = [100.0] * 50 + [86.0, 72.0] + [72.0] * (len(DAYS) - 52)
    frames = bars(**{s: path(d) for s, d in drops.items()}, G=g)
    result, _ = run(small(), frames)
    d51, d52 = DAYS[51], DAYS[52]
    assert decisions(result)[d51] == [
        ("ENTRY", "C", 1),
        ("ENTRY", "A", 2),
        ("ENTRY", "B", 3),
        ("ENTRY", "E", 4),
        ("ENTRY", "D", 5),
    ]
    rej = result.rejections[result.rejections["now"] == ts(d51, "15:30")]
    assert list(zip(rej["symbol"], rej["reason"], rej["rank"], strict=True)) == [
        ("D", "MAX_POSITIONS", 5)
    ]
    buys = result.fills[(result.fills["side"] == "BUY") & (result.fills["session_date"] == d52)]
    assert sorted(buys["symbol"]) == ["A", "B", "C", "E"]
    assert set(buys["ts"]) == {ts(d52, "09:15")}


def test_no_decision_before_the_rise_or_on_the_first_drop():
    result, _ = run(small(), bars(A=path(14)))
    assert min(decisions(result)) == DAYS[51]  # day 50: RSI 100 x 2 / 9 = 22.2


# --- exits ---


def test_exit_at_the_next_open_after_a_close_above_the_5_session_average():
    # Day 52 close 280 < (292 + 296 + 282 + 268 + 280) / 5 = 283.6; day 53 close 290 >
    # (296 + 282 + 268 + 280 + 290) / 5 = 283.2. Flat after: RSI stays 75.9, no re-entry.
    closes = path(14)[:52] + [280.0, 290.0] + [290.0] * (len(DAYS) - 54)
    result, bt = run(small(), bars(A=closes))
    assert decisions(result) == {DAYS[51]: [("ENTRY", "A", 1)], DAYS[53]: [("EXIT", "A", None)]}
    assert tags(result)[DAYS[53]] == ["pullback_exit_ma"]
    assert trades(bt) == [("A", DAYS[52], DAYS[54], "strategy")]
    (t,) = bt.portfolio.trades
    assert float(t.entry_price) == pytest.approx(268 * 1.0003)
    assert float(t.exit_price) == pytest.approx(290 * 0.9997)


def test_time_exit_after_10_sessions_held_then_bought_again_next_decision():
    # Bought at the day 52 open; held over the closes of days 52..61 (10 sessions) while
    # the close stays below its 5-session average; sold at the day 62 open. Still RSI
    # < 10 and above the 40-session average (262.5 vs 251.3) on day 62: bought again at
    # the day 63 open, and closed at the end of the run.
    result, bt = run(small(), bars(A=path(14)))
    assert decisions(result) == {
        DAYS[51]: [("ENTRY", "A", 1)],
        DAYS[61]: [("EXIT", "A", None)],  # held, so not also a candidate
        DAYS[62]: [("ENTRY", "A", 1)],
    }
    assert tags(result)[DAYS[61]] == ["pullback_exit_time"]
    assert trades(bt) == [
        ("A", DAYS[52], DAYS[62], "strategy"),
        ("A", DAYS[63], DAYS[69], "end_of_run"),  # no decision on the last session
    ]


def test_a_held_symbol_without_a_bar_still_gets_the_time_exit():
    frames = bars(A=path(14), Z=FLAT)
    frames = frames[~((frames["symbol"] == "A") & (frames["session_date"] == DAYS[61]))]
    result, bt = run(small(), frames)
    assert decisions(result)[DAYS[61]] == [("EXIT", "A", None)]
    assert trades(bt)[0] == ("A", DAYS[52], DAYS[62], "strategy")


def test_no_ma_exit_check_without_a_bar_on_the_decision_day():
    closes = path(14)[:52] + [280.0, 290.0] + [290.0] * (len(DAYS) - 54)
    frames = bars(A=closes, Z=FLAT)
    frames = frames[~((frames["symbol"] == "A") & (frames["session_date"] == DAYS[53]))]
    result, _ = run(small(), frames)
    # Day 54: bars 49, 50, 51, 52, 54 -> average 283.2 < 290.
    assert [d for d, i in decisions(result).items() if i[0][0] == "EXIT"] == [DAYS[54]]


# --- no_trade sessions ---


def test_no_decision_on_a_no_trade_session_the_signal_waits():
    # Day 51 is no_trade. Day 52: RSI 50 / 6 = 8.33, still a candidate.
    result, bt = run(small(), bars(A=path(14)), no_trade=(DAYS[51],))
    assert decisions(result) == {
        DAYS[52]: [("ENTRY", "A", 1)],
        DAYS[62]: [("EXIT", "A", None)],
        DAYS[63]: [("ENTRY", "A", 1)],
    }
    assert trades(bt)[0] == ("A", DAYS[53], DAYS[63], "strategy")


def test_a_no_trade_session_counts_as_a_session_held():
    _, bt = run(small(), bars(A=path(14)), no_trade=(DAYS[55],))
    assert trades(bt)[0] == ("A", DAYS[52], DAYS[62], "strategy")


def test_an_exit_due_on_a_no_trade_session_is_decided_on_the_next_tradeable_one():
    result, bt = run(small(), bars(A=path(14)), no_trade=(DAYS[61],))
    assert DAYS[61] not in decisions(result)
    assert decisions(result)[DAYS[62]] == [("EXIT", "A", None)]  # 11 sessions held
    assert trades(bt)[0] == ("A", DAYS[52], DAYS[63], "strategy")


# --- YAML defaults against an independent computation ---

LONG_DAYS = business_days("2023-01-02", 420)
LONG_SYMBOLS = ("P", "Q", "R", "S", "T", "U", "V", "W")


def _walks(days: list[date], symbols, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    parts = []
    for i, s in enumerate(symbols):
        drift = (i - 2) * 3e-4
        px = 100 * np.exp(np.cumsum(rng.normal(drift, 0.02, len(days))))
        parts.append(frame(s, list(px), days))
    return pd.concat(parts, ignore_index=True)


def expected(frames: pd.DataFrame, days: list[date]):
    """Decisions and trades from the rules with pandas rolling means and full-history
    Wilder RSI (4 slots; every candidate fits a slot's cash in these walks)."""
    close = frames.pivot(index="session_date", columns="symbol", values="close")
    above = close > close.rolling(200).mean()
    rsi = close.apply(reference_rsi)
    over5 = close > close.rolling(5).mean()
    held: dict[str, int] = {}  # symbol -> index of the entry session
    out, done = {}, []
    for i, d in enumerate(days[:-1]):
        exits = sorted(s for s, e in held.items() if i - e + 1 >= 10 or over5.loc[d, s])
        ok = [s for s in close.columns if s not in held and above.loc[d, s] and rsi.loc[d, s] < 10]
        ranked = sorted(ok, key=lambda s: (rsi.loc[d, s], s))
        intents = [("EXIT", s, None) for s in exits] + [
            ("ENTRY", s, k) for k, s in enumerate(ranked, start=1)
        ]
        if intents:
            out[d] = intents
        done += [(s, days[held.pop(s)], days[i + 1], "strategy") for s in exits]
        free = 4 - len(held)
        held |= {s: i + 1 for s in ranked[:free]}
    done += [(s, days[e], days[-1], "end_of_run") for s, e in held.items()]
    return out, sorted(done)


def test_defaults_match_an_independent_pandas_computation():
    frames = _walks(LONG_DAYS, LONG_SYMBOLS, seed=7)
    result, bt = run(pullback(), frames, days=LONG_DAYS)
    want_decisions, want_trades = expected(frames, LONG_DAYS)
    assert decisions(result) == want_decisions
    assert sorted(trades(bt)) == want_trades
    assert set(result.rejections["reason"]) == {"MAX_POSITIONS"}
    assert len(want_trades) >= 40  # not vacuous
    exits = [t for t in want_trades if t[3] == "strategy"]
    held = [LONG_DAYS.index(t[2]) - LONG_DAYS.index(t[1]) for t in exits]
    assert max(held) == 10 and min(held) < 10  # both exit rules fired


# --- look-ahead ---


def _la_run(cut: pd.Timestamp | None) -> list:
    frames = _walks(LONG_DAYS, LONG_SYMBOLS, seed=7)
    if cut is not None:
        frames = frames[frames["available_at"] <= cut]
    result, _ = run(pullback(), frames, days=LONG_DAYS)
    return result.intents


@pytest.mark.parametrize("i", [250, 300, 350])
def test_intents_unchanged_by_truncation(i):
    full = _la_run(None)
    assert sum(x.kind is IntentKind.ENTRY for _, x in full) >= 20  # not vacuous
    for cut in (ts(LONG_DAYS[i], "09:15"), ts(LONG_DAYS[i], "15:30")):
        assert _la_run(cut) == [(t, x) for t, x in full if t <= cut]
