"""scripts/venv_run.py: the venv's packages on the base interpreter, the target as __main__."""

import subprocess
import sys
from pathlib import Path

import pytest

from nsealgo.settings import REPO_ROOT

VENV_RUN = REPO_ROOT / "scripts" / "venv_run.py"
BASE = getattr(sys, "_base_executable", sys.executable)


def test_a_script_runs_with_the_venv_packages_and_its_own_argv(tmp_path):
    script = tmp_path / "probe.py"
    script.write_text(
        "import sys, nsealgo, yaml\n"
        "print(__name__, sys.argv[1:], sys.path[0] == sys.argv[0].rsplit('\\\\', 1)[0])\n"
        "sys.exit(5)\n",
        encoding="utf-8",
    )
    done = subprocess.run(
        [BASE, "-s", str(VENV_RUN), str(script), "--scheduled", "x y"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert done.returncode == 5, done.stderr
    assert done.stdout.strip() == "__main__ ['--scheduled', 'x y'] True"


def test_a_module_runs_with_minus_m():
    done = subprocess.run(
        [BASE, "-s", str(VENV_RUN), "-m", "pytest", "--version"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=REPO_ROOT,
    )
    assert done.returncode == 0 and "pytest" in (done.stdout + done.stderr)


def test_a_venv_of_another_python_version_is_refused(tmp_path, monkeypatch):
    sys.path.insert(0, str(VENV_RUN.parent))
    try:
        import venv_run
    finally:
        sys.path.remove(str(VENV_RUN.parent))
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = C:\\x\nversion_info = 3.99.1\n", encoding="utf-8")
    monkeypatch.setattr(sys, "path", list(sys.path))
    with pytest.raises(SystemExit) as err:
        venv_run.use_venv(Path(venv))
    assert err.value.code == 2
