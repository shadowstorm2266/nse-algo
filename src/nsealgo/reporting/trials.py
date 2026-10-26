"""Append-only research trial log, research/trials.jsonl.

Every research run appends one JSON line. The file is the trial count for the
Deflated Sharpe Ratio, so lines are never edited or deleted.
"""

import json
import subprocess
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from nsealgo.settings import REPO_ROOT

TRIALS_PATH = REPO_ROOT / "research" / "trials.jsonl"
REQUIRED = (
    "run_at",
    "git_hash",
    "git_dirty",
    "strategy",
    "strategy_version",
    "params",
    "period",
    "cost_tier",
    "metrics",
)


def _git(args: list[str], root: Path) -> str:
    out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def git_state(root: Path = REPO_ROOT) -> dict[str, Any]:
    """HEAD hash and whether tracked/untracked files differ (the trial log itself excluded)."""
    try:
        head = _git(["rev-parse", "HEAD"], root)
        status = _git(["status", "--porcelain", "--", ".", ":!research/trials.jsonl"], root)
    except (OSError, subprocess.CalledProcessError):
        return {"git_hash": "unknown", "git_dirty": True}
    return {"git_hash": head, "git_dirty": bool(status)}


def _default(x: Any) -> Any:
    if isinstance(x, (date, datetime)):
        return x.isoformat()
    if isinstance(x, Decimal):
        return float(x)
    raise TypeError(f"not JSON serializable: {type(x).__name__}")


def append_trial(path: Path, record: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED if k not in record]
    if missing:
        raise ValueError(f"trial record missing {missing}")
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, default=_default)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def read_trials(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def holdout_already_run(path: Path, strategy: str, version: str) -> bool:
    return any(
        t.get("holdout") and t["strategy"] == strategy and t["strategy_version"] == version
        for t in read_trials(path)
    )
