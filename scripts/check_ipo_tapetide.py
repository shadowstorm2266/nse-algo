"""Cross-check the clean IPO table against an aggregator (Tapetide), on a random sample.

    uv run python scripts/check_ipo_tapetide.py [N] [SEED]   # default 30 issues, seed 20261031

Tapetide (UNVERIFIED aggregator; robots.txt welcomes AI agents and declares ai-input=yes)
publishes one page per listing year, 2018 onward, with every IPO's listing date, issue
price, listing price ("the price at which the shares opened on their first trading day",
exchange not stated) and overall subscription. The pages are saved by hand as
data/raw/ipo/aggregator_tapetide/ipo_listing_gains_<year>.md (the site's Markdown twins).

N listed issues are drawn at random from data/clean/ipo/ipos.parquet (listing year 2018
on). Each is matched to the Tapetide row with the same listing date and issue price (name
overlap breaks ties). The comparison goes to research/ipo_crosscheck_tapetide.csv. No field
of the clean table is taken from Tapetide.
"""

import re
import sys

import numpy as np
import pandas as pd

from nsealgo.settings import REPO_ROOT

AGG = REPO_ROOT / "data" / "raw" / "ipo" / "aggregator_tapetide"
CLEAN = REPO_ROOT / "data" / "clean" / "ipo" / "ipos.parquet"
OUT = REPO_ROOT / "research" / "ipo_crosscheck_tapetide.csv"
COVERAGE_OUT = REPO_ROOT / "research" / "ipo_coverage_tapetide.csv"
STOP = {"limited", "ltd", "india", "the", "and", "of", "ipo", "&"}


def _num(cell: str) -> float | None:
    cell = cell.strip().replace(",", "")
    return None if cell in ("", "—", "-") else float(cell)


def tapetide_rows() -> pd.DataFrame:
    rows = []
    for path in sorted(AGG.glob("ipo_listing_gains_*.md")):
        for line in path.read_text("utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 10 or cells[1] != "Mainboard" or not re.match(r"\d{4}-", cells[2]):
                continue
            name = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cells[0])
            rows.append(
                {
                    "agg_name": name,
                    "agg_listing_date": pd.Timestamp(cells[2]).date(),
                    "agg_issue_price": _num(cells[3]),
                    "agg_listing_price": _num(cells[4]),
                    "agg_subscription": _num(cells[6]),
                    "agg_file": path.name,
                }
            )
    # a page lists some issues twice (in a monthly table and the full table)
    return pd.DataFrame(rows).drop_duplicates(subset=[c for c in rows[0] if c != "agg_file"])


def _tokens(name: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", name.lower()) if w not in STOP}


def _match(issue: pd.Series, agg: pd.DataFrame) -> pd.Series | None:
    same_day = agg[agg["agg_listing_date"] == issue["listing_date"]]
    cands = same_day[(same_day["agg_issue_price"] - issue["issue_price"]).abs() < 0.005]
    if len(cands) != 1:
        pool = cands if len(cands) > 1 else agg
        score = pool["agg_name"].map(lambda n: len(_tokens(n) & _tokens(issue["company"])))
        if score.empty or score.max() == 0:
            return None
        cands = pool[score == score.max()]
        if len(cands) != 1:
            return None
    return cands.iloc[0]


def coverage(clean: pd.DataFrame, agg: pd.DataFrame) -> pd.DataFrame:
    """Every Tapetide mainboard row with no issue in the clean table listed within 3 days
    of its listing date at the same issue price (any status counts, by close date)."""
    rows = []
    for _, a in agg.iterrows():
        day = pd.Timestamp(a["agg_listing_date"])
        listed = pd.to_datetime(clean["listing_date"])
        closed = pd.to_datetime(clean["issue_close"])
        near = ((listed - day).abs() <= pd.Timedelta(days=3)) | (
            listed.isna() & ((day - closed).dt.days.between(0, 20))
        )
        price = (clean["issue_price"] - a["agg_issue_price"]).abs() < 0.005
        if not (near & price).any():
            rows.append(a.to_dict())
    return pd.DataFrame(rows)


def main(argv: list[str]) -> None:
    n = int(argv[0]) if argv else 30
    seed = int(argv[1]) if len(argv) > 1 else 20261031
    clean = pd.read_parquet(CLEAN)
    pool = clean[
        (clean["status"] == "listed") & (pd.to_datetime(clean["listing_date"]).dt.year >= 2018)
    ]
    sample = pool.sample(n=n, random_state=np.random.RandomState(seed))
    agg = tapetide_rows()
    out = []
    for _, r in sample.sort_values("listing_date").iterrows():
        m = _match(r, agg)
        row = {
            "issue_id": r["issue_id"],
            "company": r["company"],
            "listing_date": r["listing_date"],
            "issue_price": r["issue_price"],
            "list_open_nse": r["list_open"],
            "total_sub_exch": r["total_sub_exch"],
        }
        row |= m.to_dict() if m is not None else {"agg_name": None}
        if m is not None:
            row["date_match"] = m["agg_listing_date"] == r["listing_date"]
            row["price_match"] = abs(m["agg_issue_price"] - r["issue_price"]) < 0.005
            row["open_gap_pct"] = 100 * (m["agg_listing_price"] / r["list_open"] - 1)
        out.append(row)
    df = pd.DataFrame(out)
    df.to_csv(OUT, index=False)
    matched = df["agg_name"].notna()
    print(f"sample {n} (seed {seed}); matched {int(matched.sum())}")
    print("listing date mismatches:", int((~df.loc[matched, "date_match"].astype(bool)).sum()))
    print("issue price mismatches:", int((~df.loc[matched, "price_match"].astype(bool)).sum()))
    gap = df.loc[matched, "open_gap_pct"].abs()
    print(
        f"listing open: {int((gap < 0.01).sum())} equal, {int((gap >= 0.01).sum())} differ "
        f"(max |gap| {gap.max():.2f}%)"
    )
    print(
        df.loc[
            ~matched | (df.get("open_gap_pct", 0).abs() >= 0.01),
            ["issue_id", "issue_price", "list_open_nse", "agg_name", "agg_listing_price"],
        ].to_string()
    )
    missing = coverage(clean, agg)
    missing.to_csv(COVERAGE_OUT, index=False)
    print(f"coverage: {len(agg)} Tapetide mainboard rows, {len(missing)} with no issue here")
    if len(missing):
        print(missing[["agg_name", "agg_listing_date", "agg_issue_price"]].to_string())


if __name__ == "__main__":
    main(sys.argv[1:])
