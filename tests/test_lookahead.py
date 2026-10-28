"""No look-ahead: what a strategy sees and emits at time T must not depend on data after T.

Each run uses random-walk bars and random daily feature columns. The test strategies
read bars, features, positions, working orders and fills, and their scores depend on
fills, so a leak through any of them (or through fill timing) changes their intents.
For a cut time T, a run on the full data and a run on data truncated at
available_at <= T must produce identical intents up to T, and identical contexts.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from nsealgo.data.calendar import IST
from nsealgo.data.resample import resample_bars
from nsealgo.engine.types import OrderIntent, OrderType, Product, Side
from tests.data_helpers import business_days, many_sessions
from tests.engine_helpers import daily_frame, entry, exit_, run_frames, ts

SYMBOLS = ("AAA", "BBB", "CCC")


def _features(days: list[date], seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = [
        {
            "symbol": s,
            "session_date": d,
            "available_at": ts(d, "09:15"),
            "f1": rng.normal(),
            "f2": rng.normal(),
        }
        for d in days
        for s in SYMBOLS
    ]
    return pd.DataFrame(rows)


def _truncate(df: pd.DataFrame, cut: pd.Timestamp) -> pd.DataFrame:
    return df[df["available_at"] <= cut].reset_index(drop=True)


def fingerprint(ctx: Any) -> tuple:
    """Everything the context exposes, as plain values."""
    bars = tuple(
        (s, len(b), b.last_close, tuple(sorted((ctx.features(s) or {}).items())))
        for s in ctx.symbols
        for b in [ctx.bars(s)]
    )
    pos = tuple(sorted((s, p.qty, p.avg_price) for s, p in ctx.positions.items()))
    orders = tuple(
        (v.order_id, v.order.symbol, v.order.side, v.order.qty, v.order.order_type, v.order.price)
        for v in ctx.working_orders
    )
    fills = tuple((f.order_id, f.ts, f.price, f.qty) for f in ctx.fills_today)
    return ctx.now, bars, pos, orders, fills


def _fill_score(ctx: Any, sym: str) -> float:
    return sum(f.qty for f in ctx.fills_today if f.symbol == sym) % 3 * 0.7


@dataclass(frozen=True)
class RandomFeatureMIS:
    product: Product = Product.MIS
    timeframe: str = "5m"
    name: str = "random_feature_mis"
    version: str = "test"
    instrument: str = "EQ"
    lookback_sessions: int = 0
    seen: list = field(default_factory=list, compare=False)

    def params(self) -> dict[str, Any]:
        return {}

    def on_bar(self, ctx: Any) -> list[OrderIntent]:
        self.seen.append(fingerprint(ctx))
        out = []
        for sym in ctx.symbols:
            b, f = ctx.bars(sym), ctx.features(sym)
            if len(b) < 3 or f is None:
                continue
            c = b.close
            score = (c[-1] - c[-3]) / c[-1] * 500 + f["f1"] * 0.5 + _fill_score(ctx, sym)
            pos = ctx.positions.get(sym)
            pending = any(v.order.symbol == sym for v in ctx.working_orders)
            if pos is None and not pending:
                out += self._entries(sym, b, float(c[-1]), score, f["f2"])
            elif pos is not None and score * pos.qty < -0.5:
                out.append(exit_(sym))
        return out

    @staticmethod
    def _entries(sym: str, b: Any, px: float, score: float, f2: float) -> list[OrderIntent]:
        if score > 1.0:
            return [entry(sym, Side.BUY, stop=px * 0.998, target=px * 1.006)]
        if score < -1.0:
            return [entry(sym, Side.SELL, stop=px * 1.002)]
        if abs(score) < 0.3 or f2 > 1.5:
            hi, lo, g = float(b.high[-3:].max()), float(b.low[-3:].min()), f"{sym}{len(b)}"
            return [
                entry(
                    sym,
                    Side.BUY,
                    order_type=OrderType.STOP,
                    price=hi + 0.05,
                    stop=hi * 0.996,
                    target=hi * 1.004,
                    group=g,
                ),
                entry(
                    sym,
                    Side.SELL,
                    order_type=OrderType.STOP,
                    price=lo - 0.05,
                    stop=lo * 1.004,
                    group=g,
                ),
            ]
        return []


@dataclass(frozen=True)
class RandomFeatureSwing:
    product: Product = Product.CNC
    timeframe: str = "1d"
    name: str = "random_feature_swing"
    version: str = "test"
    instrument: str = "EQ"
    lookback_sessions: int = 0
    seen: list = field(default_factory=list, compare=False)

    def params(self) -> dict[str, Any]:
        return {}

    def on_bar(self, ctx: Any) -> list[OrderIntent]:
        self.seen.append(fingerprint(ctx))
        scores = {}
        for sym in ctx.symbols:
            b, f = ctx.bars(sym), ctx.features(sym)
            if len(b) >= 2 and f is not None:
                trend = (b.close[-1] / b.close.mean() - 1) * 50
                scores[sym] = trend + f["f1"] + _fill_score(ctx, sym)
        top = sorted(scores, key=lambda s: -scores[s])[:2]
        pending = {v.order.symbol for v in ctx.working_orders}
        held = ctx.positions
        out = [exit_(s, product=Product.CNC) for s in held if s not in top and s not in pending]
        out += [
            entry(s, Side.BUY, product=Product.CNC, rank=i)
            for i, s in enumerate(top, 1)
            if s not in held and s not in pending
        ]
        return out


MIS_DAYS = business_days("2024-03-04", 4)
MIS_BARS = pd.concat(
    [resample_bars(many_sessions(s, MIS_DAYS, seed=10 * i), 5) for i, s in enumerate(SYMBOLS)],
    ignore_index=True,
)
MIS_FEATURES = _features(MIS_DAYS, seed=1)

SWING_DAYS = business_days("2024-03-04", 30)
_rng = np.random.default_rng(7)


def _walk(symbol: str) -> pd.DataFrame:
    prices = 100 * np.exp(np.cumsum(_rng.normal(0, 0.02, len(SWING_DAYS))))
    return daily_frame(
        symbol, {d: (p, p * 1.01, p * 0.99, p) for d, p in zip(SWING_DAYS, prices, strict=True)}
    )


SWING_BARS = pd.concat([_walk(s) for s in SYMBOLS], ignore_index=True)
SWING_FEATURES = _features(SWING_DAYS, seed=2)

CASES = {
    "mis": (RandomFeatureMIS, MIS_BARS, MIS_FEATURES, MIS_DAYS),
    "swing": (RandomFeatureSwing, SWING_BARS, SWING_FEATURES, SWING_DAYS),
}
_FULL: dict[str, tuple[list, list, Any]] = {}


def _run(case: str, cut: pd.Timestamp | None) -> tuple[list, list, Any]:
    make, bars, feats, days = CASES[case]
    if cut is not None:
        bars, feats = _truncate(bars, cut), _truncate(feats, cut)
    strategy = make()
    # More trades per day than risk.yaml allows, so stops, targets and flat_by all occur.
    extra = {"max_trades_per_day": 50} if case == "mis" else {}
    result, bt = run_frames(strategy, bars, days, features=feats, **extra)
    return result.intents, strategy.seen, bt


def _full(case: str) -> tuple[list, list, Any]:
    if case not in _FULL:
        _FULL[case] = _run(case, None)
    return _FULL[case]


def _check(case: str, cut: pd.Timestamp) -> int:
    full_intents, full_seen, _ = _full(case)
    cut_intents, cut_seen, _ = _run(case, cut)
    assert cut_seen == [s for s in full_seen if s[0] <= cut]
    expected = [(t, i) for t, i in full_intents if t <= cut]
    assert cut_intents == expected
    return len(expected)


def test_strategies_are_not_vacuous():
    for case in CASES:
        intents, _, bt = _full(case)
        assert len(intents) >= 10, case
        assert len(bt.portfolio.trades) >= 3, case
    intents, _, bt = _full("mis")
    assert any(i.group_id for _, i in intents), "the MIS strategy should exercise OCO groups"
    assert {t.exit_reason for t in bt.portfolio.trades} >= {"stop", "target", "strategy"}


@pytest.mark.parametrize(
    "cut",
    [
        ts(MIS_DAYS[0], "09:20"),
        ts(MIS_DAYS[0], "10:00"),
        ts(MIS_DAYS[1], "11:35"),
        ts(MIS_DAYS[1], "14:50"),
        ts(MIS_DAYS[2], "15:30"),
        ts(MIS_DAYS[3], "09:15"),
    ],
)
def test_mis_intents_unchanged_by_truncation(cut):
    _check("mis", cut)


@pytest.mark.parametrize("k", [0, 1, 5, 12, 20, 29])
@pytest.mark.parametrize("hhmm", ["09:15", "15:30"])
def test_swing_intents_unchanged_by_truncation(k, hhmm):
    _check("swing", ts(SWING_DAYS[k], hhmm))


_MIS_TIMES = sorted({pd.Timestamp(t).tz_convert(IST) for t in MIS_BARS["available_at"]})


@settings(max_examples=40, deadline=None)
@given(cut=st.sampled_from(_MIS_TIMES))
def test_mis_intents_unchanged_at_random_cut(cut):
    _check("mis", cut)


def test_every_decision_time_matches():
    # Exhaustive over one session: every 5m decision time on day 2.
    day_times = [t for t in _MIS_TIMES if t.date() == MIS_DAYS[1]]
    for cut in day_times:
        _check("mis", cut)


def test_late_cut_compares_everything():
    assert _check("mis", ts(MIS_DAYS[3], "15:30")) == len(_full("mis")[0])
    assert _check("swing", ts(SWING_DAYS[-1], "15:30")) == len(_full("swing")[0])
