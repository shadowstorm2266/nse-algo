"""Print markdown tables for research runs. Numbers only, no verdicts.

    uv run python scripts/report_runs.py summary LABEL=RUN_DIR [LABEL=RUN_DIR ...]
    uv run python scripts/report_runs.py detail RUN_DIR [--top 5] [--sort METRIC]

`summary`: one row per run from its metrics.json and its research/trials.jsonl record.
`detail`: one run broken down by year, side, exit reason and symbol (top and bottom N
by `--sort`, default net bps per trade, which does not depend on position size), plus
turnover and costs by the year of each fill, holding periods, position-cap skips and
rejections. `--all-symbols` lists every symbol instead of the top and bottom N.
Reads run outputs only; it runs no backtest and logs no trial.

Turnover is one-way: (rupees bought + sold) / 2 / capital. Costs are charges +
slippage. "Per year" in the summary is the run total over (sessions / 252). Runs written
before fills.parquet existed take both from trades.parquet, with each round trip's costs
on its exit date (exact when entry and exit fall in the same year, as for MIS).
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

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
from nsealgo.reporting.metrics import TRADING_DAYS
from nsealgo.reporting.trials import TRIALS_PATH, read_trials

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
    args = p.parse_args(argv)
    if args.cmd == "summary":
        print(summary(args.runs))
    else:
        print(detail(args.run, args.top, args.sort, args.all_symbols))
    return 0


if __name__ == "__main__":
    sys.exit(main())
