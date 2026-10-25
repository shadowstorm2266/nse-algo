import itertools
from pathlib import Path

import pytest
import yaml

from nsealgo.settings import (
    REPO_ROOT,
    LiveNotAllowedError,
    Settings,
    assert_live_allowed,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    # Keep the real environment from leaking into tests.
    monkeypatch.delenv("MODE", raising=False)


def _settings(mode: str) -> Settings:
    return Settings(_env_file=None, mode=mode)


def _make_root(tmp_path: Path, *, armed: bool, live_enabled: object) -> Path:
    # tmp_path is a pytest scratch dir, never the repo root.
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "risk.yaml").write_text(
        yaml.safe_dump({"capital": 20000, "live_enabled": live_enabled}), encoding="utf-8"
    )
    if armed:
        (tmp_path / "LIVE_ARMED").write_text("", encoding="utf-8")
    return tmp_path


def test_default_mode_is_backtest():
    assert Settings(_env_file=None).mode == "backtest"


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        _settings("yolo")


def test_secrets_are_masked():
    s = Settings(_env_file=None, telegram_bot_token="abc123")
    assert "abc123" not in repr(s)
    assert "abc123" not in str(s.telegram_bot_token)


@pytest.mark.parametrize(
    ("mode_live", "armed", "enabled"),
    list(itertools.product([False, True], repeat=3)),
)
def test_assert_live_allowed_every_combination(tmp_path, mode_live, armed, enabled):
    root = _make_root(tmp_path, armed=armed, live_enabled=enabled)
    settings = _settings("live" if mode_live else "paper")
    if mode_live and armed and enabled:
        assert_live_allowed(settings, root)
    else:
        with pytest.raises(LiveNotAllowedError):
            assert_live_allowed(settings, root)


@pytest.mark.parametrize("value", ["true", "yes", 1, None])
def test_live_enabled_must_be_yaml_boolean_true(tmp_path, value):
    root = _make_root(tmp_path, armed=True, live_enabled=value)
    with pytest.raises(LiveNotAllowedError):
        assert_live_allowed(_settings("live"), root)


def test_missing_risk_yaml_blocks_live(tmp_path):
    (tmp_path / "LIVE_ARMED").write_text("", encoding="utf-8")
    with pytest.raises(LiveNotAllowedError):
        assert_live_allowed(_settings("live"), tmp_path)


def test_live_armed_directory_does_not_count(tmp_path):
    root = _make_root(tmp_path, armed=False, live_enabled=True)
    (root / "LIVE_ARMED").mkdir()
    with pytest.raises(LiveNotAllowedError):
        assert_live_allowed(_settings("live"), root)


def test_repo_risk_config_has_live_disabled():
    data = yaml.safe_load((REPO_ROOT / "config" / "risk.yaml").read_text(encoding="utf-8"))
    assert data["live_enabled"] is False
