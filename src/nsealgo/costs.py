"""Trading cost model for NSE equity cash: intraday (MIS) and delivery (CNC), and
equity-ETF units on delivery (instrument "ETF": own STT and stamp rates, everything
else as equity delivery). Equity ("EQ") is the default instrument.

IPO allotments (research only) have their own stamp rule (`IpoCosts`); their listing-day
sale is an ordinary CNC sell.

Pure functions on Decimal rupees. Each component is computed exactly and then
rounded to the paisa (half-up); `total` is the sum of the rounded components.
Slippage is not a charge here: it is applied to fill prices by the simulator, from
the instrument's tier table (`CostConfig.slippage_table`).
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Literal

import yaml

PAISA = Decimal("0.01")
HUNDRED = Decimal(100)
CRORE = Decimal(10_000_000)

BrokerageKind = Literal["zero", "flat_or_pct", "flat"]
Number = Decimal | int | float | str
PRODUCTS = ("MIS", "CNC")
SIDES = ("BUY", "SELL")
INSTRUMENTS = ("EQ", "ETF")


def _dec(x: Number) -> Decimal:
    # str() first so floats like 0.00297 become the decimal they look like.
    return x if isinstance(x, Decimal) else Decimal(str(x))


def _paisa(x: Decimal) -> Decimal:
    return x.quantize(PAISA, rounding=ROUND_HALF_UP)


def _pct(value: Decimal, pct: Decimal) -> Decimal:
    return value * pct / HUNDRED


@dataclass(frozen=True)
class BrokerageModel:
    """Per-order brokerage. Amounts in rupees, `pct` in percent."""

    kind: BrokerageKind
    flat_rupees: Decimal = Decimal(0)
    pct: Decimal = Decimal(0)

    def per_order(self, order_value: Decimal) -> Decimal:
        if self.kind == "zero":
            return Decimal(0)
        if self.kind == "flat":
            return self.flat_rupees
        if self.kind == "flat_or_pct":
            return min(self.flat_rupees, _pct(order_value, self.pct))
        raise ValueError(f"unknown brokerage model {self.kind!r}")


@dataclass(frozen=True)
class BrokerPreset:
    """A broker's charges: per-order brokerage by product, and DP charge before GST."""

    intraday: BrokerageModel
    delivery: BrokerageModel
    dp_charge_per_scrip: Decimal


@dataclass(frozen=True)
class StatutoryRates:
    """Statutory rates; every `*_pct` field is in percent."""

    transaction_charge_pct: Decimal
    sebi_fee_per_crore: Decimal
    gst_pct: Decimal
    intraday_stt_sell_pct: Decimal
    intraday_stamp_buy_pct: Decimal
    delivery_stt_buy_pct: Decimal
    delivery_stt_sell_pct: Decimal
    delivery_stamp_buy_pct: Decimal
    etf_delivery_stt_buy_pct: Decimal
    etf_delivery_stt_sell_pct: Decimal
    etf_delivery_stamp_buy_pct: Decimal

    def delivery(self, instrument: str) -> tuple[Decimal, Decimal, Decimal]:
        """(STT buy, STT sell, stamp buy) percents for a delivery trade in `instrument`."""
        if instrument == "EQ":
            return (
                self.delivery_stt_buy_pct,
                self.delivery_stt_sell_pct,
                self.delivery_stamp_buy_pct,
            )
        if instrument == "ETF":
            return (
                self.etf_delivery_stt_buy_pct,
                self.etf_delivery_stt_sell_pct,
                self.etf_delivery_stamp_buy_pct,
            )
        raise ValueError(f"unknown instrument {instrument!r}")


@dataclass(frozen=True)
class CostBreakdown:
    """Round-trip charges in rupees, each rounded to the paisa."""

    brokerage: Decimal
    stt: Decimal
    transaction_charge: Decimal
    sebi_fee: Decimal
    stamp_duty: Decimal
    gst: Decimal
    dp_charge: Decimal
    total: Decimal


@dataclass(frozen=True)
class CostConfig:
    rates: StatutoryRates
    brokerage_presets: dict[str, BrokerPreset]
    active_brokerage: str
    slippage_bps_per_side: dict[str, Decimal]  # equity
    etf_slippage_bps_per_side: dict[str, Decimal]  # equity-ETF units

    @property
    def broker(self) -> BrokerPreset:
        return self.brokerage_presets[self.active_brokerage]

    def slippage_table(self, instrument: str) -> dict[str, Decimal]:
        """Slippage tiers (bps per side) for fills in `instrument`."""
        if instrument == "EQ":
            return self.slippage_bps_per_side
        if instrument == "ETF":
            return self.etf_slippage_bps_per_side
        raise ValueError(f"unknown instrument {instrument!r}")


def _validate_values(buy_value: Decimal, sell_value: Decimal) -> None:
    if buy_value <= 0 or sell_value <= 0:
        raise ValueError(f"order values must be positive, got buy={buy_value} sell={sell_value}")


def _build(
    *,
    brokerage: Decimal,
    stt: Decimal,
    turnover: Decimal,
    stamp: Decimal,
    dp_charge: Decimal,
    rates: StatutoryRates,
) -> CostBreakdown:
    txn = _pct(turnover, rates.transaction_charge_pct)
    sebi = turnover * rates.sebi_fee_per_crore / CRORE
    gst = _pct(brokerage + txn + sebi + dp_charge, rates.gst_pct)
    parts = [_paisa(p) for p in (brokerage, stt, txn, sebi, stamp, gst, dp_charge)]
    return CostBreakdown(*parts, total=sum(parts, Decimal(0)))


def intraday_round_trip(
    buy_value: Number, sell_value: Number, rates: StatutoryRates, brokerage: BrokerageModel
) -> CostBreakdown:
    """Charges for one MIS buy order and one MIS sell order of the given rupee values."""
    buy, sell = _dec(buy_value), _dec(sell_value)
    _validate_values(buy, sell)
    return _build(
        brokerage=brokerage.per_order(buy) + brokerage.per_order(sell),
        stt=_pct(sell, rates.intraday_stt_sell_pct),
        turnover=buy + sell,
        stamp=_pct(buy, rates.intraday_stamp_buy_pct),
        dp_charge=Decimal(0),
        rates=rates,
    )


def delivery_round_trip(
    buy_value: Number,
    sell_value: Number,
    rates: StatutoryRates,
    brokerage: BrokerageModel,
    dp_charge_per_scrip: Number,
    *,
    instrument: str = "EQ",
) -> CostBreakdown:
    """Charges for one CNC buy and one CNC sell of a single scrip (one DP charge).

    `dp_charge_per_scrip` is before GST; GST is charged on it with the other fees.
    `instrument` "ETF" uses the equity-ETF STT and stamp rates.
    """
    buy, sell = _dec(buy_value), _dec(sell_value)
    _validate_values(buy, sell)
    stt_buy, stt_sell, stamp_buy = rates.delivery(instrument)
    return _build(
        brokerage=brokerage.per_order(buy) + brokerage.per_order(sell),
        stt=_pct(buy, stt_buy) + _pct(sell, stt_sell),
        turnover=buy + sell,
        stamp=_pct(buy, stamp_buy),
        dp_charge=_dec(dp_charge_per_scrip),
        rates=rates,
    )


def fill_charges(
    product: str,
    side: str,
    value: Number,
    rates: StatutoryRates,
    brokerage: BrokerageModel,
    dp_charge: Number = 0,
    *,
    instrument: str = "EQ",
) -> CostBreakdown:
    """Charges for one executed order (one leg) of `value` rupees.

    `product` is "MIS" or "CNC", `side` is "BUY" or "SELL". `dp_charge` (before GST)
    is only allowed on a CNC sell; the caller decides whether this sell is the first
    of the scrip that day. `instrument` "ETF" is allowed only with CNC. Components are
    rounded to the paisa per order, so the two legs of a round trip can differ by a
    few paise from the round-trip functions.
    """
    if product not in PRODUCTS or side not in SIDES or instrument not in INSTRUMENTS:
        raise ValueError(f"unknown product/side/instrument {product!r}/{side!r}/{instrument!r}")
    if instrument == "ETF" and product != "CNC":
        raise ValueError("ETF charges are modelled for delivery (CNC) only")
    v, dp = _dec(value), _dec(dp_charge)
    if v <= 0:
        raise ValueError(f"order value must be positive, got {v}")
    if dp and not (product == "CNC" and side == "SELL"):
        raise ValueError("DP charge applies only to CNC sells")
    buy = side == "BUY"
    if product == "MIS":
        stt = Decimal(0) if buy else _pct(v, rates.intraday_stt_sell_pct)
        stamp = _pct(v, rates.intraday_stamp_buy_pct) if buy else Decimal(0)
    else:
        stt_buy, stt_sell, stamp_buy = rates.delivery(instrument)
        stt = _pct(v, stt_buy if buy else stt_sell)
        stamp = _pct(v, stamp_buy) if buy else Decimal(0)
    return _build(
        brokerage=brokerage.per_order(v),
        stt=stt,
        turnover=v,
        stamp=stamp,
        dp_charge=dp,
        rates=rates,
    )


def _parse_brokerage(raw: dict[str, Any]) -> BrokerageModel:
    kind = raw["model"]
    if kind not in ("zero", "flat_or_pct", "flat"):
        raise ValueError(f"unknown brokerage model {kind!r}")
    if kind == "zero":
        return BrokerageModel("zero")
    pct = _dec(raw["pct"]) if kind == "flat_or_pct" else Decimal(0)
    return BrokerageModel(kind, flat_rupees=_dec(raw["flat_rupees"]), pct=pct)


def _parse_preset(raw: dict[str, Any]) -> BrokerPreset:
    return BrokerPreset(
        intraday=_parse_brokerage(raw["intraday"]),
        delivery=_parse_brokerage(raw["delivery"]),
        dp_charge_per_scrip=_dec(raw["dp_charge_per_scrip_rupees"]),
    )


def load_cost_config(path: Path) -> CostConfig:
    """Parse config/costs.yaml. Missing keys raise KeyError rather than defaulting."""
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    st = raw["statutory"]
    rates = StatutoryRates(
        transaction_charge_pct=_dec(st["transaction_charge_pct"]),
        sebi_fee_per_crore=_dec(st["sebi_fee_per_crore"]),
        gst_pct=_dec(st["gst_pct"]),
        intraday_stt_sell_pct=_dec(st["intraday"]["stt_sell_pct"]),
        intraday_stamp_buy_pct=_dec(st["intraday"]["stamp_buy_pct"]),
        delivery_stt_buy_pct=_dec(st["delivery"]["stt_buy_pct"]),
        delivery_stt_sell_pct=_dec(st["delivery"]["stt_sell_pct"]),
        delivery_stamp_buy_pct=_dec(st["delivery"]["stamp_buy_pct"]),
        etf_delivery_stt_buy_pct=_dec(st["etf_delivery"]["stt_buy_pct"]),
        etf_delivery_stt_sell_pct=_dec(st["etf_delivery"]["stt_sell_pct"]),
        etf_delivery_stamp_buy_pct=_dec(st["etf_delivery"]["stamp_buy_pct"]),
    )
    presets = {name: _parse_preset(p) for name, p in raw["brokerage"]["presets"].items()}
    active = raw["brokerage"]["active"]
    if active not in presets:
        raise ValueError(f"active brokerage preset {active!r} not in presets")
    return CostConfig(
        rates=rates,
        brokerage_presets=presets,
        active_brokerage=active,
        slippage_bps_per_side={k: _dec(v) for k, v in raw["slippage_bps_per_side"].items()},
        etf_slippage_bps_per_side={k: _dec(v) for k, v in raw["etf_slippage_bps_per_side"].items()},
    )


@dataclass(frozen=True)
class IpoCosts:
    """IPO allotment charges and listing-sale slippage tiers (config/costs.yaml `ipo`,
    `ipo_listing_slippage_pct`). Every `*_pct` field is in percent."""

    stamp_rule_from: date
    allotment_stamp_pct: Decimal
    allotment_stamp_pct_before_rule: Decimal
    listing_slippage_pct: dict[str, Decimal]

    def allotment_charges(self, value: Number, allotment_date: date) -> Decimal:
        """Charges on an allotment of `value` rupees: stamp duty only (no brokerage, no
        STT), at the rate in force on `allotment_date`."""
        before = allotment_date < self.stamp_rule_from
        pct = self.allotment_stamp_pct_before_rule if before else self.allotment_stamp_pct
        return _paisa(_pct(_dec(value), pct))


def load_ipo_costs(path: Path) -> IpoCosts:
    """Parse the IPO entries of config/costs.yaml. Missing keys raise KeyError."""
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    ipo = raw["ipo"]
    return IpoCosts(
        stamp_rule_from=ipo["stamp_rule_from"],
        allotment_stamp_pct=_dec(ipo["allotment_stamp_pct"]),
        allotment_stamp_pct_before_rule=_dec(ipo["allotment_stamp_pct_before_rule"]),
        listing_slippage_pct={k: _dec(v) for k, v in raw["ipo_listing_slippage_pct"].items()},
    )
