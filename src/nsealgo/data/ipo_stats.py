"""Descriptive tables for the mainboard IPO dataset (data step only: no strategy, no costs).

Years are calendar years of the bid close. Returns are listing-day open or close over the
issue price, minus 1, gross (no charges, no retail discount). Pure functions on the
clean table (nsealgo.data.ipo_build.CLEAN_COLS).
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd

P_BUCKETS = [
    (1.0, 1.0001, "= 100%"),
    (0.5, 1.0, "50-<100%"),
    (0.25, 0.5, "25-<50%"),
    (0.10, 0.25, "10-<25%"),
    (0.05, 0.10, "5-<10%"),
    (0.02, 0.05, "2-<5%"),
    (0.0, 0.02, "<2%"),
]


def with_year(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(year=pd.to_datetime(df["issue_close"]).dt.year)


def status_per_year(df: pd.DataFrame) -> pd.DataFrame:
    return with_year(df).pivot_table(
        index="year", columns="status", values="issue_id", aggfunc="count", fill_value=0
    )


def missing_per_year(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """Listed issues per year and, per field, how many have no value."""
    d = with_year(df[df["status"] == "listed"])
    out = d.groupby("year")[fields].agg(lambda s: int(s.isna().sum()))
    return out.assign(listed=d.groupby("year").size()).iloc[:, ::-1]


def _p_row(label: object, p: np.ndarray) -> dict:
    row: dict = {"year": label, "n": len(p)}
    for lo, hi, name in P_BUCKETS:
        row[name] = int(((p >= lo) & (p < hi)).sum())
    return row | {
        "p10": np.quantile(p, 0.1),
        "median": np.median(p),
        "p90": np.quantile(p, 0.9),
        "mean": p.mean(),
    }


def p_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Listed issues with a 1-lot allotment chance, per year and pooled ('all'), by
    bucket, with quantiles."""
    d = with_year(df[(df["status"] == "listed") & df["p_1lot"].notna()])
    rows = [_p_row(year, g["p_1lot"].to_numpy(float)) for year, g in d.groupby("year")]
    if len(d):
        rows.append(_p_row("all", d["p_1lot"].to_numpy(float)))
    cols = ["year", "n", *(b[2] for b in P_BUCKETS), "p10", "median", "p90", "mean"]
    return pd.DataFrame(rows, columns=cols).set_index("year")


def returns_per_year(df: pd.DataFrame, col: str) -> pd.DataFrame:
    d = with_year(df[(df["status"] == "listed") & df[col].notna()])
    g = d.groupby("year")[col]
    return pd.DataFrame(
        {
            "n": g.size(),
            "mean": g.mean(),
            "median": g.median(),
            "p25": g.quantile(0.25),
            "p75": g.quantile(0.75),
            "share_below_0": g.apply(lambda s: float((s < 0).mean())),
            "min": g.min(),
            "max": g.max(),
        }
    )


def max_sequential(intervals: list[tuple[date, date]]) -> int:
    """Most intervals one block of money can take one after another: the next must start
    strictly after the previous one's end day (inclusive endpoints, so funds released on
    a day are not reused that day). Greedy by earliest end, which maximises the count."""
    count, last_end = 0, None
    for start, end in sorted(intervals, key=lambda iv: (iv[1], iv[0])):
        if last_end is None or start > last_end:
            count, last_end = count + 1, end
    return count


def max_concurrent(intervals: list[tuple[date, date]]) -> int:
    events: dict[date, int] = {}
    for start, end in intervals:
        events[start] = events.get(start, 0) + 1
        events[end + timedelta(days=1)] = events.get(end + timedelta(days=1), 0) - 1
    level = peak = 0
    for day in sorted(events):
        level += events[day]
        peak = max(peak, level)
    return peak


def _overlapping(intervals: list[tuple[date, date]]) -> int:
    """How many intervals share at least one day with another."""
    hit = 0
    for i, (s, e) in enumerate(intervals):
        hit += any(s <= e2 and s2 <= e for j, (s2, e2) in enumerate(intervals) if j != i)
    return hit


def overlap_per_year(df: pd.DataFrame, block: float) -> pd.DataFrame:
    """Per year, for listed issues: blocking ends on the allotment date (the listing date
    where the advert gives none). 'full' = [bid open, end], the owner's definition;
    'last_day' = [bid close, end], applying on the last bid day."""
    d = with_year(df[df["status"] == "listed"]).copy()
    d["end"] = d["allotment_date"].where(d["allotment_date"].notna(), d["listing_date"])
    d["cost"] = d["lot_size"] * (d["price_band_high"] - d["retail_discount"].fillna(0))
    rows = []
    for year, g in d.groupby("year"):
        fits = g[g["cost"] <= block]
        full = list(zip(fits["issue_open"], fits["end"], strict=True))
        last = list(zip(fits["issue_close"], fits["end"], strict=True))
        rows.append(
            {
                "year": year,
                "listed": len(g),
                "end_is_listing_date": int(g["allotment_date"].isna().sum()),
                "lot_cost_unknown": int(g["cost"].isna().sum()),
                "lot_cost_above_block": int((g["cost"] > block).sum()),
                "fit_block": len(fits),
                "overlap_full": _overlapping(full),
                "max_concurrent_full": max_concurrent(full),
                "one_block_full": max_sequential(full),
                "overlap_last_day": _overlapping(last),
                "max_concurrent_last_day": max_concurrent(last),
                "one_block_last_day": max_sequential(last),
            }
        )
    return pd.DataFrame(rows).set_index("year")
