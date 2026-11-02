"""IPO v2 forward-test evaluation (research/ipo_v2_plan.md sections 6-8).

    uv run python scripts/evaluate_ipo_v2.py              # counts only (always allowed)
    uv run python scripts/evaluate_ipo_v2.py --evaluate   # the single evaluation, once ready

Before the evaluation set is ready, this shows counts and nothing else: decisions, applies,
skips, no decision data, before plan, listed, withdrawn, pending. It computes no P&L and no
listing-day figure. The set is every decision up to the last bid day of the 20th decision.
It is ready when every issue in it has listed (a listing file is saved) or is marked
withdrawn in config/ipo_v2.yaml.

With --evaluate, once ready, on a clean commit, and only if no ipo v2 trial exists: the
Monte Carlo over the set (nsealgo.reporting.ipo_v2_eval). It writes
research/runs/<stamp>_ipo_v2/ and logs one trial to research/trials.jsonl. A second
evaluation is refused. Refresh the Nifty 50 TRI first:
`uv run python scripts/download_indices.py --only nifty50 --out data/raw/ipo/benchmark`.
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from ipo_live_backup import load_live_config
from ipo_v2_decisions import load_v2_config, read_decisions

from nsealgo.costs import load_cost_config, load_ipo_costs
from nsealgo.data.calendar import IST, load_holidays
from nsealgo.data.ipo_boa import parse_retail_boa, text_is_readable
from nsealgo.data.ipo_build import _p_one_lot, _validated
from nsealgo.data.ipo_live import book_summary, parse_snapshot_name
from nsealgo.data.ipo_read import pdf_text
from nsealgo.engine.ipo_sim import TradingDays
from nsealgo.reporting.ipo_v2_eval import ISSUE_COLS, evaluate
from nsealgo.reporting.trials import TRIALS_PATH, append_trial, git_state, read_trials
from nsealgo.settings import REPO_ROOT
from nsealgo.strategies.ipo_v2 import NAME, VERSION, IpoV2Config, counts, evaluation_set

LIVE = REPO_ROOT / "data" / "live" / "ipo"
CONFIG = REPO_ROOT / "config" / "ipo_v2.yaml"
COSTS = REPO_ROOT / "config" / "costs.yaml"
HOLIDAYS = REPO_ROOT / "config" / "holidays.csv"


def listed_ids(root: Path) -> set[str]:
    return {p.parent.name for p in root.glob("*/listing_*.json")}


def already_evaluated(trials: Path) -> bool:
    return any(
        t["strategy"] == NAME and t["strategy_version"] == VERSION for t in read_trials(trials)
    )


def status(root: Path, cfg: IpoV2Config, today: date) -> tuple[list[dict] | None, list[str]]:
    """Print the counts; return (evaluation set or None, pending issue ids in it)."""
    decisions = read_decisions(root)
    listed, withdrawn = listed_ids(root), {w.issue_id for w in cfg.withdrawn}
    for k, v in counts(decisions, listed, withdrawn).items():
        print(f"{k}: {v}")
    found = evaluation_set(decisions, cfg.min_decisions)
    if found is None:
        n = sum(d["status"] in ("apply", "skip") for d in decisions)
        print(f"performance withheld: {n} of {cfg.min_decisions} decisions")
        return None, []
    es, last = found
    pending = [d for d in es if d["issue_id"] not in listed | withdrawn]
    print(f"evaluation set: {len(es)} issues, last bid day {last}")
    for d in pending:
        late = today > date.fromisoformat(d["bid_close"]) + timedelta(days=cfg.listing_wait_days)
        print(f"pending: {d['issue_id']} (bid close {d['bid_close']}){' OVERDUE' if late else ''}")
    if pending:
        print(f"performance withheld: {len(pending)} issue(s) not yet listed")
    return es, [d["issue_id"] for d in pending]


def advert_fields(path: Path | None, lot: int, retail_x: float | None, exe: str) -> dict:
    """1-lot chance and the other advert fields, by the dataset's rules; {} if unreadable."""
    if path is None:
        return {}
    prose = pdf_text(path, False, exe)
    parsed = (
        parse_retail_boa(prose, pdf_text(path, True, exe), lot) if text_is_readable(prose) else None
    )
    if parsed is None:
        return {}
    raw = parsed.as_dict()
    sub = raw.get("retail_sub_boa") or retail_x
    b, _, _ = _validated(raw, sub)
    p = _p_one_lot(b, sub)[0]
    keys = ("allotment_date", "retail_discount")
    out = {k: raw[k] for k in keys} | {"p_1lot": p}
    return out | {k: b.get(k) for k in ("retail_shares_applied", "retail_valid_applications")}


def final_retail_x(d: Path) -> float | None:
    """Retail times in the final book, else in the latest snapshot."""
    snaps = sorted((n[0], n[1], p) for p in d.iterdir() if (n := parse_snapshot_name(p.name)))
    if not snaps:
        return None
    s = book_summary(json.loads(snaps[-1][2].read_bytes()))
    return s["retail"][2] if s["retail"] else None


def issue_row(root: Path, dec: dict, withdrawn: set[str], exe: str) -> dict:
    d, iid = root / dec["issue_id"], dec["issue_id"]
    row = dict.fromkeys(ISSUE_COLS) | {
        "issue_id": iid,
        "decision": dec["status"],
        "total_x": dec["total_x"],
        "issue_close": date.fromisoformat(dec["bid_close"]),
        "lot_size": dec["lot"],
        "price_band_high": dec["band_high"],
    }
    if iid in withdrawn:
        return row | {"status": "withdrawn"}
    lst = json.loads(next(d.glob("listing_*.json")).read_text("utf-8"))
    adverts = sorted(d.glob("ADV_*"))
    rx = final_retail_x(d)
    row |= {
        "status": "listed",
        "issue_price": lst["prev_close"],
        "listing_date": date.fromisoformat(lst["listing_date"]),
        "list_open": lst["open"],
        "list_close": lst["close"],
        "retail_sub_exch": rx,
    }
    return row | advert_fields(adverts[0] if adverts else None, dec["lot"], rx, exe)


def trading_days(holidays: set[date], start: date) -> TradingDays:
    """Weekdays not in config/holidays.csv up to the last year it covers; later days are
    weekdays and reported as past the calendar."""
    horizon = date(max(h.year for h in holidays), 12, 31) if holidays else start
    end, day, out = max(horizon, start + timedelta(days=7)), start, []
    while day <= end:
        if day.weekday() < 5 and day not in holidays:
            out.append(day)
        day += timedelta(days=1)
    return TradingDays(out)


def run_evaluation(es: list[dict], cfg: IpoV2Config, root: Path) -> dict:
    exe = load_live_config().pdftotext
    withdrawn = {w.issue_id for w in cfg.withdrawn}
    df = pd.DataFrame([issue_row(root, d, withdrawn, exe) for d in es], columns=ISSUE_COLS)
    first = min(df["issue_close"])
    days = trading_days(load_holidays(HOLIDAYS), first - timedelta(days=60))
    tri_raw = pd.read_csv(REPO_ROOT / cfg.benchmark.tri_csv, usecols=["date", "tri"])
    tri = pd.Series(
        tri_raw["tri"].astype(float).to_numpy(), index=pd.to_datetime(tri_raw["date"]).dt.date
    )
    costs, ipo_costs = load_cost_config(COSTS), load_ipo_costs(COSTS)
    return evaluate(df, days, cfg, costs, ipo_costs, tri) | {
        "issue_table": df.astype(str).to_dict("records")
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--evaluate", action="store_true", help="the single evaluation, once ready")
    args = ap.parse_args(argv)
    cfg, now = load_v2_config(CONFIG), datetime.now(IST)
    es, pending = status(LIVE, cfg, now.date())
    if es is None or pending:
        return 0
    if not args.evaluate:
        print("ready: run with --evaluate (once; logged as one trial)")
        return 0
    if already_evaluated(TRIALS_PATH):
        raise SystemExit(f"{NAME} v{VERSION} was already evaluated; a second evaluation is refused")
    git = git_state()
    if git["git_dirty"]:
        raise SystemExit("commit first: the evaluation runs on a clean tree")
    result = run_evaluation(es, cfg, LIVE)
    run_dir = REPO_ROOT / "research" / "runs" / f"{now:%Y%m%d-%H%M%S}_ipo_v2"
    run_dir.mkdir(parents=True)
    (run_dir / "results.json").write_text(json.dumps(result, indent=1, default=str), "utf-8")
    period = {
        "label": "ipo_v2_forward",
        "start": result["first_bid_close"],
        "end": result["end_date"],
    }
    metrics = {
        k: result[k] for k in ("tiers", "v1_rules_base", "benchmark", "checks", "issues", "applies")
    }
    append_trial(
        TRIALS_PATH,
        {"run_at": now.isoformat(), **git, "strategy": NAME, "strategy_version": VERSION,
         "params": cfg.model_dump(mode="json"), "period": period, "cost_tier": "all",
         "forward_test": True, "run_dir": str(run_dir.relative_to(REPO_ROOT)), "metrics": metrics},
    )  # fmt: skip
    for c in result["checks"]:
        print(f"check {c['check']}: {c['result']}  {c['what']}  {c['value']}")
    print(f"wrote {run_dir}; one trial logged")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
