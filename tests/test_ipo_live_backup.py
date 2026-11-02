"""Backup of data/live/ipo/ (scripts/ipo_live_backup.py), with real git in temp dirs: new
files are committed and pushed byte for byte, appends to the logs pass, changed or deleted
snapshots are refused, and the recorder backs up only after the scheduled 19:30 run. Also
the pdftotext check on a program that does not exist."""

import subprocess
import sys
from datetime import date, datetime, time

import pytest

from nsealgo.data.calendar import IST
from nsealgo.settings import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import ipo_live_backup
import ipo_live_steps
import record_ipo_live
from ipo_live_backup import BackupConfig, BackupError, LiveConfig, backup, init


def ist(*args: int) -> datetime:
    return datetime(*args, tzinfo=IST)


@pytest.fixture
def repo(tmp_path) -> BackupConfig:
    work = tmp_path / "live"
    work.mkdir()
    cfg = BackupConfig(tmp_path / "backup.git", work, "origin", "main")
    init(cfg)
    ipo_live_backup.git(cfg, "config", "user.name", "test")
    ipo_live_backup.git(cfg, "config", "user.email", "test@example.invalid")
    return cfg


def committed(cfg: BackupConfig) -> list[str]:
    out = ipo_live_backup.git(cfg, "ls-tree", "-r", "--name-only", "HEAD").stdout
    return sorted(out.decode().split())


def test_new_files_are_committed_byte_for_byte(repo):
    snap = repo.work_tree / "BCSSL_20261029" / "20261102T193002+0530.json"
    snap.parent.mkdir()
    snap.write_bytes(b'{"a": 1}\r\n')  # CRLF must survive
    (repo.work_tree / "run_log.jsonl").write_bytes(b'{"run": 1}\n')
    r = backup(repo, "first")
    assert r["committed"] and r["pushed"] is False and "no remote" in r["note"]
    assert committed(repo) == ["BCSSL_20261029/20261102T193002+0530.json", "run_log.jsonl"]
    blob = ipo_live_backup.git(repo, "show", "HEAD:BCSSL_20261029/20261102T193002+0530.json")
    assert blob.stdout == b'{"a": 1}\r\n'
    assert backup(repo, "again")["committed"] is False


def test_log_appends_pass_and_changed_or_deleted_snapshots_are_refused(repo):
    w = repo.work_tree
    snap, log = w / "20261102T193002+0530.json", w / "run_log.jsonl"
    snap.write_bytes(b"one")
    log.write_bytes(b"a\n")
    backup(repo, "first")
    with log.open("ab") as fh:
        fh.write(b"b\n")
    assert backup(repo, "append")["committed"]
    snap.write_bytes(b"two")
    with pytest.raises(BackupError, match="not append-only"):
        backup(repo, "change")
    assert ipo_live_backup.git(repo, "diff", "--cached", "--quiet", check=False).returncode == 0
    snap.write_bytes(b"one")
    log.write_bytes(b"rewritten\n")
    with pytest.raises(BackupError, match=r"M run_log\.jsonl"):
        backup(repo, "rewrite the log")
    log.write_bytes(b"a\nb\n")
    snap.unlink()
    with pytest.raises(BackupError, match="D 20261102T193002"):
        backup(repo, "delete")


def test_the_backup_is_pushed_to_the_remote(repo, tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    ipo_live_backup.git(repo, "remote", "add", "origin", str(remote))
    (repo.work_tree / "x.json").write_bytes(b"1")
    r = backup(repo, "push me")
    assert r["committed"] and r["pushed"]
    cmd = ["git", f"--git-dir={remote}", "log", "--format=%s", "main"]
    assert subprocess.run(cmd, capture_output=True, text=True, check=True).stdout == "push me\n"
    assert ipo_live_backup.check(repo)["ok"]


def test_nothing_happens_without_the_git_directory(tmp_path):
    cfg = BackupConfig(tmp_path / "missing.git", tmp_path, "origin", "main")
    with pytest.raises(BackupError, match="not set up"):
        backup(cfg, "x")
    assert ipo_live_backup.check(cfg)["ok"] is False
    assert not (tmp_path / "missing.git").exists()


def test_pdftotext_check_reports_a_missing_program(tmp_path):
    r = ipo_live_steps.pdftotext_check(str(tmp_path / "nope.exe"))
    assert r["ok"] is False and "error" in r


def test_the_recorder_backs_up_only_after_the_scheduled_1930_run(repo, tmp_path):
    cfg = LiveConfig(str(tmp_path / "nope.exe"), repo, time(19, 30))
    net = ipo_live_steps.Net(
        nse=lambda url, ref: b"[]", archive=lambda url: None, ready=lambda: True
    )
    holidays = {date(2026, 12, 25)}

    def run(at: datetime, scheduled: bool = True) -> ipo_live_steps.Run:
        return record_ipo_live.run_once(
            net, repo.work_tree, holidays, scheduled, lambda: at, {}, cfg
        )

    assert "backup" not in run(ist(2026, 11, 2, 15, 30, 1)).log
    assert "backup" not in run(ist(2026, 11, 2, 19, 30, 5), scheduled=False).log
    r = run(ist(2026, 11, 2, 19, 30, 9))
    assert r.log["backup"]["committed"] and not r.errors
    assert any("no remote" in w for w in r.warnings)
    assert r.log["pdftotext"]["ok"] is False and any("pdftotext" in w for w in r.warnings)
    assert committed(repo) == [
        "current_issue/20261102T153001+0530.json",
        "current_issue/20261102T193005+0530.json",
        "current_issue/20261102T193009+0530.json",
        "run_log.jsonl",
    ]
    message = ipo_live_backup.git(repo, "log", "-1", "--format=%s").stdout.decode().strip()
    assert message == "data after the 2026-11-02T19:30:00+05:30 run"
