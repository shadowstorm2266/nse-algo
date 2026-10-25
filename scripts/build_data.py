"""Build data/clean and the data-quality reports from data/raw.

    uv run python scripts/build_data.py

Writes data/clean/** (rebuilt from scratch), research/data_quality.csv,
research/data_quality_events.csv, research/short_sessions.csv and
config/universe.yaml. data/raw is only read.
"""

import shutil
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

from nsealgo.data.build import finish, process_symbol
from nsealgo.data.calendar import load_holidays
from nsealgo.data.config import load_data_config
from nsealgo.data.raw import raw_symbols
from nsealgo.data.store import write_calendar
from nsealgo.data.universe import UNIVERSE_WARNING, rank_by_turnover, write_universe_yaml
from nsealgo.settings import REPO_ROOT

RESEARCH = REPO_ROOT / "research"


def _reset_clean_dir(clean_dir: Path) -> None:
    # Only ever delete our own output directory.
    if clean_dir.resolve() != (REPO_ROOT / "data" / "clean").resolve():
        raise RuntimeError(f"refusing to delete unexpected clean_dir {clean_dir}")
    if clean_dir.exists():
        shutil.rmtree(clean_dir)
    clean_dir.mkdir(parents=True)


def _write_reports(out: dict[str, pd.DataFrame]) -> None:
    out["quality"].to_csv(RESEARCH / "data_quality.csv", index=False)
    events = out["events"].sort_values(["symbol", "session_date", "kind", "ts"])
    events.to_csv(RESEARCH / "data_quality_events.csv", index=False)
    out["short_sessions"].to_csv(RESEARCH / "short_sessions.csv", index=False)


def main() -> int:
    cfg = load_data_config()
    _reset_clean_dir(cfg.clean_dir)
    symbols = raw_symbols(cfg.raw_dir)
    results = []
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {symbol}", flush=True)
        results.append(process_symbol(cfg, symbol))
    out = finish(results, cfg, load_holidays(REPO_ROOT / "config" / "holidays.csv"))
    write_calendar(out["calendar"], cfg.clean_dir)
    _write_reports(out)

    year_end = cfg.clean_start.replace(year=cfg.clean_start.year + 1) - timedelta(days=1)
    ranked = rank_by_turnover(out["daily"], cfg.clean_start, year_end, cfg.universe_size)
    write_universe_yaml(REPO_ROOT / "config" / "universe.yaml", ranked, cfg.clean_start, year_end)
    print(f"WARNING: {UNIVERSE_WARNING}")
    if len(ranked) < cfg.universe_size:
        print(f"WARNING: only {len(ranked)} symbols available for a {cfg.universe_size} universe")

    unclassified = out["short_sessions"].query("status == 'UNCLASSIFIED'")
    if not unclassified.empty:
        print(f"WARNING: short sessions not in config/data.yaml:\n{unclassified}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
