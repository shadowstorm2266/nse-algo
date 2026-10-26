"""Static guards: strategies stay pure, and nothing under src/ calls an LLM (rule 7)."""

import ast
from pathlib import Path

import pytest

from nsealgo.settings import REPO_ROOT

SRC = REPO_ROOT / "src" / "nsealgo"
STRATEGY_FILES = sorted((SRC / "strategies").rglob("*.py"))
IMPURE_MODULES = {
    "os",
    "sys",
    "pathlib",
    "io",
    "socket",
    "subprocess",
    "shutil",
    "time",
    "random",
    "secrets",
    "requests",
    "urllib",
    "http",
    "sqlite3",
    "duckdb",
    "logging",
    "threading",
    "multiprocessing",
    "asyncio",
    "nsealgo.settings",
    "nsealgo.brokers",
    "nsealgo.data",
}
IMPURE_CALLS = {"open", "print", "input", "eval", "exec", "globals", "__import__"}
IMPURE_ATTRS = {"now", "today", "utcnow", "time_ns", "perf_counter"}
LLM_MODULES = {"anthropic", "openai", "google.generativeai", "mistralai", "cohere", "ollama"}


def _imports(tree: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _blocked(name: str, blocked: set[str]) -> bool:
    return any(name == b or name.startswith(b + ".") for b in blocked)


def _violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = [f"import {m}" for m in _imports(tree) if _blocked(m, IMPURE_MODULES)]
    for node in ast.walk(tree):
        if isinstance(node, ast.Global | ast.Nonlocal):
            found.append("global/nonlocal statement")
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in IMPURE_CALLS:
                found.append(f"{f.id}()")
            elif isinstance(f, ast.Attribute) and (
                f.attr in IMPURE_ATTRS or f.attr.startswith(("read_", "to_csv", "to_parquet"))
            ):
                found.append(f".{f.attr}()")
    return found


def test_strategy_package_exists():
    assert STRATEGY_FILES, "no strategy files found"


@pytest.mark.parametrize("path", STRATEGY_FILES, ids=lambda p: p.name)
def test_strategies_are_pure(path):
    assert _violations(path) == []


def test_guard_catches_impurity(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text(
        "import random\nfrom datetime import datetime\nimport pandas as pd\n"
        "x = datetime.now()\ny = pd.read_csv('f')\nopen('f')\n",
        encoding="utf-8",
    )
    assert sorted(_violations(bad)) == [".now()", ".read_csv()", "import random", "open()"]


def test_no_llm_imports_under_src():
    offenders = [
        f"{p.relative_to(SRC)}: {m}"
        for p in SRC.rglob("*.py")
        for m in _imports(ast.parse(p.read_text(encoding="utf-8")))
        if _blocked(m, LLM_MODULES)
    ]
    assert offenders == []
