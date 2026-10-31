"""Build the mainboard IPO table: data/raw/ipo/ -> data/clean/ipo/.

    uv run python scripts/build_ipo.py

Run scripts/download_ipo.py, scripts/download_bhavcopy.py and scripts/download_ipo_boa.py
first. Writes ipos.parquet and ipos.csv (one row per issue, columns in
nsealgo.data.ipo_build.CLEAN_COLS; docs/data.md describes them) and manifest.json
(row counts, statuses, check counts, the pdftotext version and SHA-256 of every raw file
read). data/clean/ipo/ is rewritten; nothing else is touched. Needs xpdf pdftotext 4.x on
PATH (Git for Windows ships it).
"""

import hashlib
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from nsealgo.data.ipo_build import assemble
from nsealgo.data.ipo_read import (
    bhavcopy_paths,
    load_exceptions,
    read_boa,
    read_issues,
    read_listings,
)
from nsealgo.settings import REPO_ROOT

RAW = REPO_ROOT / "data" / "raw" / "ipo"
OUT = REPO_ROOT / "data" / "clean" / "ipo"
CACHE = OUT / "_cache"  # advert text and bhavcopy first-seen rows, keyed by their inputs


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_hashes() -> dict:
    groups = {
        "nse_past_issues": sorted((RAW / "nse_past_issues").glob("*.json")),
        "nse_ipo_detail": sorted((RAW / "nse_ipo_detail").glob("*.json")),
        "nse_boa": sorted((RAW / "nse_boa").glob("*")),
    }
    out: dict = {k: {p.name: _sha(p) for p in v} for k, v in groups.items()}
    bhav = hashlib.sha256()
    paths = bhavcopy_paths(RAW)
    for p in paths:
        bhav.update(f"{p.name}:{_sha(p)}\n".encode())
    out["bhavcopy"] = {
        "files": len(paths),
        "first": paths[0].name,
        "last": paths[-1].name,
        "sha256_of_name_hash_lines": bhav.hexdigest(),
    }
    return out


def main() -> None:
    issues = read_issues(RAW)
    listings, first_session, last_session = read_listings(RAW, issues, CACHE)
    lots = dict(zip(issues["issue_id"], issues["lot_size"], strict=True))
    lots = {k: int(v) for k, v in lots.items() if v == v}  # NaN != NaN
    boa = read_boa(RAW, CACHE, lots)
    clean = assemble(issues, listings, boa, last_session, load_exceptions())
    OUT.mkdir(parents=True, exist_ok=True)
    clean.to_parquet(OUT / "ipos.parquet", index=False)
    clean.to_csv(OUT / "ipos.csv", index=False)
    checks = Counter(c for s in clean["checks"] for c in s.split(";") if c)
    version = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True)
    manifest = {
        "built_at": datetime.now(UTC).isoformat(),
        "rows": len(clean),
        "status": dict(Counter(clean["status"])),
        "listing_match": dict(Counter(clean["listing_match"].fillna("none"))),
        "failed_checks": dict(checks),
        "bhavcopy_sessions": [first_session.isoformat(), last_session.isoformat()],
        "pdftotext": (version.stdout or version.stderr).splitlines()[0],
        "raw_sha256": _raw_hashes(),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "raw_sha256"}, indent=2))


if __name__ == "__main__":
    main()
