"""Risk and margin settings (config/risk.yaml, config/margins.yaml) and strategy
parameters (config/strategies/<name>.yaml)."""

from collections.abc import Mapping
from datetime import time
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from nsealgo.settings import REPO_ROOT, Mode

RISK_CONFIG_PATH = REPO_ROOT / "config" / "risk.yaml"
MARGIN_CONFIG_PATH = REPO_ROOT / "config" / "margins.yaml"
STRATEGY_CONFIG_DIR = REPO_ROOT / "config" / "strategies"

HaltMode = Literal["record", "latch"]


class HaltModes(BaseModel):
    """`record`: keep trading and remember when the halt would have fired.
    `latch`: no new entries for the rest of the run. Paper and live must latch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    backtest: HaltMode
    paper: Literal["latch"]
    live: Literal["latch"]

    def for_mode(self, mode: Mode) -> HaltMode:
        return getattr(self, mode)


class SwingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool
    max_positions: int = Field(gt=0)
    max_position_pct: Decimal = Field(gt=0, le=100)
    max_gross_exposure_pct: Decimal = Field(gt=0, le=100)
    max_orders_per_day: int = Field(gt=0)


class RiskConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    capital: Decimal = Field(gt=0)
    account_drawdown_halt_pct: Decimal = Field(gt=0, lt=100)
    halt_mode: HaltModes
    live_enabled: bool
    risk_per_trade_rupees: Decimal = Field(gt=0)
    max_trades_per_day: int = Field(gt=0)
    max_daily_loss_rupees: Decimal = Field(gt=0)
    max_gross_exposure_rupees: Decimal = Field(gt=0)
    entry_start: time
    entry_end: time
    flat_by: time
    max_positions_per_symbol: int
    swing: SwingConfig

    @field_validator("max_positions_per_symbol")
    @classmethod
    def _one_per_symbol(cls, v: int) -> int:
        # The engine and RiskGovernor assume one position per symbol (no pyramiding).
        if v != 1:
            raise ValueError("only max_positions_per_symbol: 1 is supported")
        return v

    @model_validator(mode="after")
    def _window_order(self) -> "RiskConfig":
        if not self.entry_start < self.entry_end < self.flat_by:
            raise ValueError("need entry_start < entry_end < flat_by")
        return self


class MarginConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_mis_margin_pct: Decimal = Field(gt=0, le=100)
    symbols: dict[str, Decimal] = Field(default_factory=dict)

    @field_validator("symbols")
    @classmethod
    def _pcts_in_range(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        bad = {s: p for s, p in v.items() if not 0 < p <= 100}
        if bad:
            raise ValueError(f"margin pct must be in (0, 100]: {bad}")
        return v

    def mis_fraction(self, symbol: str) -> Decimal:
        return self.symbols.get(symbol, self.default_mis_margin_pct) / 100


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_risk_config(path: Path = RISK_CONFIG_PATH) -> RiskConfig:
    return RiskConfig.model_validate(_read_yaml(path))


def load_margin_config(path: Path = MARGIN_CONFIG_PATH) -> MarginConfig:
    return MarginConfig.model_validate(_read_yaml(path))


def merge_params(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    """`base` with `overrides` applied key by key; nested mappings merge recursively."""
    out = dict(base)
    for key, value in overrides.items():
        if isinstance(value, Mapping) and isinstance(out.get(key), Mapping):
            out[key] = merge_params(out[key], value)
        else:
            out[key] = value
    return out


def load_strategy_params(
    name: str, overrides: Mapping[str, Any], config_dir: Path = STRATEGY_CONFIG_DIR
) -> dict[str, Any]:
    """config/strategies/<name>.yaml (empty if absent) with `overrides` merged in.
    Strategies validate their own parameters and reject unknown keys."""
    path = config_dir / f"{name}.yaml"
    base = (_read_yaml(path) or {}) if path.is_file() else {}
    return merge_params(base, overrides)
