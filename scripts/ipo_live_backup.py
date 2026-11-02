"""Back up data/live/ipo/ to its own git repository (GitHub: nse-algo-live-data, private).

    uv run python scripts/ipo_live_backup.py init    # create the local git directory once
    uv run python scripts/ipo_live_backup.py run     # commit and push now
    uv run python scripts/ipo_live_backup.py check   # can this environment push? (ls-remote)

scripts/record_ipo_live.py calls backup() after the scheduled run for the 19:30 slot
(config/ipo_live.yaml). The git directory is a bare repository outside the main repo.
Every git command names it and the work tree (--git-dir, --work-tree) and runs from inside
it, so git never discovers or touches the main repo; git only reads the work tree. Files
are stored byte for byte (core.autocrlf false, '* -text'). Credential prompts are off, so
a scheduled push fails instead of waiting for input.

Append-only check before each commit: every staged change must be a new file, or one of
APPENDABLE whose committed content is a prefix of its new content. Anything else (a
changed or deleted snapshot) is unstaged and raised as an error; nothing is committed.
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import time
from pathlib import Path

import yaml

from nsealgo.settings import REPO_ROOT

CONFIG = REPO_ROOT / "config" / "ipo_live.yaml"
WORK_TREE = REPO_ROOT / "data" / "live" / "ipo"
APPENDABLE = ("run_log.jsonl", "bhavcopy/misses.jsonl", "decisions.jsonl")
NO_PROMPTS = {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}


class BackupError(Exception):
    pass


@dataclass(frozen=True)
class BackupConfig:
    git_dir: Path
    work_tree: Path
    remote: str
    branch: str


@dataclass(frozen=True)
class LiveConfig:
    pdftotext: str
    backup: BackupConfig
    backup_after: time  # the slot whose scheduled run backs up


def load_live_config(path: Path = CONFIG, work_tree: Path = WORK_TREE) -> LiveConfig:
    cfg = yaml.safe_load(path.read_text("utf-8"))
    b = cfg["backup"]
    return LiveConfig(
        pdftotext=cfg["pdftotext"],
        backup=BackupConfig(Path(b["git_dir"]), work_tree, b["remote"], b["branch"]),
        backup_after=time.fromisoformat(b["after_slot"]),
    )


def git(cfg: BackupConfig, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    cmd = ["git", "-c", "core.autocrlf=false", f"--git-dir={cfg.git_dir}"]
    cmd += [f"--work-tree={cfg.work_tree}", *args]
    env = os.environ | NO_PROMPTS
    done = subprocess.run(cmd, cwd=cfg.git_dir, capture_output=True, env=env, check=False)
    if check and done.returncode != 0:
        err = done.stderr.decode("utf-8", "replace").strip()[-400:]
        raise BackupError(f"git {' '.join(args[:2])} failed: {err}")
    return done


def init(cfg: BackupConfig) -> None:
    if cfg.git_dir.exists():
        raise BackupError(f"{cfg.git_dir} already exists")
    cfg.git_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", "--bare", f"--initial-branch={cfg.branch}", str(cfg.git_dir)],
        cwd=cfg.git_dir.parent,
        check=True,
        capture_output=True,
    )
    (cfg.git_dir / "info").mkdir(exist_ok=True)
    (cfg.git_dir / "info" / "attributes").write_text("* -text\n", encoding="utf-8")
    git(cfg, "config", "core.autocrlf", "false")


def staged_problems(cfg: BackupConfig) -> list[str]:
    """Staged changes that are not appends (empty list if all are)."""
    out = git(cfg, "diff", "--cached", "--name-status", "--no-renames", "-z").stdout
    parts = out.decode("utf-8").split("\0")[:-1]
    problems = []
    for status, path in zip(parts[::2], parts[1::2], strict=True):
        if status == "A":
            continue
        if status == "M" and path in APPENDABLE:
            old = git(cfg, "show", f"HEAD:{path}").stdout
            if git(cfg, "show", f":{path}").stdout.startswith(old):
                continue
        problems.append(f"{status} {path}")
    return problems


def backup(cfg: BackupConfig, message: str) -> dict:
    """Commit everything new under the work tree and push. Returns what happened; raises
    BackupError if the repo is not set up, a change is not an append, or the push fails."""
    if not (cfg.git_dir / "HEAD").exists():
        raise BackupError(f"{cfg.git_dir} is not set up (scripts/ipo_live_backup.py init)")
    git(cfg, "add", "-A")
    problems = staged_problems(cfg)
    if problems:
        git(cfg, "reset", "-q")
        raise BackupError(f"not append-only, nothing committed: {'; '.join(problems[:10])}")
    result: dict = {"committed": False}
    if git(cfg, "diff", "--cached", "--quiet", check=False).returncode != 0:
        git(cfg, "commit", "-q", "-m", message)
        head = git(cfg, "rev-parse", "--short", "HEAD").stdout.decode().strip()
        result = {"committed": True, "commit": head}
    if git(cfg, "remote", "get-url", cfg.remote, check=False).returncode != 0:
        return result | {"pushed": False, "note": f"no remote {cfg.remote!r}; committed locally"}
    git(cfg, "push", "-q", cfg.remote, f"HEAD:refs/heads/{cfg.branch}")
    return result | {"pushed": True}


def check(cfg: BackupConfig) -> dict:
    """Whether this environment can push to the remote, credentials included: a dry-run
    push authenticates against the remote's push service without sending anything."""
    if not (cfg.git_dir / "HEAD").exists():
        return {"ok": False, "error": f"{cfg.git_dir} is not set up"}
    url = git(cfg, "remote", "get-url", cfg.remote, check=False)
    if url.returncode != 0:
        return {"ok": False, "error": f"no remote {cfg.remote!r}"}
    ref = f"HEAD:refs/heads/{cfg.branch}"
    done = git(cfg, "push", "--dry-run", "--porcelain", cfg.remote, ref, check=False)
    err = done.stderr.decode("utf-8", "replace").strip()[-300:]
    out = done.stdout.decode("utf-8", "replace").strip()[-300:]
    remote = url.stdout.decode().strip()
    return {"ok": done.returncode == 0, "remote": remote, "dry_run": out, "error": err}


def main(argv: list[str]) -> int:
    cfg = load_live_config().backup
    if argv == ["init"]:
        init(cfg)
        print(f"created {cfg.git_dir}")
    elif argv == ["run"]:
        print(backup(cfg, "manual backup"))
    elif argv == ["check"]:
        print(check(cfg))
    else:
        raise SystemExit("usage: ipo_live_backup.py init | run | check")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
