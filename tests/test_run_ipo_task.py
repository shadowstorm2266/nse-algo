"""scripts/run_ipo_task.ps1, the Task Scheduler launch wrapper: a launch that fails before
the recorder writes its own log must leave a line in data/live/ipo/launch_failures.jsonl.
Windows only (Windows PowerShell 5.1). Children are this interpreter, so the tests also
show the wrapper's exit code is the child's."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from nsealgo.settings import REPO_ROOT

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell wrapper")

WRAPPER = REPO_ROOT / "scripts" / "run_ipo_task.ps1"
POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def launch(root: Path, *command: str) -> int:
    env = os.environ | {"NSEALGO_LAUNCH_ROOT": str(root), "NSEALGO_LAUNCH_NO_PUSH": "1"}
    cmd = [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(WRAPPER), *command]
    return subprocess.run(cmd, env=env, capture_output=True, timeout=120).returncode


def failures(root: Path) -> list[dict]:
    path = root / "data" / "live" / "ipo" / "launch_failures.jsonl"
    if not path.exists():
        return []
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in raw.replace(b"\\r\\n", b"")
    return [json.loads(x) for x in raw.decode("utf-8").splitlines()]


def test_a_clean_exit_logs_nothing_and_keeps_stdout(tmp_path):
    assert launch(tmp_path, sys.executable, "-c", "print('ok ₹ two words')") == 0
    assert failures(tmp_path) == []
    out = (tmp_path / "data" / "live" / "last_launch_stdout.txt").read_text("utf-8")
    assert out.strip() == "ok ₹ two words"


def test_a_non_zero_exit_is_logged_with_its_code_and_stderr(tmp_path):
    code = "import sys; sys.stderr.write('boom ä\\n'); sys.exit(3)"
    assert launch(tmp_path, sys.executable, "-c", code) == 3
    [row] = failures(tmp_path)
    assert row["exit_code"] == 3 and row["stderr"].strip() == "boom ä"
    assert row["command"] == [sys.executable, "-c", code] and row["start_error"] is None
    assert row["time"].endswith("+05:30")


def test_a_command_that_cannot_start_is_logged_and_lines_are_appended(tmp_path):
    assert launch(tmp_path, sys.executable, "-c", "import sys; sys.exit(2)") == 2
    assert launch(tmp_path, str(tmp_path / "missing" / "uv.exe"), "run") == 1
    first, second = failures(tmp_path)
    assert first["exit_code"] == 2
    assert second["exit_code"] is None and "cannot find the file" in second["start_error"]
