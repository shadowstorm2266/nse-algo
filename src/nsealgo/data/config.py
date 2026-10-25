"""Settings for the historical data layer, read from config/data.yaml."""

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from nsealgo.settings import REPO_ROOT

DATA_CONFIG_PATH = REPO_ROOT / "config" / "data.yaml"


class SessionNote(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    reason: str


class QualityConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    bad_print_max_dev: float
    bad_print_lookaround: int
    overnight_move_flag: float
    short_session_bars: int
    out_of_line_window_sessions: int
    out_of_line_low: float
    out_of_line_high: float


class DataConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    raw_dir: Path
    clean_dir: Path
    clean_start: date
    clean_end: date
    feature_warmup_sessions: int
    atr_period: int
    avg_window_sessions: int
    universe_size: int
    excluded_sessions: list[SessionNote]
    no_trade_sessions: list[SessionNote]
    quality: QualityConfig

    def excluded(self) -> dict[date, str]:
        return {s.date: s.reason for s in self.excluded_sessions}

    def no_trade(self) -> dict[date, str]:
        return {s.date: s.reason for s in self.no_trade_sessions}


def load_data_config(path: Path = DATA_CONFIG_PATH, root: Path = REPO_ROOT) -> DataConfig:
    """Load config/data.yaml; relative directories resolve against the repo root."""
    with path.open(encoding="utf-8") as fh:
        cfg = DataConfig.model_validate(yaml.safe_load(fh))
    overlap = set(cfg.excluded()) & set(cfg.no_trade())
    if overlap:
        raise ValueError(f"sessions both excluded and no_trade: {sorted(overlap)}")
    return cfg.model_copy(
        update={
            "raw_dir": cfg.raw_dir if cfg.raw_dir.is_absolute() else root / cfg.raw_dir,
            "clean_dir": cfg.clean_dir if cfg.clean_dir.is_absolute() else root / cfg.clean_dir,
        }
    )
