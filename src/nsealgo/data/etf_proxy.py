"""Tradable proxies for NSE equity ETFs, from index history (config/etf_proxy.yaml).

Per series, on exactly the calendar's sessions (research/strategy4_plan.md section 3):
- close = the total-return index rebased to 100 on the first session, times
  (1 - expense ratio / 365) ^ (calendar days since the first session): the expense
  ratio accrued daily over calendar days, as a fund's NAV accrues it;
- open, high, low = that close x the price index's open, high, low over its close the
  same day.
A session without a complete, positive price and TRI row fails the build; nothing is
filled. Pure functions on frames; scripts/build_etf_proxy.py does the I/O.
"""

from collections.abc import Sequence
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nsealgo.settings import REPO_ROOT

ETF_PROXY_CONFIG_PATH = REPO_ROOT / "config" / "etf_proxy.yaml"
PROXY_COLS = ["symbol", "session_date", "open", "high", "low", "close"]
INDEX_COLS = ["open", "high", "low", "close", "tri"]
REBASE_TO = 100.0
DAYS_PER_YEAR = 365


class ProxySeries(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    index: str = Field(min_length=1)  # key of <index>_price.csv / <index>_tri.csv
    expense_ratio_pct: float = Field(ge=0, lt=100)  # percent a year


class EtfProxyConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    raw_dir: Path
    series: dict[str, ProxySeries]
    universe: list[str]  # what an ETF strategy trades
    benchmark: str  # reporting only, never traded

    @model_validator(mode="after")
    def _consistent(self) -> "EtfProxyConfig":
        unknown = sorted(set(self.universe) - set(self.series))
        if unknown or self.benchmark not in self.series:
            raise ValueError(f"universe/benchmark not in series: {unknown or self.benchmark}")
        if len(set(self.universe)) != len(self.universe) or self.benchmark in self.universe:
            raise ValueError("universe has duplicates or contains the benchmark")
        return self


def load_etf_proxy_config(
    path: Path = ETF_PROXY_CONFIG_PATH, root: Path = REPO_ROOT
) -> EtfProxyConfig:
    """Load config/etf_proxy.yaml; a relative raw_dir resolves against the repo root."""
    with path.open(encoding="utf-8") as fh:
        cfg = EtfProxyConfig.model_validate(yaml.safe_load(fh))
    raw = cfg.raw_dir if cfg.raw_dir.is_absolute() else root / cfg.raw_dir
    return cfg.model_copy(update={"raw_dir": raw})


def read_index(raw_dir: Path, index: str) -> pd.DataFrame:
    """One index's daily rows: date, open, high, low, close (price index) and tri.
    Dates in only one of the two files keep NaN for the other's columns."""
    price = pd.read_csv(raw_dir / f"{index}_price.csv", na_values=["-"])
    tri = pd.read_csv(raw_dir / f"{index}_tri.csv", na_values=["-"], usecols=["date", "tri"])
    df = price.merge(tri, on="date", how="outer")
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d").dt.date
    if df["date"].duplicated().any():
        raise ValueError(f"{index}: duplicate dates")
    return df


def accrual_factor(days: np.ndarray, expense_ratio_pct: float) -> np.ndarray:
    """(1 - e / 365) ^ days: what is left after `days` calendar days of daily accrual."""
    return (1 - expense_ratio_pct / 100 / DAYS_PER_YEAR) ** np.asarray(days, dtype="float64")


def proxy_bars(
    index: pd.DataFrame, sessions: Sequence[date], expense_ratio_pct: float, symbol: str
) -> pd.DataFrame:
    """Proxy bars (PROXY_COLS) for `symbol` on exactly `sessions` (ascending, unique)
    from `index` (read_index's columns)."""
    days = list(sessions)
    if not days or days != sorted(set(days)):
        raise ValueError("sessions must be non-empty, ascending and unique")
    v = index.set_index("date").reindex(days)[INDEX_COLS]
    bad = v.isna().any(axis=1) | (v <= 0).any(axis=1)
    if bad.any():
        raise ValueError(f"{symbol}: no complete positive row on {list(v.index[bad][:5])}")
    o, h, lo, c = (v[k].to_numpy("float64") for k in ("open", "high", "low", "close"))
    if (h < np.maximum(o, c)).any() or (lo > np.minimum(o, c)).any():
        raise ValueError(f"{symbol}: price index high/low outside open/close")
    elapsed = (pd.to_datetime(days) - pd.Timestamp(days[0])).days.to_numpy()
    tri = v["tri"].to_numpy("float64")
    close = REBASE_TO * tri / tri[0] * accrual_factor(elapsed, expense_ratio_pct)
    return pd.DataFrame(
        {
            "symbol": symbol,
            "session_date": days,
            "open": close * o / c,
            "high": close * h / c,
            "low": close * lo / c,
            "close": close,
        }
    )[PROXY_COLS]


def build_proxies(cfg: EtfProxyConfig, sessions: Sequence[date]) -> pd.DataFrame:
    """Every configured series on `sessions`, sorted by symbol and date."""
    parts = [
        proxy_bars(read_index(cfg.raw_dir, s.index), sessions, s.expense_ratio_pct, symbol)
        for symbol, s in sorted(cfg.series.items())
    ]
    return pd.concat(parts, ignore_index=True)
