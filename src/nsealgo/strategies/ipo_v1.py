"""IPO v1: one lot of every affordable mainboard IPO, bid at the top of the band on the
last bid day and sold at the NSE listing-day open (research/ipo_strategy_plan.md).

IPO applications are manual UPI and never automated (hard rule 1): this module only
prepares a simulation for `nsealgo.engine.ipo_sim`. Pure functions on the clean IPO table
(data/clean/ipo/ipos.parquet, columns in docs/data.md). Parameters come from
config/strategies/ipo_v1.yaml, parsed by the caller into `IpoV1Config` (this package does
no I/O). Amounts leave here as integer paise.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from nsealgo.costs import CostConfig, IpoCosts, fill_charges
from nsealgo.engine.ipo_sim import SimInput, Tax, TradingDays

NAME = "ipo"
VERSION = "1"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Release(_Frozen):
    not_allotted_days_after_allotment: int = Field(ge=0)
    allotted_days_after_listing: int = Field(ge=0)
    allotment_estimate_days_before_listing: int = Field(ge=1)


class MonteCarlo(_Frozen):
    runs: int = Field(gt=0)
    seed: int


class TaxSensitivity(_Frozen):
    stcg_pct: float = Field(ge=0, le=100)
    due_month: int = Field(ge=1, le=12)
    due_day: int = Field(ge=1, le=31)


class Benchmark(_Frozen):
    tri_csv: str
    expense_ratio_pct: float = Field(ge=0)
    base_date: date


class IpoV1Config(_Frozen):
    capital_rupees: int = Field(gt=0)
    bid_close_from: date
    bid_close_to: date
    lots_per_application: int = Field(ge=1, le=1)  # the rule is exactly one lot
    choice_statuses: list[str]
    release: Release
    monte_carlo: MonteCarlo
    tax_sensitivity: TaxSensitivity
    benchmark: Benchmark
    notes: dict[str, str]


def _gap(r: pd.Series) -> str | None:
    """Why a choice-status issue cannot be simulated, or None."""
    if pd.isna(r["lot_size"]):
        return "data gap: no lot"
    if pd.isna(r["price_band_high"]):
        return "data gap: no price band"
    if r["status"] != "listed":
        return None
    if pd.isna(r["issue_price"]) or pd.isna(r["list_open"]):
        return "data gap: no issue or listing price"
    if pd.isna(r["p_1lot"]) and pd.isna(r["retail_sub_exch"]):
        return "data gap: no 1-lot chance and no exchange multiple"
    return None


def _reason(r: pd.Series, cfg: IpoV1Config) -> str | None:
    if r["status"] in cfg.choice_statuses:
        return _gap(r)
    note = cfg.notes.get(r["issue_id"])
    return f"status {r['status']}" + (f": {note}" if note else "")


def select_universe(df: pd.DataFrame, cfg: IpoV1Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(choices, excluded) among issues with bid close in [bid_close_from, bid_close_to].
    Choices are sorted by (bid close, issue id); `excluded` has a `reason` column."""
    close = pd.to_datetime(df["issue_close"]).dt.date
    window = df[(close >= cfg.bid_close_from) & (close <= cfg.bid_close_to)].copy()
    window["reason"] = [_reason(r, cfg) for _, r in window.iterrows()]
    keep = window["reason"].isna()
    choices = window[keep].drop(columns="reason")
    choices = choices.sort_values(["issue_close", "issue_id"], ignore_index=True)
    return choices, window[~keep].reset_index(drop=True)


def k_by_year(df: pd.DataFrame) -> dict[int, float]:
    """Median average lots per valid retail application (advert TOTAL row), by bid-close
    year, over listed issues with a parsed 1-lot chance."""
    ok = (
        (df["status"] == "listed")
        & df["p_1lot"].notna()
        & df["retail_shares_applied"].notna()
        & (pd.to_numeric(df["retail_valid_applications"]) > 0)
        & (df["lot_size"] > 0)
    )
    rows = df[ok]
    lots = rows["retail_shares_applied"].astype(float) / rows["lot_size"]
    avg = lots / rows["retail_valid_applications"].astype(float)
    year = pd.to_datetime(rows["issue_close"]).dt.year
    return {int(y): float(v) for y, v in avg.groupby(year).median().items()}


def _chance(r: pd.Series, k: dict[int, float]) -> tuple[float, bool]:
    if r["status"] == "withdrawn":
        return 0.0, False
    if pd.notna(r["p_1lot"]):
        return float(r["p_1lot"]), False
    x, year = float(r["retail_sub_exch"]), r["issue_close"].year
    if not x > 0 or year not in k:
        raise ValueError(f"{r['issue_id']}: cannot estimate p (x={x}, year={year})")
    return min(1.0, k[year] / x), True


def one_lot_chance(choices: pd.DataFrame, k: dict[int, float]) -> tuple[pd.Series, pd.Series]:
    """(p, estimated) per choice: the parsed 1-lot chance, else min(1, k_year / x) with x
    the exchange retail multiple (flagged estimated); 0 for a withdrawn issue."""
    pairs = [_chance(r, k) for _, r in choices.iterrows()]
    p = pd.Series([a for a, _ in pairs], index=choices.index, dtype=float)
    return p, pd.Series([b for _, b in pairs], index=choices.index, dtype=bool)


def _fy(d: date) -> int:
    """Indian financial year (April-March) by its start year."""
    return d.year if d.month >= 4 else d.year - 1


def _release(r: pd.Series, days: TradingDays, cfg: IpoV1Config) -> dict:
    close = r["issue_close"]
    if r["status"] == "withdrawn":  # blocked through the bid window only
        return {
            "allotment_date_used": None,
            "allotment_date_estimated": False,
            "release_not": close,
            "free_not": days.after(close),
            "release_allot": close,
            "free_allot": days.after(close),
            "sale_date": close,
        }
    listing, rel = r["listing_date"], cfg.release
    est = r["allotment_date"] is None or pd.isna(r["allotment_date"])
    if est:
        allot = days.before(listing, rel.allotment_estimate_days_before_listing)
    else:
        allot = r["allotment_date"]
    not_day = days.after(allot, rel.not_allotted_days_after_allotment)
    allot_day = days.after(listing, rel.allotted_days_after_listing)
    return {
        "allotment_date_used": allot,
        "allotment_date_estimated": est,
        "release_not": not_day,
        "free_not": days.after(not_day),
        "release_allot": allot_day,
        "free_allot": days.after(allot_day),
        "sale_date": listing,
    }


def _block_paise(r: pd.Series) -> int:
    disc = 0.0 if pd.isna(r["retail_discount"]) else float(r["retail_discount"])
    price = Decimal(str(r["price_band_high"])) - Decimal(str(disc))
    return int(Decimal(int(r["lot_size"])) * price * 100)


def issue_terms(choices: pd.DataFrame, days: TradingDays, cfg: IpoV1Config) -> pd.DataFrame:
    """Application day, blocked amount and release days per choice (plan section 5.2).
    Release days are the last blocked day; `free_*` is the next trading day."""
    out = []
    for _, r in choices.iterrows():
        if days.on_or_after(r["issue_close"]) != r["issue_close"]:
            raise ValueError(f"{r['issue_id']}: bid close {r['issue_close']} is not a session")
        t = _release(r, days, cfg)
        out.append(
            {
                "issue_id": r["issue_id"],
                "status": r["status"],
                "app_date": r["issue_close"],
                "block_paise": _block_paise(r),
                **t,
                "pnl_year": t["sale_date"].year,
                "count_year": r["issue_close"].year,
                "fy": _fy(t["sale_date"]),
            }
        )
    return pd.DataFrame(out, index=choices.index)


def allotted_pnl(
    r: pd.Series,
    sale_col: str,
    slippage_pct: Decimal,
    allotment_date: date,
    costs: CostConfig,
    ipo_costs: IpoCosts,
) -> int:
    """Net P&L in paise of one allotted lot: sold at `sale_col` less slippage, as a CNC
    sell through costs.py, less the price paid (issue price - retail discount) and the
    allotment charges (stamp duty by date)."""
    qty = Decimal(int(r["lot_size"]))
    disc = Decimal(0) if pd.isna(r["retail_discount"]) else Decimal(str(r["retail_discount"]))
    buy = qty * (Decimal(str(r["issue_price"])) - disc)
    sale = qty * Decimal(str(r[sale_col])) * (1 - Decimal(slippage_pct) / 100)
    br = costs.broker
    sell = fill_charges("CNC", "SELL", sale, costs.rates, br.delivery, br.dp_charge_per_scrip)
    net = sale - sell.total - buy - ipo_costs.allotment_charges(buy, allotment_date)
    return int((net * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def pnl_paise(
    choices: pd.DataFrame,
    terms: pd.DataFrame,
    sale_col: str,
    slippage_pct: Decimal,
    costs: CostConfig,
    ipo_costs: IpoCosts,
) -> np.ndarray:
    """P&L if allotted, per choice (0 for a withdrawn issue)."""
    out = []
    for i, r in choices.iterrows():
        t = terms.loc[i]
        if r["status"] == "withdrawn":
            out.append(0)
        else:
            date_ = t["allotment_date_used"]
            out.append(allotted_pnl(r, sale_col, slippage_pct, date_, costs, ipo_costs))
    return np.array(out, dtype=np.int64)


def sim_input(terms: pd.DataFrame, p: pd.Series, pnl: np.ndarray) -> SimInput:
    def ordinals(col: str) -> np.ndarray:
        return np.array([d.toordinal() for d in terms[col]], dtype=np.int64)

    return SimInput(
        app=ordinals("app_date"),
        block=terms["block_paise"].to_numpy(np.int64),
        p=p.to_numpy(np.float64),
        free_allot=ordinals("free_allot"),
        free_not=ordinals("free_not"),
        pnl=np.asarray(pnl, dtype=np.int64),
        pnl_year=terms["pnl_year"].to_numpy(np.int64),
        count_year=terms["count_year"].to_numpy(np.int64),
        fy=terms["fy"].to_numpy(np.int64),
    )


def tax_schedule(terms: pd.DataFrame, days: TradingDays, cfg: IpoV1Config) -> Tax:
    """Tax sensitivity: each financial year's tax on the first session on or after its due
    date; a year due after the period is paid at the end and counts in the last year."""
    ts, end = cfg.tax_sensitivity, cfg.bid_close_to
    day, year = {}, {}
    for fy in sorted(set(terms["fy"])):
        due = date(int(fy) + 1, ts.due_month, ts.due_day)
        if due > end:
            day[int(fy)], year[int(fy)] = date.max.toordinal(), end.year
        else:
            paid = days.on_or_after(due)
            day[int(fy)], year[int(fy)] = paid.toordinal(), paid.year
    return Tax(pct=ts.stcg_pct, day=day, year=year)
