"""Position sizing in whole shares. Pure functions on Decimal rupees."""

from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal

from nsealgo.engine.types import RejectReason


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
    est_buy_charges: Decimal,
    max_positions: int,
    cash_buffer_pct: Decimal,
    position_cap: Decimal,
    remaining_gross: Decimal,
) -> SwingSize:
    """Equal-weight shares: slot = (equity - estimated buy charges) / max_positions,
    of which (100 - cash_buffer_pct)% is spent (the rest absorbs an opening gap).

    If that buys no whole share but one share fits the position cap (and the gross
    cap), buy one. If one share is above the position cap, skip the stock. The caps
    are not reduced by the buffer.
    """
    if price > position_cap:
        detail = f"1 share at {price:.2f} > position cap {position_cap:.2f}"
        return SwingSize(0, RejectReason.PRICE_ABOVE_POSITION_CAP, detail)
    slot = (equity - est_buy_charges) / max_positions * (1 - cash_buffer_pct / 100)
    by_slot = floor_shares(slot, price)
    by_cap = floor_shares(position_cap, price)
    by_gross = floor_shares(remaining_gross, price)
    qty = min(max(by_slot, 1), by_cap, by_gross)
    detail = (
        f"slot={slot:.2f} by_slot={by_slot} by_cap={by_cap} by_gross={by_gross} "
        f"remaining_gross={remaining_gross:.2f}"
    )
    if qty < 1:
        return SwingSize(0, RejectReason.QTY_BELOW_ONE, detail)
    return SwingSize(qty, None, detail)
