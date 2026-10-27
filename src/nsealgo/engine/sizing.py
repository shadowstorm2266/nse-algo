"""Position sizing in whole shares. Pure functions on Decimal rupees."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal

from nsealgo.costs import BrokerageModel, StatutoryRates, fill_charges
from nsealgo.engine.types import RejectReason

ZERO = Decimal(0)


def floor_shares(amount: Decimal, price: Decimal) -> int:
    """Whole shares of `price` that `amount` buys; never negative."""
    if amount <= 0:
        return 0
    return int((amount / price).to_integral_value(rounding=ROUND_FLOOR))


@dataclass(frozen=True, slots=True)
class MisQty:
    by_risk: int
    by_exposure: int
    by_margin: int

    @property
    def qty(self) -> int:
        return min(self.by_risk, self.by_exposure, self.by_margin)

    def __str__(self) -> str:
        return f"by_risk={self.by_risk} by_exposure={self.by_exposure} by_margin={self.by_margin}"


def mis_qty(
    *,
    risk_rupees: Decimal,
    ref: Decimal,
    stop: Decimal,
    remaining_exposure: Decimal,
    free_margin: Decimal,
    margin_fraction: Decimal,
) -> MisQty:
    """min(floor(risk / stop distance), floor(exposure left / price),
    floor(free margin / (price x margin fraction)))."""
    distance = abs(ref - stop)
    if distance == 0:
        raise ValueError("zero stop distance")
    return MisQty(
        by_risk=floor_shares(risk_rupees, distance),
        by_exposure=floor_shares(remaining_exposure, ref),
        by_margin=floor_shares(free_margin, ref * margin_fraction),
    )


@dataclass(frozen=True, slots=True)
class SwingSize:
    qty: int
    reason: RejectReason | None
    detail: str


def swing_qty(
    *,
    price: Decimal,
    equity: Decimal,
    rates: StatutoryRates,
    delivery: BrokerageModel,
    max_positions: int,
    cash_buffer_pct: Decimal,
    position_cap: Decimal,
    gross_left: Decimal,
    pending: Sequence[Decimal],
) -> SwingSize:
    """Equal-weight shares. slot = equity / max_positions. room = gross_left (the gross
    cap less held positions at marks) less what each pending same-morning buy reserves:
    its notional plus the buffer plus its estimated buy charges, so each buy keeps its
    own buffer. Slot and room are each reduced by their own estimated buy charges and
    spent at (100 - cash_buffer_pct)% (the rest absorbs an opening gap, slippage and
    same-morning sell charges).

    If the slot buys no whole share but one share fits the position cap (and the room),
    buy one. If one share is above the position cap, skip the stock. The position cap
    is not reduced by the buffer.
    """
    if price > position_cap:
        detail = f"1 share at {price:.2f} > position cap {position_cap:.2f}"
        return SwingSize(0, RejectReason.PRICE_ABOVE_POSITION_CAP, detail)
    buffer = cash_buffer_pct / 100
    reserved = sum((p * (1 + buffer) + _buy_charges(p, rates, delivery) for p in pending), ZERO)
    per_slot, left = equity / max_positions, gross_left - reserved
    slot = (per_slot - _buy_charges(per_slot, rates, delivery)) * (1 - buffer)
    room = (left - _buy_charges(left, rates, delivery)) * (1 - buffer)
    by_slot = floor_shares(slot, price)
    by_cap = floor_shares(position_cap, price)
    by_gross = floor_shares(room, price)
    qty = min(max(by_slot, 1), by_cap, by_gross)
    detail = (
        f"slot={slot:.2f} room={room:.2f} reserved={reserved:.2f} by_slot={by_slot} "
        f"by_cap={by_cap} by_gross={by_gross} gross_left={gross_left:.2f}"
    )
    if qty < 1:
        return SwingSize(0, RejectReason.QTY_BELOW_ONE, detail)
    return SwingSize(qty, None, detail)


def _buy_charges(value: Decimal, rates: StatutoryRates, delivery: BrokerageModel) -> Decimal:
    """Estimated CNC buy charges on a buy of `value` rupees (zero for none)."""
    if value <= 0:
        return ZERO
    return fill_charges("CNC", "BUY", value, rates, delivery).total
