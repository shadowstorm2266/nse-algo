"""Equity-ETF units (instrument "ETF", strategy 4) through the engine: ETF charges on
every fill and in swing sizing, the ETF slippage tiers, the ETF proxy dataset in the
loader and the backtest CLI, the ETF benchmark, and sector_rotation = swing v2's rules."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from nsealgo import strategies
from nsealgo.backtest import RunPaths, main
from nsealgo.brokers.sim import SimBroker
from nsealgo.costs import fill_charges
from nsealgo.data.calendar import build_calendar
from nsealgo.data.features import daily_bars, daily_features, rvol_profile
from nsealgo.data.resample import resample_bars, with_available_at
from nsealgo.data.store import (
    connect,
    write_bars,
    write_calendar,
    write_etf_proxy,
    write_symbol_table,
)
from nsealgo.engine.backtest import validate_strategy
from nsealgo.engine.config import load_strategy_params
from nsealgo.engine.loader import (
    HoldoutLockedError,
    load_bars,
    load_research_config,
    market_chunks,
)
from nsealgo.engine.market import BAR_COLS
from nsealgo.engine.portfolio import Portfolio
from nsealgo.engine.sizing import swing_qty
from nsealgo.engine.types import OrderRole, Product, Side
from nsealgo.reporting.benchmark import buy_and_hold
from nsealgo.reporting.trials import read_trials
from nsealgo.strategies import make_strategy
from nsealgo.strategies.sector_rotation import SectorRotationStrategy
from nsealgo.strategies.swing_momentum import SwingMomentumStrategy
from tests.data_helpers import business_days, many_sessions
from tests.engine_helpers import (
    ScriptedStrategy,
    cost_config,
    daily_frame,
    entry,
    exit_,
    margins,
    risk_config,
    run_frames,
    ts,
)
from tests.test_sim_broker import cnc, daily
from tests.test_swing_momentum import DAYS as SWING_DAYS
from tests.test_swing_momentum import SMALL, decisions, universe_bars

D = Decimal
CNC = Product.CNC
DAYS = business_days("2016-02-01", 5)  # inside the dev period


def etf_charges(side: str, value: Decimal, dp: str = "0") -> Decimal:
    cfg = cost_config()
    d = cfg.broker.delivery
    return fill_charges("CNC", side, value, cfg.rates, d, D(dp), instrument="ETF").total


# --- costs and sizing ---


def test_slippage_tables_by_instrument():
    cfg = cost_config()
    assert cfg.slippage_table("EQ") == {"none": 0, "base": 3, "stress1": 6, "stress2": 10}
    assert cfg.slippage_table("ETF") == {"none": 0, "base": 10, "stress1": 20, "stress2": 30}
    with pytest.raises(ValueError, match="unknown instrument"):
        cfg.slippage_table("GOLD")


def test_swing_sizing_uses_the_instruments_buy_charges():
    cfg = cost_config()
    common = {
        "price": D("4.945"),
        "equity": D(20000),
        "rates": cfg.rates,
        "delivery": cfg.broker.delivery,
        "max_positions": 4,
        "cash_buffer_pct": D(1),
        "position_cap": D(6000),
        "gross_left": D(20000),
        "pending": [],
    }
    # slot = (5000 - buy charges on 5000) x 0.99. Equity pays Rs 5.94 (Rs 5 of it 0.1%
    # STT), ETF units Rs 0.94 (no STT on the buy): 4,944.12 vs 4,949.07.
    assert swing_qty(**common).qty == 999  # 1,000 x 4.945 = 4,945 > 4,944.12
    assert swing_qty(**common, instrument="ETF").qty == 1000


# --- SimBroker and the Backtester ---


def test_sim_broker_charges_etf_rates_on_buys_and_sells():
    pf = Portfolio(D(20000), margins(), "current_equity")
    cfg = cost_config()
    broker = SimBroker(cfg, "shoonya", D(10), funds=pf, on_fill=pf.apply_fill, instrument="ETF")
    day1, day2 = date(2024, 1, 3), date(2024, 1, 4)
    broker.place(cnc("A", Side.BUY, 50))
    (buy,) = broker.process({"A": daily("A", day1, 100)})
    assert buy.price == D("100.1")  # 10 bps
    assert buy.charges.total == etf_charges("BUY", buy.value)
    assert buy.charges.stt == 0 and buy.charges.stamp_duty == D("0.75")  # 0.015% of 5,005
    broker.place(cnc("A", Side.SELL, 50, role=OrderRole.EXIT))
    (sell,) = broker.process({"A": daily("A", day2, 100)})
    assert sell.charges.total == etf_charges("SELL", sell.value, "9")
    assert sell.charges.stt == D("0.05")  # 0.001% of 4,995


@pytest.mark.parametrize(
    ("product", "timeframe", "instrument", "match"),
    [(Product.MIS, "5m", "ETF", "delivery"), (CNC, "1d", "GOLD", "unknown instrument")],
)
def test_etf_strategies_must_be_cnc(product, timeframe, instrument, match):
    s = ScriptedStrategy(product, timeframe, {}, instrument=instrument)
    with pytest.raises(ValueError, match=match):
        validate_strategy(s, risk_config())


def test_backtester_passes_the_instrument_to_broker_and_risk_governor():
    days = SWING_DAYS[:4]
    rows = {d: (100.0, 101.0, 99.0, 100.0) for d in days}
    script = {
        ts(days[0], "15:30"): [entry("A", Side.BUY, product=CNC)],
        ts(days[1], "15:30"): [exit_("A", product=CNC)],
    }
    s = ScriptedStrategy(CNC, "1d", script, instrument="ETF")
    result, bt = run_frames(s, daily_frame("A", rows), days)
    assert bt.risk.instrument == "ETF"
    buy, sell = result.fills.itertuples()
    assert buy.side == "BUY" and buy.charges == float(etf_charges("BUY", D(str(buy.value))))
    assert sell.charges == float(etf_charges("SELL", D(str(sell.value)), "9"))


# --- loader and CLI on a temporary data/clean ---


def proxy_frame(symbols: tuple[str, ...]) -> pd.DataFrame:
    rows = [
        {
            "symbol": s,
            "session_date": d,
            "open": 100.0 + i + k,
            "high": 102.0 + i + k,
            "low": 98.0 + i + k,
            "close": 101.0 + i + k,
        }
        for k, s in enumerate(symbols)
        for i, d in enumerate(DAYS)
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def paths(tmp_path: Path) -> RunPaths:
    clean = tmp_path / "clean"
    bars = many_sessions("AAA", DAYS)
    write_bars(with_available_at(bars, 1), clean, "1m")
    for m in (5, 15):
        write_bars(resample_bars(bars, m), clean, f"{m}m")
    daily = daily_bars(bars)
    write_symbol_table(daily_features(daily, DAYS), clean, "features")
    write_symbol_table(rvol_profile(resample_bars(bars, 5), DAYS), clean, "rvol")
    sessions = daily[["symbol", "session_date", "n_bars"]]
    write_calendar(build_calendar(sessions, {}, set()), clean)
    write_etf_proxy(proxy_frame(("PX_A", "PX_B", "PX_N")), clean)
    cfg = tmp_path / "etf_proxy.yaml"
    cfg.write_text(
        f"raw_dir: {tmp_path.as_posix()}\nseries:\n"
        "  PX_A: {index: a, expense_ratio_pct: 0.40}\n"
        "  PX_B: {index: b, expense_ratio_pct: 0.40}\n"
        "  PX_N: {index: n, expense_ratio_pct: 0.05}\n"
        "universe: [PX_A, PX_B]\nbenchmark: PX_N\n",
        encoding="utf-8",
    )
    return RunPaths(
        clean_dir=clean, trials=tmp_path / "t.jsonl", runs_dir=tmp_path / "runs", etf_proxy=cfg
    )


def test_etf_daily_bars_come_from_the_proxy_dataset(paths):
    con = connect(paths.clean_dir)
    df = load_bars(con, "1d", ["PX_A"], DAYS[0], DAYS[-1], instrument="ETF")
    assert list(df.columns) == BAR_COLS and len(df) == len(DAYS)
    assert df["ts"].iloc[0] == ts(DAYS[0], "09:15")
    assert df["available_at"].iloc[0] == ts(DAYS[0], "15:30")
    assert (df["volume"] == 0).all() and df["close"].tolist()[:2] == [101.0, 102.0]
    with pytest.raises(ValueError, match="daily only"):
        load_bars(con, "5m", ["PX_A"], DAYS[0], DAYS[-1], instrument="ETF")


def test_etf_reads_keep_the_holdout_lock(paths):
    con = connect(paths.clean_dir)
    cfg = load_research_config()
    chunks = market_chunks(
        con,
        "1d",
        ["PX_A"],
        [cfg.holdout_start],
        lookback_sessions=0,
        research=cfg,
        allow_holdout=False,
        instrument="ETF",
    )
    with pytest.raises(HoldoutLockedError):
        next(chunks)


def test_missing_proxy_dataset_is_an_error(paths):
    (paths.clean_dir / "etf_proxy" / "bars.parquet").unlink()
    with pytest.raises(FileNotFoundError, match="build_etf_proxy"):
        load_bars(connect(paths.clean_dir), "1d", ["PX_A"], DAYS[0], DAYS[-1], instrument="ETF")


@pytest.fixture
def toy_etf(monkeypatch):
    script = {
        ts(DAYS[0], "15:30"): [entry("PX_A", Side.BUY, product=CNC)],
        ts(DAYS[2], "15:30"): [exit_("PX_A", product=CNC)],
    }
    monkeypatch.setitem(
        strategies.REGISTRY,
        "toy_etf",
        lambda: ScriptedStrategy(CNC, "1d", script, "toy_etf", instrument="ETF"),
    )


@pytest.mark.parametrize(("tier", "bps"), [("base", 10.0), ("stress2", 30.0)])
def test_cli_etf_run_uses_proxy_data_etf_universe_and_etf_slippage(paths, toy_etf, tier, bps):
    assert main(["--strategy", "toy_etf", "--cost-tier", tier], paths) == 0
    (trial,) = read_trials(paths.trials)
    assert trial["instrument"] == "ETF" and trial["universe"] == ["PX_A", "PX_B"]
    assert trial["slippage_bps_per_side"] == bps and trial["metrics"]["trades"] == 1
    fills = pd.read_parquet(Path(trial["run_dir"]) / "fills.parquet")
    buy, sell = fills.itertuples()
    assert buy.session_date == DAYS[1] and sell.session_date == DAYS[3]
    assert buy.price == pytest.approx(101.0 * (1 + bps / 10_000))  # PX_A's open on DAYS[1]
    assert sell.price == pytest.approx(103.0 * (1 - bps / 10_000))
    assert buy.charges == float(etf_charges("BUY", D(str(buy.value))))
    assert sell.charges == float(etf_charges("SELL", D(str(sell.value)), "9"))


# --- benchmark ---


def test_buy_and_hold_with_etf_buy_charges():
    cfg = cost_config()
    frame = pd.DataFrame(
        [{"symbol": "PX_A", "session_date": date(2024, 1, 1), "open": 100.0, "close": 100.0}]
    )
    eq = buy_and_hold(frame, 20000.0, cfg.rates, cfg.broker.delivery, D(10), "ETF")
    value = D(20000) - etf_charges("BUY", D(20000))
    expected = float(value) / 100.1 * 100 + float(D(20000) - value - etf_charges("BUY", value))
    assert eq["equity"].iloc[0] == pytest.approx(expected)
    assert 20000 - eq["equity"].iloc[0] == pytest.approx(20 + 3.75, abs=0.5)  # slippage + stamp


# --- strategy 4 ---


def test_sector_rotation_is_swing_v2_on_etf_units():
    s = make_strategy("sector_rotation", load_strategy_params("sector_rotation", {}))
    v2 = make_strategy("swing", load_strategy_params("swing", {}))
    assert isinstance(s, SectorRotationStrategy) and isinstance(s, SwingMomentumStrategy)
    assert (s.name, s.version, s.instrument) == ("sector_rotation", "1", "ETF")
    assert (s.product, s.timeframe, s.lookback_sessions) == (CNC, "1d", 200)
    assert v2.version == "2" and s.reference_symbols == ()
    p, q = s.params(), v2.params()
    # Only the disabled market filter's index name differs (PX_NIFTY50 vs NIFTY 50).
    assert p.pop("market_filter")["enabled"] is False
    assert q.pop("market_filter")["enabled"] is False
    assert p == q


def test_sector_rotation_decides_exactly_as_swing_v2():
    bars = universe_bars().reset_index(drop=True)
    rot = SectorRotationStrategy(**load_strategy_params("sector_rotation", SMALL))
    v2 = SwingMomentumStrategy(**load_strategy_params("swing", SMALL))
    got, bt = run_frames(rot, bars, SWING_DAYS)
    want, _ = run_frames(v2, bars, SWING_DAYS)
    assert decisions(got) == decisions(want) and len(decisions(got)) == 2
    assert bt.risk.instrument == "ETF"
    assert got.fills["charges"].sum() < want.fills["charges"].sum()  # no 0.1% STT
