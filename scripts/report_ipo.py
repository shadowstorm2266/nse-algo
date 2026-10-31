"""Descriptive tables for the mainboard IPO dataset -> research/ipo_dataset_tables.md.

    uv run python scripts/report_ipo.py [BLOCK_RS]   # default 15000

Reads data/clean/ipo/ipos.parquet (scripts/build_ipo.py). Data step only: no strategy, no
costs, no trial. Years are calendar years of the bid close.
"""

import sys
from datetime import UTC, datetime

import pandas as pd

from nsealgo.data.ipo_stats import (
    missing_per_year,
    overlap_per_year,
    p_distribution,
    returns_per_year,
    status_per_year,
    with_year,
)
from nsealgo.settings import REPO_ROOT

CLEAN = REPO_ROOT / "data" / "clean" / "ipo" / "ipos.parquet"
OUT = REPO_ROOT / "research" / "ipo_dataset_tables.md"
FIELDS = [
    "isin",
    "issue_price",
    "lot_size",
    "retail_sub",
    "retail_sub_boa",
    "retail_valid_applications",
    "retail_allottees",
    "retail_lots_allotted",
    "p_1lot",
    "allotment_date",
    "list_open",
    "list_close",
]
SOURCES = ["issue_price_src", "lot_size_src", "retail_sub_src", "p_1lot_method", "listing_match"]


def _md(df: pd.DataFrame, pct: list[str] | None = None, digits: int = 2) -> str:
    d = df.copy()
    for c in pct or []:
        d[c] = d[c].map(lambda v: "" if pd.isna(v) else f"{100 * v:.1f}%")
    d = d.map(lambda v: f"{v:.{digits}f}" if isinstance(v, float) else v)
    d = d.reset_index()
    head = "| " + " | ".join(map(str, d.columns)) + " |"
    rule = "|" + "---|" * len(d.columns)
    body = [
        "| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |"
        for row in d.itertuples(index=False)
    ]
    return "\n".join([head, rule, *body])


def _sources(df: pd.DataFrame) -> pd.DataFrame:
    listed = df[df["status"] == "listed"]
    parts = {c: listed[c].fillna("none").value_counts() for c in SOURCES}
    return pd.DataFrame(parts).fillna(0).astype(int)


def _not_listed(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["status"] != "listed"]
    return d[["issue_id", "company", "issue_open", "issue_close", "status"]].set_index("issue_id")


def _checks(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["checks"] != ""]
    return d[["company", "checks"]].set_index(d["issue_id"])


def main(argv: list[str]) -> None:
    block = float(argv[0]) if argv else 15000.0
    df = pd.read_parquet(CLEAN)
    rets = {c: returns_per_year(df, c) for c in ("ret_open", "ret_close")}
    pct_cols = ["mean", "median", "p25", "p75", "share_below_0", "min", "max"]
    sections = [
        f"# Mainboard IPO dataset: tables\n\nGenerated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC "
        f"by `scripts/report_ipo.py` from `data/clean/ipo/ipos.parquet` ({len(df)} rows). "
        "Years are calendar years of the bid close. Returns are gross (no charges, no retail "
        "discount). Narrative and caveats: `research/ipo_dataset.md`.",
        "## 1. Issues per year, by status\n\n" + _md(status_per_year(df)),
        "## 2. Missing fields per year (listed issues)\n\n" + _md(missing_per_year(df, FIELDS)),
        "## 3. Source of each field (listed issues)\n\n" + _md(_sources(df)),
        "## 4. Allotment chance of a 1-lot retail application\n\n"
        + _md(p_distribution(df), pct=["p10", "median", "p90", "mean"]),
        "## 5a. Listing-day open over issue price\n\n" + _md(rets["ret_open"], pct=pct_cols),
        "## 5b. Listing-day close over issue price\n\n" + _md(rets["ret_close"], pct=pct_cols),
        f"## 6. Overlapping windows and one block of Rs {block:,.0f}\n\n"
        + _md(overlap_per_year(df, block)),
        "## 7. Rows failing a cross-check\n\n" + _md(_checks(df)),
        "## 8. Issues not listed on NSE (or not yet)\n\n" + _md(_not_listed(df)),
    ]
    OUT.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT} ({len(df)} rows; {int((with_year(df)['status'] == 'listed').sum())} listed)"
    )


if __name__ == "__main__":
    main(sys.argv[1:])
