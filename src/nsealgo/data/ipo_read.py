"""Mainboard IPO dataset: read data/raw/ipo/ for scripts/build_ipo.py and
scripts/download_ipo_boa.py.

NSE's lists and per-issue JSON (parsed by ipo.py), the bhavcopies (ipo_listing.py), the
basis-of-allotment adverts' text via xpdf pdftotext (parsed by ipo_boa.py), and the
hand-made exceptions in config/ipo_dataset.yaml. Slow inputs can be cached under a
directory the caller names, keyed by the input files.
"""

import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from nsealgo.data.ipo import issues_frame, overwritten_ipo_rows
from nsealgo.data.ipo_boa import RetailBoa, parse_retail_boa, text_is_readable
from nsealgo.data.ipo_listing import first_seen, listings_frame, read_bhavcopy
from nsealgo.settings import REPO_ROOT

BOA_DIR = "nse_boa"
ZIP_MAGIC = b"PK\x03\x04"
EXCEPTIONS_PATH = REPO_ROOT / "config" / "ipo_dataset.yaml"


def list_rows(raw: Path) -> list[dict]:
    """NSE's Equity-list rows plus the IPO rows only its unfiltered list still has
    (nsealgo.data.ipo.overwritten_ipo_rows)."""

    def read(prefix: str) -> list[dict]:
        rows: list[dict] = []
        for path in sorted((raw / "nse_past_issues").glob(f"{prefix}_*.json")):
            rows.extend(json.loads(path.read_bytes()))
        return rows

    eq = read("eq")
    return eq + overwritten_ipo_rows(read("all"), eq)


def read_issues(raw: Path) -> pd.DataFrame:
    details = {p.stem: json.loads(p.read_bytes()) for p in (raw / "nse_ipo_detail").glob("*.json")}
    return issues_frame(list_rows(raw), details)


def bhavcopy_day(p: Path) -> date:
    """Session date from a bhavcopy file name (either format)."""
    if m := re.fullmatch(r"cm(\d{2})([A-Z]{3})(\d{4})bhav\.csv\.zip", p.name):
        return pd.to_datetime(f"{m[1]}{m[2]}{m[3]}", format="%d%b%Y").date()
    m = re.fullmatch(r"BhavCopy_NSE_CM_0_0_0_(\d{8})_F_0000\.csv\.zip", p.name)
    if m is None:
        raise ValueError(f"unexpected file in bhavcopy dir: {p.name}")
    return pd.to_datetime(m[1], format="%Y%m%d").date()


def bhavcopy_paths(raw: Path) -> list[Path]:
    """Every downloaded bhavcopy, in session order."""
    paths = [p for p in (raw / "bhavcopy").iterdir() if p.suffix == ".zip"]
    return sorted(paths, key=bhavcopy_day)


def _first_seen_cached(paths: list[Path], cache: Path | None) -> tuple[pd.DataFrame, dict]:
    """first_seen over the bhavcopies, cached under `cache` by their names and sizes."""
    if cache is None:
        return first_seen(read_bhavcopy(p, bhavcopy_day(p)) for p in paths)
    key = hashlib.sha256("".join(f"{p.name}:{p.stat().st_size}\n" for p in paths).encode())
    stem = cache / f"first_seen_{key.hexdigest()[:16]}"
    if not stem.with_suffix(".parquet").exists():
        new, sym_first = first_seen(read_bhavcopy(p, bhavcopy_day(p)) for p in paths)
        cache.mkdir(parents=True, exist_ok=True)
        new.to_parquet(stem.with_suffix(".parquet"), index=False)
        firsts = {s: d.isoformat() for s, d in sym_first.items()}
        stem.with_suffix(".json").write_text(json.dumps(firsts), encoding="utf-8")
    new = pd.read_parquet(stem.with_suffix(".parquet"))
    new["session_date"] = pd.to_datetime(new["session_date"]).dt.date
    firsts = json.loads(stem.with_suffix(".json").read_text("utf-8"))
    return new, {s: date.fromisoformat(d) for s, d in firsts.items()}


def read_listings(
    raw: Path, issues: pd.DataFrame, cache: Path | None = None
) -> tuple[pd.DataFrame, date, date]:
    """listings_frame over every bhavcopy, plus the first and last session read."""
    paths = bhavcopy_paths(raw)
    new, sym_first = _first_seen_cached(paths, cache)
    return listings_frame(issues, new, sym_first), bhavcopy_day(paths[0]), bhavcopy_day(paths[-1])


def _pdftotext(pdf: Path, table: bool, exe: str = "pdftotext") -> str:
    """pdftotext's text, or '' if it cannot read the file (one NSE advert is served cut
    short: its GET body is 2.3 MB of a 4.4 MB PDF). '' then counts as unreadable. `exe` is
    the program, a full path where PATH cannot be relied on (scheduled tasks)."""
    args = [exe, "-q", "-enc", "UTF-8", *(["-table"] if table else []), str(pdf), "-"]
    done = subprocess.run(args, capture_output=True, check=False)
    return done.stdout.decode("utf-8", errors="replace") if done.returncode == 0 else ""


def pdf_text(path: Path, table: bool, exe: str = "pdftotext") -> str:
    """xpdf pdftotext 4.x output (reading order, or `-table` layout) of an advert file:
    a PDF, or a zip of PDF newspaper pages (members read in name order, joined)."""
    if path.read_bytes()[:4] != ZIP_MAGIC:
        return _pdftotext(path, table, exe)
    parts = []
    with zipfile.ZipFile(path) as zf, tempfile.TemporaryDirectory() as tmp:
        for i, name in enumerate(sorted(n for n in zf.namelist() if n.lower().endswith(".pdf"))):
            member = Path(tmp) / f"page{i}.pdf"
            member.write_bytes(zf.read(name))
            parts.append(_pdftotext(member, table, exe))
    return "\n".join(parts)


def _cached_text(path: Path, table: bool, cache: Path | None) -> str:
    """pdf_text, cached under `cache` by a hash of the file's bytes."""
    if cache is None:
        return pdf_text(path, table)
    key = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    hit = cache / f"{path.stem}.{key}.{'table' if table else 'prose'}.txt"
    if not hit.exists():
        cache.mkdir(parents=True, exist_ok=True)
        hit.write_text(pdf_text(path, table), encoding="utf-8")
    return hit.read_text("utf-8")


# issue_id -> (advert file, ISIN it was found under, readable text?, parsed retail fields)
BoaMap = dict[str, tuple[str, str, bool, RetailBoa | None]]


def read_boa(raw: Path, cache: Path | None = None, lots: dict | None = None) -> BoaMap:
    """Every advert in the download log, parsed (None if unreadable or no retail section).
    `lots` maps issue_id -> NSE's bid lot, the parser's hint for the 1-lot row."""
    lots = lots or {}
    log_path = raw / BOA_DIR / "probe_log.json"
    log = json.loads(log_path.read_text("utf-8")) if log_path.exists() else {}
    out = {}
    for issue_id, entry in log.items():
        if entry.get("found"):
            pdf = raw / BOA_DIR / entry["found"]
            prose = _cached_text(pdf, False, cache)
            readable = text_is_readable(prose)
            table = _cached_text(pdf, True, cache) if readable else ""
            parsed = parse_retail_boa(prose, table, lots.get(issue_id)) if readable else None
            out[issue_id] = (entry["found"], entry["isin"], readable, parsed)
    return out


def load_exceptions(path: Path = EXCEPTIONS_PATH) -> dict[str, str]:
    """issue_id -> status from config/ipo_dataset.yaml (each entry carries its reason)."""
    cfg = yaml.safe_load(path.read_text("utf-8")) or {}
    out = {}
    for status, entries in cfg.items():
        for e in entries or []:
            if not (e.get("issue_id") and e.get("reason") and e.get("source")):
                raise ValueError(f"{path.name}: {status} entry needs issue_id, reason, source")
            out[e["issue_id"]] = status
    return out
