from dataclasses import astuple
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nsealgo.costs import (
    BrokerageModel,
    CostConfig,
    delivery_round_trip,
    fill_charges,
    intraday_round_trip,
    load_cost_config,
)
from nsealgo.settings import REPO_ROOT

D = Decimal


@pytest.fixture(scope="module")
def cfg() -> CostConfig:
    return load_cost_config(REPO_ROOT / "config" / "costs.yaml")


@pytest.mark.parametrize(
    ("preset", "expected"),
    [("zero", D("17.62")), ("shoonya", D("29.42")), ("dhan", D("53.02"))],
)
def test_intraday_50k_round_trip_to_the_paisa(cfg, preset, expected):
    cb = intraday_round_trip(50_000, 50_000, cfg.rates, cfg.brokerage_presets[preset].intraday)
    assert cb.total == expected


def test_intraday_50k_components_dhan(cfg):
    cb = intraday_round_trip(50_000, 50_000, cfg.rates, cfg.brokerage_presets["dhan"].intraday)
    assert cb.brokerage == D("30.00")  # min(20, 15) per leg
    assert cb.stt == D("12.50")
    assert cb.transaction_charge == D("2.97")
    assert cb.sebi_fee == D("0.10")
    assert cb.stamp_duty == D("1.50")
    assert cb.gst == D("5.95")  # 18% of 33.07
    assert cb.dp_charge == D("0.00")


def test_intraday_unequal_legs(cfg):
    cb = intraday_round_trip(50_000, 51_000, cfg.rates, cfg.brokerage_presets["zero"].intraday)
    assert cb.stt == D("12.75")
    assert cb.transaction_charge == D("3.00")  # 2.9997
    assert cb.sebi_fee == D("0.10")  # 0.101
    assert cb.stamp_duty == D("1.50")
    assert cb.gst == D("0.56")  # 18% of 3.1007 = 0.558126
    assert cb.total == D("17.91")


def _delivery(cfg: CostConfig, preset: str, buy: int, sell: int):
    p = cfg.brokerage_presets[preset]
    return delivery_round_trip(buy, sell, cfg.rates, p.delivery, p.dp_charge_per_scrip)


@pytest.mark.parametrize(
    ("preset", "expected"),
    # Per-charge paisa rounding, as on contract notes (unrounded sums: 21.73226, 25.86226).
    [("shoonya", D("21.74")), ("dhan", D("25.87"))],
)
def test_delivery_5k_round_trip_to_the_paisa(cfg, preset, expected):
    assert _delivery(cfg, preset, 5_000, 5_000).total == expected


def test_delivery_5k_components_shoonya(cfg):
    cb = _delivery(cfg, "shoonya", 5_000, 5_000)
    assert cb.brokerage == D("0.00")
    assert cb.stt == D("10.00")
    assert cb.transaction_charge == D("0.30")  # 0.297
    assert cb.sebi_fee == D("0.01")
    assert cb.stamp_duty == D("0.75")
    assert cb.dp_charge == D("9.00")
    assert cb.gst == D("1.68")  # 18% of (0.297 + 0.01 + 9) = 1.67526


def test_presets_from_config(cfg):
    sh, dh = cfg.brokerage_presets["shoonya"], cfg.brokerage_presets["dhan"]
    assert sh.intraday == BrokerageModel("flat_or_pct", flat_rupees=D(5), pct=D("0.03"))
    assert dh.intraday == BrokerageModel("flat_or_pct", flat_rupees=D(20), pct=D("0.03"))
    assert sh.delivery == dh.delivery == BrokerageModel("zero")
    assert sh.dp_charge_per_scrip == D(9)
    assert dh.dp_charge_per_scrip == D("12.50")
    assert cfg.brokerage_presets["zero"].dp_charge_per_scrip == 0


def test_brokerage_models():
    assert BrokerageModel("zero").per_order(D(10**6)) == 0
    assert BrokerageModel("flat", flat_rupees=D(20)).per_order(D(100)) == D(20)
    fop = BrokerageModel("flat_or_pct", flat_rupees=D(20), pct=D("0.03"))
    assert fop.per_order(D(10_000)) == D(3)  # 0.03% lower
    assert fop.per_order(D(100_000)) == D(20)  # flat lower


@pytest.mark.parametrize(("buy", "sell"), [(0, 100), (100, 0), (-5, 100)])
def test_non_positive_values_rejected(cfg, buy, sell):
    with pytest.raises(ValueError):
        intraday_round_trip(buy, sell, cfg.rates, cfg.broker.intraday)


def test_config_presets_and_slippage(cfg):
    assert set(cfg.brokerage_presets) == {"zero", "shoonya", "dhan"}
    assert cfg.slippage_bps_per_side == {"base": D(3), "stress1": D(6), "stress2": D(10)}


values = st.decimals(min_value=D("1"), max_value=D("10000000"), places=2)


@given(buy=values, sell=values, preset=st.sampled_from(["zero", "shoonya", "dhan"]))
def test_total_is_sum_and_components_non_negative(cfg, buy, sell, preset):
    p = cfg.brokerage_presets[preset]
    for cb in (
        intraday_round_trip(buy, sell, cfg.rates, p.intraday),
        delivery_round_trip(buy, sell, cfg.rates, p.delivery, p.dp_charge_per_scrip),
    ):
        parts = astuple(cb)[:-1]
        assert all(p >= 0 for p in parts)
        assert cb.total == sum(parts)
        # Below ~Rs 100 a leg, paisa rounding can legitimately make every component 0.
        if min(buy, sell) >= 100:
            assert cb.total > 0


@given(buy=values, sell=values)
def test_delivery_statutory_exceeds_intraday(cfg, buy, sell):
    # Same (zero) brokerage and no DP: delivery STT and stamp are higher on every trade.
    z = BrokerageModel("zero")
    assert (
        delivery_round_trip(buy, sell, cfg.rates, z, 0).total
        >= intraday_round_trip(buy, sell, cfg.rates, z).total
    )


# --- per-fill charges (one order) ---


def test_mis_buy_leg_known_answer(cfg):
    # 20 x 500.15 = 10003.00. Brokerage min(5, 3.0009); txn 0.2970891; SEBI 0.010003;
    # stamp 0.30009; GST 18% of 3.3079921 = 0.5954...
    cb = fill_charges("MIS", "BUY", D("10003.00"), cfg.rates, cfg.broker.intraday)
    assert (cb.brokerage, cb.stt, cb.transaction_charge) == (D("3.00"), D("0.00"), D("0.30"))
    assert (cb.sebi_fee, cb.stamp_duty, cb.gst, cb.dp_charge) == (
        D("0.01"),
        D("0.30"),
        D("0.60"),
        0,
    )
    assert cb.total == D("4.21")


def test_mis_sell_leg_known_answer(cfg):
    # 20 x 509.847 = 10196.94. Brokerage 3.059082; STT 2.549235; txn 0.30285;
    # SEBI 0.0102; GST 18% of 3.37212806 = 0.6070
    cb = fill_charges("MIS", "SELL", D("10196.94"), cfg.rates, cfg.broker.intraday)
    assert (cb.brokerage, cb.stt, cb.stamp_duty, cb.gst) == (D("3.06"), D("2.55"), 0, D("0.61"))
    assert cb.total == D("6.53")


def test_cnc_legs_and_dp_only_on_sell(cfg):
    p = cfg.brokerage_presets["shoonya"]
    buy = fill_charges("CNC", "BUY", 5_000, cfg.rates, p.delivery)
    assert (buy.stt, buy.stamp_duty, buy.dp_charge) == (D("5.00"), D("0.75"), 0)
    sell = fill_charges("CNC", "SELL", 5_000, cfg.rates, p.delivery, p.dp_charge_per_scrip)
    assert (sell.stt, sell.stamp_duty, sell.dp_charge) == (D("5.00"), 0, D("9.00"))
    assert sell.gst == D("1.65")  # 18% of (txn 0.1485 + SEBI 0.005 + DP 9) = 1.64763
    with pytest.raises(ValueError):
        fill_charges("CNC", "BUY", 5_000, cfg.rates, p.delivery, 9)
    with pytest.raises(ValueError):
        fill_charges("MIS", "SELL", 5_000, cfg.rates, p.intraday, 9)


@pytest.mark.parametrize(("product", "side"), [("NRML", "BUY"), ("MIS", "HOLD")])
def test_fill_charges_rejects_unknown_product_or_side(cfg, product, side):
    with pytest.raises(ValueError):
        fill_charges(product, side, 1_000, cfg.rates, cfg.broker.intraday)


@given(buy=values, sell=values, preset=st.sampled_from(["zero", "shoonya", "dhan"]))
def test_fill_legs_match_round_trip_within_rounding(cfg, buy, sell, preset):
    # Seven components, each rounded once per leg instead of once per round trip.
    p = cfg.brokerage_presets[preset]
    mis = (
        fill_charges("MIS", "BUY", buy, cfg.rates, p.intraday).total
        + fill_charges("MIS", "SELL", sell, cfg.rates, p.intraday).total
    )
    assert abs(mis - intraday_round_trip(buy, sell, cfg.rates, p.intraday).total) <= D("0.07")
    cnc = (
        fill_charges("CNC", "BUY", buy, cfg.rates, p.delivery).total
        + fill_charges("CNC", "SELL", sell, cfg.rates, p.delivery, p.dp_charge_per_scrip).total
    )
    rt = delivery_round_trip(buy, sell, cfg.rates, p.delivery, p.dp_charge_per_scrip).total
    assert abs(cnc - rt) <= D("0.07")
