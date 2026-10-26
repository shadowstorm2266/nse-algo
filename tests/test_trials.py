import json
from pathlib import Path

import pandas as pd
import pytest

from nsealgo import strategies
from nsealgo.backtest import RunPaths, main, run_backtest
from nsealgo.data.calendar import build_calendar
from nsealgo.data.features import daily_bars, daily_features, rvol_profile
from nsealgo.data.resample import resample_bars, with_available_at
from nsealgo.data.store import write_bars, write_calendar, write_symbol_table
from nsealgo.engine.loader import (
    HoldoutLockedError,
    check_holdout,
    load_research_config,
    resolve_period,
)
from nsealgo.engine.types import Product, Side
from nsealgo.reporting.trials import REQUIRED, append_trial, git_state, read_trials
from tests.data_helpers import business_days, many_sessions
from tests.engine_helpers import ScriptedStrategy, entry, exit_, ts

DAYS = business_days("2016-02-01", 3)  # inside the dev period
RECORD = {k: f"v-{k}" for k in REQUIRED}


@pytest.fixture
def paths(tmp_path: Path) -> RunPaths:
    clean = tmp_path / "clean"
    dailies = []
    for i, sym in enumerate(("AAA", "BBB")):
        bars = many_sessions(sym, DAYS, seed=i)
        write_bars(with_available_at(bars, 1), clean, "1m")
        for m in (5, 15):
            write_bars(resample_bars(bars, m), clean, f"{m}m")
        daily = daily_bars(bars)
        dailies.append(daily)
        write_symbol_table(daily_features(daily, DAYS), clean, "features")
        write_symbol_table(rvol_profile(resample_bars(bars, 5), DAYS), clean, "rvol")
    sessions = pd.concat(dailies)[["symbol", "session_date", "n_bars"]]
    write_calendar(build_calendar(sessions, {}, set()), clean)
    return RunPaths(clean_dir=clean, trials=tmp_path / "trials.jsonl", runs_dir=tmp_path / "runs")


@pytest.fixture
def toy(monkeypatch):
    script = {
        ts(DAYS[0], "10:00"): [entry("AAA", Side.BUY, stop=90.0)],
        ts(DAYS[0], "11:00"): [exit_("AAA")],
        ts(DAYS[1], "10:00"): [entry("BBB", Side.SELL, stop=110.0)],
    }
    monkeypatch.setitem(
        strategies.REGISTRY, "toy", lambda: ScriptedStrategy(Product.MIS, "5m", script, "toy")
    )


def test_append_only(tmp_path):
    path = tmp_path / "t.jsonl"
    append_trial(path, RECORD | {"n": 1})
    first = path.read_text(encoding="utf-8")
    append_trial(path, RECORD | {"n": 2})
    text = path.read_text(encoding="utf-8")
    assert text.startswith(first) and text.count("\n") == 2
    assert [t["n"] for t in read_trials(path)] == [1, 2]
    with pytest.raises(ValueError, match="missing"):
        append_trial(path, {"strategy": "x"})


def test_periods_and_holdout_lock():
    cfg = load_research_config()
    assert resolve_period("dev", cfg, allow_holdout=False).holdout is False
    assert resolve_period("validation", cfg, allow_holdout=False).end < cfg.holdout_start
    with pytest.raises(HoldoutLockedError):
        resolve_period("holdout", cfg, allow_holdout=False)
    assert resolve_period("holdout", cfg, allow_holdout=True).holdout is True
    with pytest.raises(HoldoutLockedError):
        check_holdout(cfg.holdout_start, cfg, allow_holdout=False)
    with pytest.raises(ValueError):
        resolve_period("2024", cfg, allow_holdout=True)


def test_cli_end_to_end_writes_outputs_and_one_trial(paths, toy, capsys):
    assert main(["--strategy", "toy", "--period", "dev", "--symbols", "AAA,BBB"], paths) == 0
    (trial,) = read_trials(paths.trials)
    assert set(REQUIRED) <= set(trial)
    assert trial["strategy"] == "toy" and trial["cost_tier"] == "base"
    assert trial["brokerage_preset"] == "shoonya" and trial["reference_tier"] is False
    assert trial["slippage_bps_per_side"] == 3.0 and trial["holdout"] is False
    assert trial["period"]["label"] == "dev" and trial["metrics"]["trades"] == 2
    run_dir = Path(trial["run_dir"])
    trades = pd.read_parquet(run_dir / "trades.parquet")
    assert list(trades["exit_reason"]) == ["strategy", "flat_by"]
    assert len(pd.read_parquet(run_dir / "equity.parquet")) == 3
    assert json.loads((run_dir / "metrics.json").read_text())["trades"] == 2
    pd.read_parquet(run_dir / "rejections.parquet")
    assert '"trades": 2' in capsys.readouterr().out


def test_cli_unknown_strategy(paths, capsys):
    assert main(["--strategy", "nope"], paths) == 2
    assert "unknown strategy 'nope'" in capsys.readouterr().err
    assert not paths.trials.exists()


@pytest.mark.parametrize(
    ("params", "match"),
    [
        ('{"filters": {"nifty_direction": {"enabled": true}}}', "not implemented"),
        ('{"bogus": 1}', "bogus"),
        ("{not json", "error"),
    ],
)
def test_cli_rejects_bad_strategy_params(paths, capsys, params, match):
    assert main(["--strategy", "orb", "--params", params], paths) == 2
    assert match in capsys.readouterr().err
    assert not paths.trials.exists()


def test_cli_orb_logs_yaml_params_with_overrides(paths):
    params = '{"target_r": 3.0, "filters": {"gap": {"enabled": false}}}'
    argv = ["--strategy", "orb", "--symbols", "AAA,BBB", "--params", params]
    assert main(argv, paths) == 0
    (trial,) = read_trials(paths.trials)
    p = trial["params"]
    assert p["target_r"] == 3.0 and p["buffer_pct"] == 0.05 and p["stop"] == "full"
    assert p["filters"]["gap"] == {"enabled": False, "max_abs_pct": 0.8}
    assert trial["strategy"] == "orb" and trial["strategy_version"] == "1"


def test_cli_holdout_needs_the_flag(paths, toy, capsys):
    assert main(["--strategy", "toy", "--period", "holdout"], paths) == 3
    assert "holdout" in capsys.readouterr().err
    assert not paths.trials.exists()


def test_holdout_runs_once_per_strategy_version(paths, toy):
    append_trial(
        paths.trials, RECORD | {"strategy": "toy", "strategy_version": "test", "holdout": True}
    )
    with pytest.raises(HoldoutLockedError, match="already run"):
        run_backtest(
            strategies.make_strategy("toy", {}),
            period_label="holdout",
            cost_tier="base",
            allow_holdout=True,
            paths=paths,
        )


def test_unknown_cost_tier_or_preset(paths, toy):
    s = strategies.make_strategy("toy", {})
    with pytest.raises(ValueError, match="cost tier"):
        run_backtest(s, period_label="dev", cost_tier="cheap", paths=paths)
    with pytest.raises(ValueError, match="preset"):
        run_backtest(s, period_label="dev", cost_tier="base", brokerage="nope", paths=paths)


def test_zero_preset_is_labelled_reference_tier(paths, toy):
    rec = run_backtest(
        strategies.make_strategy("toy", {}),
        period_label="dev",
        cost_tier="base",
        brokerage="zero",
        symbols=["AAA", "BBB"],
        paths=paths,
    )
    assert rec["reference_tier"] is True


def test_zero_slippage_is_labelled_reference_tier(paths, toy, capsys):
    argv = ["--strategy", "toy", "--symbols", "AAA,BBB", "--cost-tier", "none"]
    assert main(argv, paths) == 0
    (trial,) = read_trials(paths.trials)
    assert trial["reference_tier"] is True and trial["brokerage_preset"] == "shoonya"
    assert "REFERENCE TIER" in capsys.readouterr().out


def test_git_state_reads_this_repo():
    state = git_state()
    assert len(state["git_hash"]) == 40 and isinstance(state["git_dirty"], bool)
