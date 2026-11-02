"""IPO v2 (forward test): apply for 1 lot only when the consolidated book is at least 5x
subscribed at the 15:30 snapshot on the last bid day; sell at the listing-day close.
Pre-registered in research/ipo_v2_plan.md; parameters in config/ipo_v2.yaml.

IPO applications are manual UPI and never automated (hard rule 1). This module only reads
recorded snapshots and writes nothing: the decision rule (plan section 4), the evaluation
set and the counts (section 6). No I/O and no parsing: the callers pass file names, fetch
times and the book's fields (nsealgo.data.ipo_live.decision_inputs).
"""

import math
from collections.abc import Iterable, Mapping
from datetime import date, datetime, time
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from nsealgo.strategies.ipo_v1 import MonteCarlo, Release

IST = ZoneInfo("Asia/Kolkata")
NAME = "ipo"
VERSION = "2"
DECIDED = ("apply", "skip")


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Benchmark(_Frozen):
    tri_csv: str
    expense_ratio_pct: float = Field(ge=0)


class Withdrawn(_Frozen):
    issue_id: str
    source: str


class IpoV2Config(_Frozen):
    plan_commit: str
    plan_committed_at: datetime
    threshold_total_x: float = Field(gt=0)
    decision_slot: time
    cutoff: time
    min_decisions: int = Field(gt=0)
    listing_wait_days: int = Field(gt=0)
    capital_rupees: int = Field(gt=0)
    lots_per_application: Literal[1]
    release: Release
    monte_carlo: MonteCarlo
    benchmark: Benchmark
    withdrawn: list[Withdrawn] = []


def decision_slot_at(day: date, cfg: IpoV2Config) -> datetime:
    return datetime.combine(day, cfg.decision_slot, tzinfo=IST)


def cutoff_at(day: date, cfg: IpoV2Config) -> datetime:
    return datetime.combine(day, cfg.cutoff, tzinfo=IST)


def choose_snapshot(
    snaps: Iterable[tuple[datetime, str]], scheduled: str | None, day: date, cfg: IpoV2Config
) -> tuple[str, str, datetime] | None:
    """(file, source, fetch time) of the decision snapshot for last bid day `day`, from the
    issue's bid-day snapshots (fetch time, file name). `scheduled` is the file saved by the
    scheduled run for the decision slot, if any. Source 'scheduled_1530' if that file was
    fetched on `day` before the cutoff; else 'latest_before_cutoff', the latest file
    fetched on `day` before the cutoff; None if there is none (no decision data)."""
    cutoff = cutoff_at(day, cfg)
    on_day = sorted((t, n) for t, n in snaps if t.astimezone(IST).date() == day and t < cutoff)
    for t, n in on_day:
        if n == scheduled:
            return n, "scheduled_1530", t
    if on_day:
        t, n = on_day[-1]
        return n, "latest_before_cutoff", t
    return None


def decide(total_x: float | None, threshold: float) -> tuple[str, float | None]:
    """('apply' | 'skip', total times) from the consolidated book's Total row, or
    ('no_decision_data', None) if that row is missing or unreadable (None)."""
    if total_x is None or not math.isfinite(total_x):
        return "no_decision_data", None
    return ("apply" if total_x >= threshold else "skip"), total_x


def decision_record(
    issue_id: str,
    day: date,
    chosen: tuple[str, str, datetime] | None,
    book: Mapping | None,
    cfg: IpoV2Config,
    now: datetime,
) -> dict:
    """The decisions.jsonl line for one issue (plan section 4). `book` holds the decision
    snapshot's fields (total_x, retail_x, lot, band_high, stamp)."""
    base = {
        "rule": f"{NAME} v{VERSION}",
        "plan_commit": cfg.plan_commit,
        "issue_id": issue_id,
        "bid_close": day.isoformat(),
        "decided_at": now.isoformat(),
        "threshold": cfg.threshold_total_x,
    }
    if chosen is None or book is None:
        before = cutoff_at(day, cfg) <= cfg.plan_committed_at
        return base | {"status": "before_plan" if before else "no_decision_data"}
    name, source, fetched = chosen
    status, total = decide(book.get("total_x"), cfg.threshold_total_x)
    if fetched <= cfg.plan_committed_at:
        status = "before_plan"
    lot, high = book.get("lot"), book.get("band_high")
    return base | {
        "status": status,
        "snapshot": name,
        "snapshot_source": source,
        "snapshot_fetched_at": fetched.isoformat(),
        "stamp": book.get("stamp"),
        "total_x": total,
        "retail_x": book.get("retail_x"),
        "lot": lot,
        "band_high": high,
        "application_rs": lot * high if lot and high else None,
    }


def evaluation_set(decisions: Iterable[Mapping], n: int) -> tuple[list[dict], date] | None:
    """Decisions (apply or skip) with a last bid day up to that of the n-th decision, in
    order (bid close, issue_id), and that day; None if there are fewer than n."""
    dec = sorted(
        (dict(d) for d in decisions if d["status"] in DECIDED),
        key=lambda d: (d["bid_close"], d["issue_id"]),
    )
    if len(dec) < n:
        return None
    last = dec[n - 1]["bid_close"]
    return [d for d in dec if d["bid_close"] <= last], date.fromisoformat(last)


def counts(decisions: Iterable[Mapping], listed: set[str], withdrawn: set[str]) -> dict:
    """What may be shown before the evaluation: counts only (plan section 6)."""
    rows = list(decisions)
    decided = [d for d in rows if d["status"] in DECIDED]
    ids = {d["issue_id"] for d in decided}
    return {
        "decisions": len(decided),
        "applies": sum(d["status"] == "apply" for d in rows),
        "skips": sum(d["status"] == "skip" for d in rows),
        "no_decision_data": sum(d["status"] == "no_decision_data" for d in rows),
        "before_plan": sum(d["status"] == "before_plan" for d in rows),
        "listed": len(ids & listed),
        "withdrawn": len(ids & withdrawn),
        "pending": len(ids - listed - withdrawn),
    }
