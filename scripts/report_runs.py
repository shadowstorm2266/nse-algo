"""Print markdown tables for research runs. Numbers only, no verdicts.

    uv run python scripts/report_runs.py summary LABEL=RUN_DIR [LABEL=RUN_DIR ...]
    uv run python scripts/report_runs.py detail RUN_DIR [--top 5] [--sort METRIC]
    uv run python scripts/report_runs.py benchmark RUN_DIR [--exclude SYM[,SYM...]]

`summary`: one row per run from its metrics.json and its research/trials.jsonl record.
`detail`: one run broken down by year, side, exit reason and symbol (top and bottom N
by `--sort`, default net bps per trade, which does not depend on position size), plus
turnover and costs by the year of each fill, holding periods, position-cap skips and
rejections. `--all-symbols` lists every symbol instead of the top and bottom N.
`benchmark`: the run against an equal-weight buy-and-hold of its universe
(reporting/benchmark.py: fractional shares, bought at the first session's open with one
base-tier buy, never rebalanced, no sell costs), by calendar year and over the whole
period: return, max drawdown and the run's excess return. An ETF run (instrument ETF)
also gets benchmark 2, the same buy-and-hold of config/etf_proxy.yaml's `benchmark`
series alone; both use ETF charges and the ETF base slippage tier. `--exclude` repeats
the first table with those symbols' trades taken out of the run. It reads daily bars
from data/clean (the ETF proxy dataset for ETF runs), never on or after holdout_start.
Runs no backtest and logs no trial.

Turnover is one-way: (rupees bought + sold) / 2 / capital. Costs are charges +
slippage. "Per year" in the summary is the run total over (sessions / 252). Runs written
before fills.parquet existed take both from trades.parquet, with each round trip's costs
on its exit date (exact when entry and exit fall in the same year, as for MIS).
"""

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from nsealgo.costs import load_cost_config
from nsealgo.data.etf_proxy import load_etf_proxy_config
from nsealgo.data.store import connect
from nsealgo.engine.loader import check_holdout, load_bars, load_research_config
from nsealgo.reporting.benchmark import buy_and_hold, without_symbols
from nsealgo.reporting.breakdown import (
    breakdown,
    cap_skips,
    entry_year,
    holding_days,
    legs_from_fills,
    legs_from_trades,
    yearly_activity,
    yearly_equity,
)
from nsealgo.reporting.metrics import TRADING_DAYS, equity_metrics
from nsealgo.reporting.trials import TRIALS_PATH, read_trials
from nsealgo.settings import REPO_ROOT

COSTS_PATH = REPO_ROOT / "config" / "costs.yaml"
BENCHMARK_TIER = "base"

Col = tuple[str, str, str]  # header, column, format kind
TRADE_COLS: list[Col] = [
    ("Trades", "trades", "int"),
    ("Win %", "win_rate", "pct"),
    ("Avg win Rs", "avg_win", "rs"),
    ("Avg loss Rs", "avg_loss", "rs"),
    ("Gross bps", "gross_bps_per_trade", "bps"),
    ("Cost bps", "cost_bps_per_trade", "bps"),
    ("Net bps", "net_expectancy_bps", "bps"),
    ("PF", "profit_factor", "x"),
    ("Net Rs", "net_pnl", "rs"),
]
SUMMARY_COLS: list[Col] = [
    ("Ref tier", "reference_tier", "flag"),
    ("Sizing", "sizing_basis", "text"),
    *TRADE_COLS[:-1],
    ("Max DD Rs", "max_drawdown_rs", "rs"),
    ("Max DD %", "max_drawdown_pct", "pct100"),
    ("Sharpe (daily, ann.)", "sharpe_daily_annualized", "x"),
    ("Net Rs", "net_pnl", "rs"),
    ("Skipped groups", "skipped_groups", "int"),
    ("Cap skips", "cap_skips", "int"),
    ("Turnover x/yr", "turnover_x_per_year", "x"),
    ("Costs % cap/yr", "costs_pct_capital_per_year", "pct100"),
]
YEAR_COLS: list[Col] = [
    *TRADE_COLS,
    ("Max DD %", "max_drawdown_pct", "pct100"),
    ("Sharpe", "sharpe_daily_annualized", "x"),
]
ACTIVITY_COLS: list[Col] = [
    ("Bought Rs", "buys_rs", "rs"),
    ("Sold Rs", "sells_rs", "rs"),
    ("Turnover x", "turnover_x", "x"),
    ("Charges Rs", "charges_rs", "rs"),
    ("DP Rs (pre-GST)", "dp_rs", "rs"),
    ("Slippage Rs", "slippage_rs", "rs"),
    ("Costs Rs", "costs_rs", "rs"),
    ("Costs % capital", "costs_pct_capital", "pct100"),
]
COMPARE_COLS: list[Col] = [
    ("Run return %", "run_return", "pct100"),
    ("Run max DD %", "run_max_dd", "pct100"),
    ("Benchmark return %", "bench_return", "pct100"),
    ("Benchmark max DD %", "bench_max_dd", "pct100"),
    ("Excess return, pp", "excess", "pp"),
]
SKIP_COLS: list[Col] = [
    ("Symbol", "symbol", "text"),
    ("Price", "price", "rs"),
    ("Rank", "rank", "int"),
]


def fmt(v: Any, kind: str) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    if kind == "text":
        return str(v)
    if kind == "flag":
        return "REFERENCE" if v else ""
    formats = {
        "int": "{:,.0f}",
        "rs": "{:,.0f}",
        "bps": "{:.1f}",
        "x": "{:.2f}",
        "pct100": "{:.1f}%",
        "pp": "{:+.1f}",
    }
    if kind == "pct":
        return f"{v * 100:.1f}%"
    return formats[kind].format(v)


def md_table(rows: pd.DataFrame, cols: list[Col], first: str) -> str:
    head = [first, *(h for h, _, _ in cols)]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for key, r in rows.iterrows():
        cells = [str(key), *(fmt(r.get(c), k) for _, c, k in cols)]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def trial_for(run_dir: Path) -> dict[str, Any]:
    for t in read_trials(TRIALS_PATH):
        if Path(t["run_dir"]).resolve() == run_dir.resolve():
            return t
    raise SystemExit(f"no trial record in {TRIALS_PATH} for {run_dir}")


def activity(run_dir: Path, capital: float) -> tuple[pd.DataFrame, str]:
    """Turnover and costs by year, and where they came from."""
    fills = run_dir / "fills.parquet"
    if fills.is_file():
        return yearly_activity(legs_from_fills(pd.read_parquet(fills)), capital), "fills"
    trades = pd.read_parquet(run_dir / "trades.parquet")
    return yearly_activity(legs_from_trades(trades), capital), "trades (costs on exit date)"


def summary(specs: list[str]) -> str:
    rows = {}
    for spec in specs:
        label, _, path = spec.partition("=")
        run_dir = Path(path)
        m = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        trial = trial_for(run_dir)
        rejected = m["rejections_by_reason"]
        years = m["sessions"] / TRADING_DAYS
        act, _ = activity(run_dir, trial["capital"])
        extra = {
            "reference_tier": trial["reference_tier"],
            "sizing_basis": trial.get("sizing_basis", "current_equity"),
            "skipped_groups": rejected.get("MAX_TRADES_PER_DAY", 0),
            "cap_skips": rejected.get("PRICE_ABOVE_POSITION_CAP", 0),
            "turnover_x_per_year": act["turnover_x"].sum() / years,
            "costs_pct_capital_per_year": act["costs_pct_capital"].sum() / years,
        }
        rows[label] = m | extra
    return md_table(pd.DataFrame.from_dict(rows, orient="index"), SUMMARY_COLS, "Run")


def extras(run_dir: Path, trades: pd.DataFrame, capital: float) -> list[str]:
    """Turnover and costs, holding period, position-cap skips and rejections."""
    act, source = activity(run_dir, capital)
    hold = holding_days(trades)
    rej = pd.read_parquet(run_dir / "rejections.parquet")
    skips = cap_skips(rej)
    skips.index = pd.to_datetime(skips["decision"]).dt.date
    reasons = rej["reason"].value_counts().rename("count").to_frame()
    return [
        f"Turnover and costs by year of each fill (from {source}; capital Rs {capital:,.0f})",
        md_table(act, ACTIVITY_COLS, "Year"),
        f"Holding period, calendar days per trade: median {hold.median():.1f}, "
        f"mean {hold.mean():.1f}, max {hold.max():.1f}",
        f"Entries skipped because one share was above the position cap: {len(skips)} at "
        f"{skips['decision'].nunique()} decisions",
        md_table(skips, SKIP_COLS, "Decision") if len(skips) else "(none)",
        "Rejections by reason",
        md_table(reasons, [("Count", "count", "int")], "Reason") if len(reasons) else "(none)",
    ]


def detail(run_dir: Path, top: int, sort: str, all_symbols: bool = False) -> str:
    trial = trial_for(run_dir)
    # Trials logged before the sizing basis existed sized off current equity.
    fixed = trial.get("sizing_basis", "current_equity") == "fixed_capital"
    trades = pd.read_parquet(run_dir / "trades.parquet")
    equity = pd.read_parquet(run_dir / "equity.parquet")
    years = breakdown(trades, entry_year(trades)).join(
        yearly_equity(equity, trial["capital"], fixed)[
            ["max_drawdown_pct", "sharpe_daily_annualized"]
        ]
    )
    symbols = breakdown(trades, "symbol").sort_values(sort, ascending=False)
    if all_symbols:
        sym_parts = [f"Symbols, by {sort}", md_table(symbols, TRADE_COLS, "Symbol")]
    else:
        sym_parts = [
            f"Symbols: top {top} by {sort}",
            md_table(symbols.head(top), TRADE_COLS, "Symbol"),
            f"Symbols: bottom {top} by {sort}",
            md_table(symbols.tail(top).iloc[::-1], TRADE_COLS, "Symbol"),
        ]
    parts = [
        f"run: {run_dir.name} (tier {trial['cost_tier']}, {trial['brokerage_preset']}, "
        f"sizing {'fixed_capital' if fixed else 'current_equity'})",
        "By year (entry year; Max DD % and Sharpe from that year's sessions)",
        md_table(years, YEAR_COLS, "Year"),
        "By side",
        md_table(breakdown(trades, "side"), TRADE_COLS, "Side"),
        "By exit reason",
        md_table(breakdown(trades, "exit_reason"), TRADE_COLS, "Exit"),
        *sym_parts,
        *extras(run_dir, trades, trial["capital"]),
    ]
    return "\n\n".join(parts)


def returns_and_drawdowns(equity: pd.DataFrame, capital: float, fixed: bool) -> pd.DataFrame:
    """Return % and max drawdown % per calendar year (in-year) and over the whole period
    ("All"), on the given sizing basis (definitions in reporting/metrics.py)."""
    cols = ["total_return_pct", "max_drawdown_pct"]
    out = yearly_equity(equity, capital, fixed)[cols]
    whole = equity_metrics(equity, capital, capital if fixed else None)
    out.loc["All"] = [whole[c] for c in cols]
    return out


def compare(run: pd.DataFrame, bench: pd.DataFrame, capital: float, fixed: bool) -> pd.DataFrame:
    r = returns_and_drawdowns(run, capital, fixed)
    b = returns_and_drawdowns(bench, capital, fixed=False)
    out = pd.DataFrame(
        {
            "run_return": r["total_return_pct"],
            "run_max_dd": r["max_drawdown_pct"],
            "bench_return": b["total_return_pct"],
            "bench_max_dd": b["max_drawdown_pct"],
        }
    )
    out["excess"] = out["run_return"] - out["bench_return"]
    return out


def benchmark_equity(trial: dict[str, Any]) -> tuple[pd.DataFrame, list[tuple[str, pd.DataFrame]]]:
    """(daily bars of the trial's universe over its period, [(label, buy-and-hold
    equity)]: the universe's equal weight, then for ETF runs the benchmark series)."""
    instrument = trial.get("instrument", "EQ")  # trials before the field were equity
    start, end = (date.fromisoformat(str(trial["period"][k])) for k in ("start", "end"))
    check_holdout(end, load_research_config(), allow_holdout=False)
    con = connect()
    bars = load_bars(con, "1d", trial["universe"], start, end, instrument=instrument)
    costs = load_cost_config(COSTS_PATH)
    preset = costs.active_brokerage
    bps = costs.slippage_table(instrument)[BENCHMARK_TIER]
    delivery = costs.brokerage_presets[preset].delivery

    def hold(b: pd.DataFrame, what: str) -> tuple[str, pd.DataFrame]:
        equity = buy_and_hold(b, trial["capital"], costs.rates, delivery, bps, instrument)
        days = pd.to_datetime(equity["session_date"])
        label = (
            f"{what}, fractional units, bought at the {days.iloc[0]:%Y-%m-%d} open with "
            f"one {BENCHMARK_TIER}-tier {instrument} buy ({preset}, {bps} bps), held to the "
            f"{days.iloc[-1]:%Y-%m-%d} close, no rebalancing, no sell costs"
        )
        return label, equity

    n = bars["symbol"].nunique()
    out = [hold(bars, f"benchmark: equal-weight buy-and-hold of the run's {n} symbols")]
    if instrument == "ETF":
        sym = load_etf_proxy_config().benchmark
        b2 = load_bars(con, "1d", [sym], start, end, instrument=instrument)
        out.append(hold(b2, f"benchmark 2: buy-and-hold of {sym}"))
    return bars, out


def bench_report(run_dir: Path, exclude: list[str]) -> str:
    trial = trial_for(run_dir)
    capital = trial["capital"]
    fixed = trial.get("sizing_basis", "current_equity") == "fixed_capital"
    bars, benches = benchmark_equity(trial)
    equity = pd.read_parquet(run_dir / "equity.parquet")
    parts = [
        f"run: {run_dir.name} (tier {trial['cost_tier']}, sizing {trial.get('sizing_basis')})",
        "Return and max drawdown by calendar year (in-year) and over the whole period; "
        "excess = run return - benchmark return, in percentage points",
    ]
    for label, b in benches:
        parts += [label, md_table(compare(equity, b, capital, fixed), COMPARE_COLS, "Year")]
    bench = benches[0][1]
    if exclude:
        fills = pd.read_parquet(run_dir / "fills.parquet")
        trades = pd.read_parquet(run_dir / "trades.parquet")
        ex = without_symbols(equity, fills, bars, exclude)
        kept = trades.loc[~trades["symbol"].isin(exclude), "net_pnl"].sum()
        parts += [
            f"Run without the trades of {', '.join(exclude)} (their fills' cash flows and "
            "holdings taken out of each session's equity; nothing else changed)",
            md_table(compare(ex, bench, capital, fixed), COMPARE_COLS, "Year"),
            f"Check: final equity - capital = {ex['equity'].iloc[-1] - capital:,.2f}; "
            f"net P&L of the other trades in trades.parquet = {kept:,.2f}",
        ]
    return "\n\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summary")
    s.add_argument("runs", nargs="+", help="LABEL=RUN_DIR")
    d = sub.add_parser("detail")
    d.add_argument("run", type=Path)
    d.add_argument("--top", type=int, default=5)
    d.add_argument("--sort", default="net_expectancy_bps", help="trade metric to rank symbols")
    d.add_argument("--all-symbols", action="store_true", help="list every symbol")
    b = sub.add_parser("benchmark")
    b.add_argument("run", type=Path)
    b.add_argument("--exclude", default="", help="comma-separated symbols to take out")
    args = p.parse_args(argv)
    if args.cmd == "summary":
        print(summary(args.runs))
    elif args.cmd == "detail":
        print(detail(args.run, args.top, args.sort, args.all_symbols))
    else:
        print(bench_report(args.run, [s for s in args.exclude.split(",") if s]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
