"""Strategy 2, monthly momentum (swing, CNC): known-answer tests on synthetic daily bars
run through the real Backtester, a check against an independent pandas computation with
the YAML defaults, and a look-ahead truncation check."""

from collections import defaultdict
from datetime import date
from itertools import pairwise

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from nsealgo.engine.config import load_strategy_params
from nsealgo.engine.types import IntentKind
from nsealgo.strategies import make_strategy
from nsealgo.strategies.swing_momentum import SwingMomentumStrategy
from tests.data_helpers import business_days
from tests.engine_helpers import daily_frame, run_frames, ts

DAYS = [d for d in business_days("2024-01-01", 130) if d <= date(2024, 6, 28)]
MONTHS = ("2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06")
# Small windows so six months of bars suffice: momentum = end of M-1 over end of M-3.
SMALL = {"top_n": 2, "lookback_months": 2, "skip_months": 1, "trend_ma_sessions": 5}
# Month levels Jan..Jun. At 30 Apr (Mar over Jan): A 1.30, B 1.20, D 1.10, C 1.05.
# At 31 May (Apr over Feb): C 2.00, B 1.30, D 1.10, A 0.82.
LEVELS = {
    "A": (100, 110, 130, 90, 90, 90),
    "B": (100, 100, 120, 130, 130, 130),
    "C": (100, 100, 105, 200, 200, 200),
    "D": (100, 100, 110, 110, 110, 110),
}
APR26, APR29, APR30, MAY1, MAY2, MAY31, JUN3, JUN28 = (
    date(2024, 4, 26),
    date(2024, 4, 29),
    date(2024, 4, 30),
    date(2024, 5, 1),
    date(2024, 5, 2),
    date(2024, 5, 31),
    date(2024, 6, 3),
    date(2024, 6, 28),
)


def swing(**overrides) -> SwingMomentumStrategy:
    return SwingMomentumStrategy(**load_strategy_params("swing", overrides))


def small(**overrides) -> SwingMomentumStrategy:
    return swing(**(SMALL | overrides))


def month_bars(symbol: str, levels, drift=1e-4, days=DAYS) -> pd.DataFrame:
    """Close = month level x (1 + drift x k) on the month's k-th session (k from 0), so
    with drift > 0 every month-end close is above its 5-session average. `drift` is one
    value or one per month. Open = close; high/low +/- 1%."""
    drifts = drift if isinstance(drift, tuple) else (drift,) * len(MONTHS)
    seen: dict[str, int] = defaultdict(int)
    rows = {}
    for d in days:
        m = MONTHS.index(f"{d:%Y-%m}")
        px = levels[m] * (1 + drifts[m] * seen[MONTHS[m]])
        seen[MONTHS[m]] += 1
        rows[d] = (px, px * 1.01, px * 0.99, px)
    return daily_frame(symbol, rows)


def universe_bars(levels=LEVELS, **drifts) -> pd.DataFrame:
    return pd.concat([month_bars(s, lv, drifts.get(s, 1e-4)) for s, lv in levels.items()])


def run(strategy, bars, days=DAYS, **kw):
    return run_frames(strategy, bars.reset_index(drop=True), days, **kw)


def decisions(result) -> dict[pd.Timestamp, list[tuple[str, str, int | None]]]:
    out: dict[pd.Timestamp, list] = defaultdict(list)
    for t, i in result.intents:
        out[t].append((i.kind.value, i.symbol, i.rank))
    return dict(out)


# --- parameters ---


def test_yaml_defaults_and_registry():
    s = make_strategy("swing", load_strategy_params("swing", {}))
    assert isinstance(s, SwingMomentumStrategy) and s.name == "swing" and s.version == "2"
    assert s.params() == {
        "top_n": 4,
        "lookback_months": 6,
        "skip_months": 1,
        "trend_ma_sessions": 200,
        "resize_holdings": False,
        "market_filter": {"enabled": False, "index_symbol": "NIFTY 50", "ma_sessions": 200},
    }
    assert (s.product.value, s.timeframe) == ("CNC", "1d")
    assert s.reference_symbols == ()
    assert s.lookback_sessions == 200  # max(200-session average, 23 sessions x 7 months)


def test_market_filter_adds_the_index_as_a_reference_symbol():
    s = swing(market_filter={"enabled": True, "ma_sessions": 250})
    assert s.reference_symbols == ("NIFTY 50",) and s.lookback_sessions == 250


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"resize_holdings": True}, "not implemented"),
        ({"top_n": 0}, "greater than 0"),
        ({"lookback_months": 0}, "greater than 0"),
        ({"skip_months": -1}, "greater than or equal to 0"),
        ({"trend_ma_sessions": 1}, "greater than 1"),
        ({"extra": 1}, "Extra inputs"),
        ({"market_filter": {"extra": 1}}, "Extra inputs"),
    ],
)
def test_bad_params_rejected(overrides, match):
    with pytest.raises(ValidationError, match=match):
        swing(**overrides)


def test_missing_param_rejected():
    params = load_strategy_params("swing", {})
    del params["skip_months"]
    with pytest.raises(ValidationError, match="skip_months"):
        SwingMomentumStrategy(**params)


# --- rebalancing ---


def test_ranks_by_return_skipping_the_latest_month_and_swaps_only_dropouts():
    result, bt = run(small(), universe_bars())
    # Only month-ends with enough history decide (30 Apr, 31 May); 28 Jun is the
    # calendar's last session (no next session), so it does not.
    assert decisions(result) == {
        ts(APR30, "15:30"): [("ENTRY", "A", 1), ("ENTRY", "B", 2)],  # not C (April skipped)
        ts(MAY31, "15:30"): [("EXIT", "A", None), ("ENTRY", "C", 1)],  # B kept as it is
    }
    trades = {t.symbol: t for t in bt.portfolio.trades}
    assert set(trades) == {"A", "B", "C"}
    a, b = trades["A"], trades["B"]
    assert (a.entry_time, a.exit_time, a.exit_reason) == (
        ts(MAY1, "09:15"),
        ts(JUN3, "09:15"),
        "strategy",
    )
    assert (b.entry_time, b.exit_time, b.exit_reason) == (
        ts(MAY1, "09:15"),
        ts(JUN28, "09:15"),
        "end_of_run",
    )
    # A: ref = 30 Apr close 90 x 1.0021; 99% of the slot (20000 - 23.76) / 4 = 4944.12
    # -> 54 shares, filled at the 1 May open 90.00 + 3 bps.
    assert a.qty == 54 and float(a.entry_price) == pytest.approx(90.027)
    assert b.qty == 37  # floor(4944.12 / (130 x 1.0021)); kept as it is to the end


def test_every_sale_pays_the_dp_charge():
    result, _ = run(small(), universe_bars())
    sells = result.fills[result.fills["side"] == "SELL"]
    assert sorted(sells["symbol"]) == ["A", "B", "C"]  # B and C both sold on 28 Jun
    assert sells["dp_charge"].tolist() == [9.0, 9.0, 9.0]


def test_trend_filter_and_cash_when_too_few_qualify():
    # B drifts down inside every month: its close is below its 5-session average.
    result, _ = run(small(), universe_bars(B=-1e-4))
    assert decisions(result)[ts(APR30, "15:30")] == [("ENTRY", "A", 1), ("ENTRY", "D", 2)]
    # Only A qualifies: one position, the rest stays in cash.
    result, bt = run(small(), universe_bars(B=-1e-4, C=-1e-4, D=-1e-4))
    assert decisions(result)[ts(APR30, "15:30")] == [("ENTRY", "A", 1)]
    assert {t.symbol for t in bt.portfolio.trades} == {"A"}


def test_a_stock_without_a_bar_on_the_decision_day_is_not_ranked():
    bars = universe_bars()
    bars = bars[~((bars["symbol"] == "A") & (bars["session_date"] == APR30))]
    result, _ = run(small(), bars)
    assert decisions(result)[ts(APR30, "15:30")] == [("ENTRY", "B", 1), ("ENTRY", "D", 2)]


def test_orders_fill_at_the_next_tradeable_open():
    _, bt = run(small(), universe_bars(), no_trade=(MAY1,))
    a = next(t for t in bt.portfolio.trades if t.symbol == "A")
    assert a.entry_time == ts(MAY2, "09:15")
    assert float(a.entry_price) == pytest.approx(90 * (1 + 1e-4) * 1.0003)  # 2 May open


@pytest.mark.parametrize(("no_trade", "decided"), [((APR30,), APR29), ((APR29, APR30), APR26)])
def test_a_month_ending_on_no_trade_days_decides_on_its_last_tradeable_session(no_trade, decided):
    result, bt = run(small(), universe_bars(), no_trade=no_trade)
    assert decisions(result) == {  # nothing on the no_trade days themselves
        ts(decided, "15:30"): [("ENTRY", "A", 1), ("ENTRY", "B", 2)],
        ts(MAY31, "15:30"): [("EXIT", "A", None), ("ENTRY", "C", 1)],
    }
    a = next(t for t in bt.portfolio.trades if t.symbol == "A")
    assert a.entry_time == ts(MAY1, "09:15")  # the next tradeable open


def test_one_share_above_the_cap_is_skipped_and_its_slot_stays_cash():
    levels = LEVELS | {"A": tuple(100 * x for x in LEVELS["A"])}  # A ~ Rs 9,000+ a share
    result, bt = run(small(), universe_bars(levels))
    assert decisions(result)[ts(APR30, "15:30")] == [("ENTRY", "A", 1), ("ENTRY", "B", 2)]
    rej = result.rejections
    assert list(rej["reason"]) == ["PRICE_ABOVE_POSITION_CAP"]
    assert (rej["symbol"].iloc[0], rej["rank"].iloc[0]) == ("A", 1)
    # Only newcomers to the top N are bought: D (rank 3) does not take A's slot.
    assert {t.symbol for t in bt.portfolio.trades} == {"B", "C"}


# --- market filter ---


def _with_index(drift) -> pd.DataFrame:
    return pd.concat([universe_bars(), month_bars("IDX", (100,) * 6, drift)])


def _filtered(drift, **mf):
    s = small(market_filter={"enabled": True, "index_symbol": "IDX", "ma_sessions": 5} | mf)
    return run(s, _with_index(drift), universe=list(LEVELS))


def test_market_filter_goes_to_cash_when_the_index_is_below_its_average():
    # Index falls through April, rises through May: no buys on 30 Apr, normal on 31 May.
    result, _ = _filtered((1e-4, 1e-4, 1e-4, -1e-4, 1e-4, 1e-4))
    assert decisions(result) == {ts(MAY31, "15:30"): [("ENTRY", "C", 1), ("ENTRY", "B", 2)]}
    # Rises through April, falls through May: buys on 30 Apr, sells everything on 31 May.
    result, bt = _filtered((1e-4, 1e-4, 1e-4, 1e-4, -1e-4, 1e-4))
    assert decisions(result)[ts(MAY31, "15:30")] == [("EXIT", "A", None), ("EXIT", "B", None)]
    assert all(t.exit_time == ts(JUN3, "09:15") for t in bt.portfolio.trades)


def test_market_filter_is_skipped_without_index_bars():
    on = small(market_filter={"enabled": True, "index_symbol": "NIFTY 50", "ma_sessions": 5})
    with_filter, _ = run(on, universe_bars())
    without, _ = run(small(), universe_bars())
    assert decisions(with_filter) == decisions(without)


# --- YAML defaults against an independent computation ---

LONG_DAYS = business_days("2023-01-02", 320)  # to late March 2024
LONG_SYMBOLS = ("P", "Q", "R", "S", "T", "U", "V")


def _walks(days: list[date], symbols, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    parts = []
    for i, s in enumerate(symbols):
        drift = (i - len(symbols) / 2) * 4e-4
        px = 100 * np.exp(np.cumsum(rng.normal(drift, 0.015, len(days))))
        rows = {d: (p, p * 1.01, p * 0.99, p) for d, p in zip(days, px, strict=True)}
        parts.append(daily_frame(s, rows))
    return pd.concat(parts, ignore_index=True)


def expected_top(bars: pd.DataFrame, day: date, n: int = 4) -> set[str]:
    close = bars.pivot(index="session_date", columns="symbol", values="close")
    close.index = pd.to_datetime(close.index)
    upto = close[close.index <= pd.Timestamp(day)]
    above = upto.iloc[-1] > upto.rolling(200).mean().iloc[-1]
    month_end = upto.groupby(upto.index.to_period("M")).last()
    m = pd.Timestamp(day).to_period("M")
    mom = month_end.loc[m - 1] / month_end.loc[m - 7] - 1
    return set(mom[above].sort_values(ascending=False).index[:n])


def test_defaults_match_an_independent_pandas_computation():
    bars = _walks(LONG_DAYS, LONG_SYMBOLS, seed=11)
    result, _ = run(swing(), bars, days=LONG_DAYS)
    assert result.rejections.empty
    month_ends = [d for d, nxt in pairwise(LONG_DAYS) if d.month != nxt.month]
    ready = [d for d in month_ends if LONG_DAYS.index(d) >= 199]  # 200 closes visible
    assert len(ready) >= 4
    by_time = decisions(result)
    assert set(by_time) <= {ts(d, "15:30") for d in ready}
    held: set[str] = set()
    sizes = []
    for d in ready:
        for kind, symbol, _ in by_time.get(ts(d, "15:30"), []):
            held = held - {symbol} if kind == "EXIT" else held | {symbol}
        assert held == expected_top(bars, d), d
        sizes.append(len(held))
    assert max(sizes) == 4 and min(sizes) < 4  # some months had fewer than 4 above trend


# --- look-ahead ---


def _la_run(cut: pd.Timestamp | None) -> list:
    bars = _walks(DAYS, ("P", "Q", "R", "S", "T"), seed=5)
    if cut is not None:
        bars = bars[bars["available_at"] <= cut]
    result, _ = run(small(), bars)
    return result.intents


@pytest.mark.parametrize(
    "cut",
    [
        ts(APR30, "09:15"),
        ts(APR30, "15:30"),
        ts(MAY2, "15:30"),
        ts(MAY31, "15:30"),
        ts(JUN3, "09:15"),
    ],
)
def test_intents_unchanged_by_truncation(cut):
    full = _la_run(None)
    assert sum(i.kind is IntentKind.ENTRY for _, i in full) >= 2  # not vacuous
    assert _la_run(cut) == [(t, i) for t, i in full if t <= cut]
