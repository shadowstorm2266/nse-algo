"""ETF proxy series (strategy 4 data): known answers on synthetic index rows, the
build's refusals, and the repo's config."""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from nsealgo.data.etf_proxy import (
    PROXY_COLS,
    EtfProxyConfig,
    accrual_factor,
    build_proxies,
    load_etf_proxy_config,
    proxy_bars,
    read_index,
)

D1, D2, D3 = date(2016, 1, 4), date(2016, 1, 5), date(2016, 1, 8)
MUHURAT = date(2016, 1, 7)  # an index row that is not a calendar session


def index_rows() -> pd.DataFrame:
    # date, price open/high/low/close, tri
    rows = [
        (D1, 101.0, 102.0, 99.0, 100.0, 2000.0),
        (D2, 99.0, 110.0, 98.0, 105.0, 2100.0),
        (MUHURAT, 105.0, 106.0, 104.0, 105.5, 2110.0),
        (D3, 104.0, 108.0, 100.0, 102.0, 2050.0),
    ]
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "tri"])


def test_close_is_rebased_tri_less_daily_accrued_expenses():
    out = proxy_bars(index_rows(), [D1, D2, D3], 0.40, "PX_X")
    assert list(out.columns) == PROXY_COLS and list(out["session_date"]) == [D1, D2, D3]
    keep = 1 - 0.004 / 365
    # D2 is 1 calendar day after D1, D3 is 4 (a weekend and the dropped day in between)
    expected = [100.0, 105.0 * keep, 102.5 * keep**4]
    np.testing.assert_allclose(out["close"], expected, rtol=1e-12)
    assert (out["symbol"] == "PX_X").all()


def test_open_high_low_scale_the_close_by_the_price_index_ratios():
    out = proxy_bars(index_rows(), [D1, D2, D3], 0.40, "PX_X").set_index("session_date")
    c = out.loc[D2, "close"]
    assert out.loc[D2, "open"] == pytest.approx(c * 99 / 105, rel=1e-12)
    assert out.loc[D2, "high"] == pytest.approx(c * 110 / 105, rel=1e-12)
    assert out.loc[D2, "low"] == pytest.approx(c * 98 / 105, rel=1e-12)
    assert out.loc[D1, "open"] == pytest.approx(101.0, rel=1e-12)


def test_a_year_of_accrual_costs_the_expense_ratio():
    assert 1 - accrual_factor(np.array([365]), 0.40)[0] == pytest.approx(0.003992, abs=1e-6)
    assert 1 - accrual_factor(np.array([365]), 0.05)[0] == pytest.approx(0.0005, abs=1e-6)
    assert accrual_factor(np.array([0]), 0.40)[0] == 1.0


def test_zero_expense_ratio_is_the_rebased_tri():
    out = proxy_bars(index_rows(), [D1, D2, D3], 0.0, "PX_X")
    np.testing.assert_allclose(out["close"], [100.0, 105.0, 102.5], rtol=1e-12)


def test_rebase_is_on_the_first_kept_session():
    out = proxy_bars(index_rows(), [D2, D3], 0.40, "PX_X")
    assert out["close"].iloc[0] == 100.0
    assert out["close"].iloc[1] == pytest.approx(100 * 2050 / 2100 * (1 - 0.004 / 365) ** 3)


def test_a_session_without_an_index_row_fails():
    with pytest.raises(ValueError, match="no complete positive row"):
        proxy_bars(index_rows(), [D1, D2, date(2016, 1, 6), D3], 0.40, "PX_X")


@pytest.mark.parametrize(("col", "value"), [("tri", np.nan), ("open", 0.0), ("low", -1.0)])
def test_missing_or_non_positive_values_fail(col, value):
    rows = index_rows()
    rows.loc[1, col] = value
    with pytest.raises(ValueError, match="no complete positive row"):
        proxy_bars(rows, [D1, D2, D3], 0.40, "PX_X")


def test_high_low_outside_open_close_fails():
    rows = index_rows()
    rows.loc[1, "high"] = 104.0  # below the close of 105
    with pytest.raises(ValueError, match="high/low"):
        proxy_bars(rows, [D1, D2, D3], 0.40, "PX_X")


def test_sessions_must_be_ascending_and_unique():
    with pytest.raises(ValueError, match="ascending"):
        proxy_bars(index_rows(), [D2, D1], 0.40, "PX_X")
    with pytest.raises(ValueError, match="ascending"):
        proxy_bars(index_rows(), [D1, D1], 0.40, "PX_X")


def write_raw(raw: Path, key: str) -> None:
    raw.mkdir(parents=True, exist_ok=True)
    (raw / f"{key}_price.csv").write_text(
        "date,open,high,low,close\n2016-01-04,101,102,99,100\n2016-01-05,99,110,98,105\n",
        encoding="utf-8",
    )
    (raw / f"{key}_tri.csv").write_text(
        "date,tri,ntr\n2016-01-04,2000,-\n2016-01-05,2100,-\n2016-01-06,2200,-\n",
        encoding="utf-8",
    )


def test_read_index_merges_price_and_tri_and_reads_dashes_as_missing(tmp_path):
    write_raw(tmp_path, "bank")
    df = read_index(tmp_path, "bank")
    assert list(df["date"]) == [D1, D2, date(2016, 1, 6)]
    assert df.loc[2, ["open", "close"]].isna().all() and df.loc[2, "tri"] == 2200


def config(raw: Path, **over) -> EtfProxyConfig:
    base = {
        "raw_dir": raw,
        "series": {
            "PX_B": {"index": "bank", "expense_ratio_pct": 0.40},
            "PX_N": {"index": "nifty", "expense_ratio_pct": 0.05},
        },
        "universe": ["PX_B"],
        "benchmark": "PX_N",
    }
    return EtfProxyConfig.model_validate(base | over)


def test_build_proxies_reads_every_series_with_its_own_expense_ratio(tmp_path):
    for key in ("bank", "nifty"):
        write_raw(tmp_path, key)
    out = build_proxies(config(tmp_path), [D1, D2]).set_index(["symbol", "session_date"])
    assert out.loc[("PX_B", D2), "close"] == pytest.approx(105 * (1 - 0.004 / 365))
    assert out.loc[("PX_N", D2), "close"] == pytest.approx(105 * (1 - 0.0005 / 365))


@pytest.mark.parametrize(
    "over",
    [
        {"universe": ["PX_B", "PX_Z"]},  # unknown series
        {"benchmark": "PX_Z"},
        {"universe": ["PX_B", "PX_N"]},  # benchmark traded
        {"universe": ["PX_B", "PX_B"]},
    ],
)
def test_config_rejects_inconsistent_universe_or_benchmark(tmp_path, over):
    with pytest.raises(ValidationError):
        config(tmp_path, **over)


def test_repo_config_is_the_owners_11_sectors_and_the_nifty_50_benchmark():
    cfg = load_etf_proxy_config()
    sectors = {"bank", "it", "pharma", "fmcg", "auto", "metal", "realty", "energy"}
    sectors |= {"psubank", "infra", "finserv"}
    assert {cfg.series[s].index for s in cfg.universe} == sectors
    assert len(cfg.universe) == 11 and all(s.startswith("PX_") for s in cfg.series)
    assert all(cfg.series[s].expense_ratio_pct == 0.40 for s in cfg.universe)
    bench = cfg.series[cfg.benchmark]
    assert bench.index == "nifty50" and bench.expense_ratio_pct == 0.05
    assert cfg.raw_dir.is_absolute()
