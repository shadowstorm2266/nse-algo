"""Build the ETF proxy dataset (data/clean/etf_proxy/) from data/raw/indices.

    uv run python scripts/build_etf_proxy.py

Series and expense ratios come from config/etf_proxy.yaml; the construction is in
src/nsealgo/data/etf_proxy.py. Only the sessions of data/clean/calendar are kept, so
run it after scripts/build_data.py (which clears data/clean). Writes bars.parquet and
manifest.json (settings, the SHA-256 of every raw file read, rows and date range).
data/raw is only read.
"""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from nsealgo.data.etf_proxy import (
    DAYS_PER_YEAR,
    REBASE_TO,
    build_proxies,
    load_etf_proxy_config,
)
from nsealgo.data.store import CLEAN_DIR, ETF_PROXY_FILE, write_etf_proxy
from nsealgo.settings import REPO_ROOT


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    cfg = load_etf_proxy_config()
    cal = pd.read_parquet(CLEAN_DIR / "calendar" / "calendar.parquet")
    sessions = sorted(pd.to_datetime(cal["session_date"]).dt.date)
    bars = build_proxies(cfg, sessions)
    out = write_etf_proxy(bars, CLEAN_DIR)
    sources = {}
    for symbol, s in sorted(cfg.series.items()):
        for kind in ("price", "tri"):
            path = cfg.raw_dir / f"{s.index}_{kind}.csv"
            sources[f"{symbol}:{kind}"] = {
                "file": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": _sha256(path),
            }
    manifest = {
        "built_at": datetime.now(UTC).isoformat(),
        "file": ETF_PROXY_FILE.as_posix(),
        "rebase_to": REBASE_TO,
        "accrual": f"(1 - expense_ratio / {DAYS_PER_YEAR}) ^ calendar days",
        "series": {k: v.model_dump() for k, v in sorted(cfg.series.items())},
        "sessions": len(sessions),
        "first_session": str(sessions[0]),
        "last_session": str(sessions[-1]),
        "rows": len(bars),
        "sources": sources,
    }
    (out.parent / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    print(f"{len(bars)} rows, {bars['symbol'].nunique()} series, {sessions[0]}..{sessions[-1]}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
