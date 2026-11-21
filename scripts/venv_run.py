"""Run a script or module with this repo's .venv packages on the venv's base interpreter,
without the venv's own python.exe.

    <base python.exe> -s scripts/venv_run.py SCRIPT [ARGS...]
    <base python.exe> -s scripts/venv_run.py -m MODULE [ARGS...]

Why: since 2026-11-05 15:30 IST Windows Smart App Control (Code Integrity event 3077,
policy VerifiedAndReputableDesktop) blocks .venv\\Scripts\\python.exe, the unsigned
launcher uv writes into the venv, so `uv run` exits 2 before any project code starts.
The base interpreter it would start (the `home` in .venv/pyvenv.cfg) is still allowed.
This script puts the venv's site-packages (with its .pth files, e.g. the editable
nsealgo) ahead of the base interpreter's own and runs the target as __main__. No security
setting is changed. Run the base interpreter with -s so a user site-packages cannot shadow
the venv. The interpreter's major.minor must match the venv's (else exit 2). uv's lock is
not re-checked here; `uv sync --frozen` still manages the venv's contents.
"""

import runpy
import site
import sys
from pathlib import Path

VENV = Path(__file__).resolve().parent.parent / ".venv"


def venv_version(venv: Path) -> str:
    for line in (venv / "pyvenv.cfg").read_text("utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "version_info":
            return ".".join(value.strip().split(".")[:2])
    raise SystemExit(f"no version_info in {venv / 'pyvenv.cfg'}")


def use_venv(venv: Path) -> None:
    """Put the venv's site-packages (and what its .pth files add) first on sys.path."""
    want, have = venv_version(venv), f"{sys.version_info[0]}.{sys.version_info[1]}"
    if want != have:
        print(f"venv_run: .venv is Python {want}, this interpreter is {have}", file=sys.stderr)
        raise SystemExit(2)
    before = list(sys.path)
    site.addsitedir(str(venv / "Lib" / "site-packages"))
    added = [p for p in sys.path if p not in before]
    sys.path[:] = [*before[:1], *added, *before[1:]]


def main(argv: list[str]) -> None:
    if not argv or (argv[0] == "-m" and len(argv) < 2):
        raise SystemExit("usage: venv_run.py SCRIPT [ARGS...] | -m MODULE [ARGS...]")
    use_venv(VENV)
    if argv[0] == "-m":
        sys.argv = [argv[1], *argv[2:]]
        sys.path[0] = str(Path.cwd())
        runpy.run_module(argv[1], run_name="__main__", alter_sys=True)
    else:
        script = Path(argv[0]).resolve()
        sys.argv = [str(script), *argv[1:]]
        sys.path[0] = str(script.parent)
        runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main(sys.argv[1:])
