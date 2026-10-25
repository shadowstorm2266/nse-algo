"""Process settings loaded from `.env`, and the live-mode safety interlock.

This module is the only place credentials are read. Never log a `SecretStr`'s
secret value.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
LIVE_ARMED_FILENAME = "LIVE_ARMED"
RISK_CONFIG_RELPATH = Path("config") / "risk.yaml"

Mode = Literal["backtest", "paper", "live"]


class Settings(BaseSettings):
    """Environment-driven settings. Every credential is optional and secret."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    mode: Mode = "backtest"

    broker_user_id: SecretStr | None = None
    broker_password: SecretStr | None = None
    broker_api_key: SecretStr | None = None
    broker_api_secret: SecretStr | None = None
    broker_totp_secret: SecretStr | None = None

    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: SecretStr | None = None


class LiveNotAllowedError(RuntimeError):
    """Raised when live trading is requested without every human-set interlock."""


def _risk_live_enabled(risk_path: Path) -> bool:
    if not risk_path.is_file():
        return False
    with risk_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    # Strict identity check: only a YAML boolean `true` counts.
    return isinstance(data, dict) and data.get("live_enabled") is True


def assert_live_allowed(settings: Settings | None = None, repo_root: Path | None = None) -> None:
    """Raise LiveNotAllowedError unless all three live conditions hold.

    1. MODE=live in settings (from `.env`),
    2. a LIVE_ARMED file in the repo root,
    3. `live_enabled: true` in config/risk.yaml.
    """
    settings = settings if settings is not None else Settings()
    root = repo_root if repo_root is not None else REPO_ROOT

    failures: list[str] = []
    if settings.mode != "live":
        failures.append(f"MODE is {settings.mode!r}, not 'live'")
    if not (root / LIVE_ARMED_FILENAME).is_file():
        failures.append(f"{LIVE_ARMED_FILENAME} file missing from repo root")
    if not _risk_live_enabled(root / RISK_CONFIG_RELPATH):
        failures.append("live_enabled is not true in config/risk.yaml")

    if failures:
        raise LiveNotAllowedError("Live trading not allowed: " + "; ".join(failures))
