"""Run one research backtest, write its outputs and log it as a trial.

    uv run python -m nsealgo.backtest --strategy NAME --period dev --cost-tier base

Writes research/runs/<stamp>_<strategy>_<period>_<tier>/ (trades.parquet,
fills.parquet, equity.parquet, rejections.parquet, metrics.json) and appends one line to
research/trials.jsonl. The holdout period needs --run-holdout and runs once per
strategy version. Backtests never read the KILL file (see docs/engine.md).

A strategy's reference symbols (e.g. an index it reads but never trades) are loaded
with the universe. Missing reference data is printed as a WARNING and recorded in the
trial's `warnings`; the strategy then skips whatever needed it.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from nsealgo.costs import CostConfig, load_cost_config
from nsealgo.data.calendar import IST
from nsealgo.data.store import CLEAN_DIR, connect
from nsealgo.engine.backtest import Backtester, BacktestResult
from nsealgo.engine.config import (
    MARGIN_CONFIG_PATH,
    RISK_CONFIG_PATH,
    STRATEGY_CONFIG_DIR,
    load_margin_config,
    load_risk_config,
    load_strategy_params,
)
from nsealgo.engine.loader import (
    RESEARCH_CONFIG_PATH,
    UNIVERSE_PATH,
    HoldoutLockedError,
    Period,
    load_calendar,
    load_research_config,
    load_universe,
    market_chunks,
    resolve_period,
    session_counts,
)
from nsealgo.engine.sessions import TradingCalendar
from nsealgo.reporting.metrics import compute_metrics
from nsealgo.reporting.trials import TRIALS_PATH, append_trial, git_state, holdout_already_run
from nsealgo.settings import REPO_ROOT
from nsealgo.strategies import make_strategy
from nsealgo.strategies.base import Strategy

COSTS_PATH = REPO_ROOT / "config" / "costs.yaml"
RUNS_DIR = REPO_ROOT / "research" / "runs"


@dataclass(frozen=True)
class RunPaths:
    clean_dir: Path = CLEAN_DIR
    trials: Path = TRIALS_PATH
    runs_dir: Path = RUNS_DIR
    risk: Path = RISK_CONFIG_PATH
    margins: Path = MARGIN_CONFIG_PATH
    costs: Path = COSTS_PATH
    research: Path = RESEARCH_CONFIG_PATH
    universe: Path = UNIVERSE_PATH
    strategies: Path = STRATEGY_CONFIG_DIR


def coverage_warnings(counts: dict[str, int], sessions: int, period: Period) -> list[str]:
    """Warnings for reference symbols with bars on fewer than all `sessions` of the period."""
    span = f"{period.start}..{period.end}"
    out = []
    for symbol, n in counts.items():
        if n == 0:
            out.append(
                f"reference symbol {symbol!r} has no bars in {span}: the strategy skips "
                "what needs it (e.g. the market filter) for the whole run"
            )
        elif n < sessions:
            out.append(
                f"reference symbol {symbol!r} has bars on {n} of {sessions} sessions in "
                f"{span}: the strategy skips what needs it where they are missing"
            )
    return out


def _simulate(
    strategy: Strategy,
    period: Period,
    *,
    costs: CostConfig,
    cost_tier: str,
    brokerage: str,
    universe: list[str],
    allow_holdout: bool,
    paths: RunPaths,
) -> tuple[BacktestResult, Backtester, list[str]]:
    research = load_research_config(paths.research)
    con = connect(paths.clean_dir)
    calendar = TradingCalendar.from_frame(load_calendar(con, period.start, period.end))
    refs = [s for s in strategy.reference_symbols if s not in universe]
    counts = session_counts(
        con,
        refs,
        (period.start, period.end),
        research=research,
        allow_holdout=allow_holdout,
    )
    chunks = market_chunks(
        con,
        strategy.timeframe,
        universe + refs,
        list(calendar.sessions),
        lookback_sessions=strategy.lookback_sessions,
        research=research,
        allow_holdout=allow_holdout,
    )
    bt = Backtester(
        strategy,
        universe=universe,
        calendar=calendar,
        risk_config=load_risk_config(paths.risk),
        margins=load_margin_config(paths.margins),
        costs=costs,
        brokerage_preset=brokerage,
        slippage_bps=costs.slippage_bps_per_side[cost_tier],
        mode="backtest",
        kill_file=None,
    )
    warnings = coverage_warnings(counts, len(calendar.sessions), period)
    return bt.run(chunks), bt, warnings


def _write_outputs(run_dir: Path, result: BacktestResult, metrics: dict[str, Any]) -> None:
    run_dir.mkdir(parents=True, exist_ok=False)
    result.trades.to_parquet(run_dir / "trades.parquet", index=False)
    result.fills.to_parquet(run_dir / "fills.parquet", index=False)
    result.equity.to_parquet(run_dir / "equity.parquet", index=False)
    result.rejections.astype({"now": "object"}).to_parquet(
        run_dir / "rejections.parquet", index=False
    )
    text = json.dumps(metrics, indent=2, sort_keys=True, default=str)
    (run_dir / "metrics.json").write_text(text + "\n", encoding="utf-8")


def _check_inputs(
    strategy: Strategy,
    period_label: str,
    cost_tier: str,
    brokerage: str | None,
    allow_holdout: bool,
    paths: RunPaths,
) -> tuple[Period, CostConfig, str]:
    """Resolve the period (holdout lock, once per version) and validate the cost tier."""
    research = load_research_config(paths.research)
    period = resolve_period(period_label, research, allow_holdout=allow_holdout)
    if period.holdout and holdout_already_run(paths.trials, strategy.name, strategy.version):
        raise HoldoutLockedError(f"holdout already run for {strategy.name} {strategy.version}")
    costs = load_cost_config(paths.costs)
    if cost_tier not in costs.slippage_bps_per_side:
        raise ValueError(f"unknown cost tier {cost_tier!r}")
    preset = brokerage or costs.active_brokerage
    if preset not in costs.brokerage_presets:
        raise ValueError(f"unknown brokerage preset {preset!r}")
    return period, costs, preset


def _trial_record(
    strategy: Strategy,
    period: Period,
    cost_tier: str,
    slippage_bps: float,
    preset: str,
    universe: list[str],
    capital: float,
    metrics: dict[str, Any],
    run_at: datetime,
    run_dir: Path,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "run_at": run_at.isoformat(),
        **git_state(),
        "strategy": strategy.name,
        "strategy_version": strategy.version,
        "params": strategy.params(),
        "product": str(strategy.product),
        "timeframe": strategy.timeframe,
        "period": {"label": period.label, "start": period.start, "end": period.end},
        "holdout": period.holdout,
        "cost_tier": cost_tier,
        "slippage_bps_per_side": slippage_bps,
        "brokerage_preset": preset,
        # No broker charges or no slippage: a labelled reference, never a tradeable result.
        "reference_tier": preset == "zero" or slippage_bps == 0,
        "universe": universe,
        "capital": capital,
        "sizing_basis": metrics["sizing_basis"],
        "metrics": metrics,
        "warnings": warnings,
        "run_dir": str(run_dir),
    }


def run_backtest(
    strategy: Strategy,
    *,
    period_label: str,
    cost_tier: str,
    brokerage: str | None = None,
    symbols: list[str] | None = None,
    allow_holdout: bool = False,
    paths: RunPaths | None = None,
) -> dict[str, Any]:
    """Run, write outputs, append the trial record and return it."""
    paths = paths or RunPaths()
    period, costs, preset = _check_inputs(
        strategy, period_label, cost_tier, brokerage, allow_holdout, paths
    )
    universe = symbols or load_universe(paths.universe)
    result, bt, warnings = _simulate(
        strategy,
        period,
        costs=costs,
        cost_tier=cost_tier,
        brokerage=preset,
        universe=universe,
        allow_holdout=allow_holdout,
        paths=paths,
    )
    capital = float(bt.portfolio.capital)
    metrics = compute_metrics(
        result.trades,
        result.equity,
        capital,
        halt=result.halt,
        rejections=result.rejections,
        fallback_exits=result.fallback_exits,
        sizing_basis=bt.portfolio.sizing,
    )
    run_at = datetime.now(IST)
    run_dir = paths.runs_dir / f"{run_at:%Y%m%d-%H%M%S}_{strategy.name}_{period.label}_{cost_tier}"
    _write_outputs(run_dir, result, metrics)
    slippage = float(costs.slippage_bps_per_side[cost_tier])
    record = _trial_record(
        strategy,
        period,
        cost_tier,
        slippage,
        preset,
        universe,
        capital,
        metrics,
        run_at,
        run_dir,
        warnings,
    )
    append_trial(paths.trials, record)
    return record


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m nsealgo.backtest", description=__doc__)
    p.add_argument("--strategy", required=True)
    p.add_argument("--period", default="dev", choices=["dev", "validation", "holdout"])
    p.add_argument("--cost-tier", default="base")
    p.add_argument(
        "--params",
        default="{}",
        help="JSON object merged over config/strategies/<strategy>.yaml (nested keys merge)",
    )
    p.add_argument("--symbols", default=None, help="comma-separated; default config/universe.yaml")
    p.add_argument("--brokerage", default=None, help="brokerage preset; default costs.yaml active")
    p.add_argument("--run-holdout", action="store_true", help="human-only: run the holdout once")
    return p


def main(argv: list[str] | None = None, paths: RunPaths | None = None) -> int:
    args = _parser().parse_args(argv)
    paths = paths or RunPaths()
    try:
        params = load_strategy_params(args.strategy, json.loads(args.params), paths.strategies)
        strategy = make_strategy(args.strategy, params)
    except KeyError as e:
        print(f"error: {e.args[0]}", file=sys.stderr)
        return 2
    except ValueError as e:  # bad JSON or parameters the strategy rejects
        print(f"error: {e}", file=sys.stderr)
        return 2
    symbols = args.symbols.split(",") if args.symbols else None
    try:
        record = run_backtest(
            strategy,
            period_label=args.period,
            cost_tier=args.cost_tier,
            brokerage=args.brokerage,
            symbols=symbols,
            allow_holdout=args.run_holdout,
            paths=paths,
        )
    except HoldoutLockedError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    m = record["metrics"]
    keys = [
        "trades",
        "net_expectancy_rs",
        "net_expectancy_bps",
        "profit_factor",
        "max_drawdown_pct",
        "sharpe_daily_annualized",
        "cost_share_of_gross",
    ]
    print(json.dumps({k: m.get(k) for k in keys}, indent=2))
    for warning in record["warnings"]:
        print(f"WARNING: {warning}")
    if record["reference_tier"]:
        print("REFERENCE TIER: no broker charges and/or no slippage; not a tradeable result")
    print(f"outputs: {record['run_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
