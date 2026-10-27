"""Exposure arithmetic over an AccountSnapshot, for the RiskGovernor.

Pure functions: they count what is committed and enforce nothing. The limits
themselves are applied only in engine/risk.py.
"""

from decimal import Decimal

from nsealgo.brokers.fills import dec
from nsealgo.engine.config import MarginConfig, SizingBasis
from nsealgo.engine.portfolio import AccountSnapshot
from nsealgo.engine.types import ExitReason, OrderIntent, OrderRole, OrderType, Product

ZERO = Decimal(0)


def reference_price(intent: OrderIntent, snap: AccountSnapshot) -> Decimal | None:
    """Sizing price: the trigger/limit of a STOP/LIMIT entry, else the last visible close."""
    if intent.order_type is not OrderType.MARKET:
        return dec(intent.price)
    mark = snap.marks.get(intent.symbol)
    return dec(mark) if mark is not None and mark > 0 else None


def sizing_shift(
    snap: AccountSnapshot, capital: Decimal, basis: SizingBasis, product: Product
) -> Decimal:
    """What to add to equity and free cash so sizing sees `capital` instead of the
    compounded account (`fixed_capital`; zero for `current_equity`). MIS: capital at the
    session open plus the session's P&L so far. CNC decides after the close for the next
    open: capital exactly (the next session opens at today's closing equity)."""
    if basis == "current_equity":
        return ZERO
    anchor = snap.equity_at_session_start if product is Product.MIS else snap.equity
    return capital - anchor


def fully_exiting(snap: AccountSnapshot) -> set[str]:
    """Symbols whose whole position has a working exit."""
    return {
        v.order.symbol
        for v in snap.working(OrderRole.EXIT)
        if v.order.symbol in snap.positions
        and v.order.qty >= abs(snap.positions[v.order.symbol].qty)
    }


def committed(
    snap: AccountSnapshot, margins: MarginConfig, exclude_group: str | None
) -> tuple[Decimal, Decimal]:
    """(gross exposure, working-entry margin): positions at marks plus working entries.
    An OCO group counts only its larger leg; `exclude_group` (the reviewing leg's own
    group) is left out so each leg is sized against the same pool."""
    exposure = sum((abs(p.qty) * p.mark for p in snap.positions.values()), ZERO)
    units: dict[str, tuple[Decimal, Decimal]] = {}
    for v in snap.working(OrderRole.ENTRY):
        o = v.order
        if exclude_group is not None and o.group_id == exclude_group:
            continue
        notional = o.qty * o.ref_price
        frac = Decimal(1) if o.product is Product.CNC else margins.mis_fraction(o.symbol)
        key = o.group_id or f"#{v.order_id}"
        prev = units.get(key, (ZERO, ZERO))
        units[key] = (max(prev[0], notional), max(prev[1], notional * frac))
    unit_notional = sum((u[0] for u in units.values()), ZERO)
    return exposure + unit_notional, sum((u[1] for u in units.values()), ZERO)


def trades_today(snap: AccountSnapshot) -> tuple[int, int]:
    """(entries filled today, working entry units). An OCO group is one unit."""
    filled = sum(1 for f in snap.fills_today if f.role is OrderRole.ENTRY)
    units = {v.order.group_id or f"#{v.order_id}" for v in snap.working(OrderRole.ENTRY)}
    return filled, len(units)


def strategy_orders_today(snap: AccountSnapshot) -> int:
    """Entries and strategy exits created this session, whatever their status."""
    return sum(
        1
        for v in snap.orders
        if v.order.created_at.date() == snap.session_date
        and (v.order.role is OrderRole.ENTRY or v.order.exit_reason is ExitReason.STRATEGY)
    )


def swing_book(snap: AccountSnapshot) -> tuple[int, list[Decimal], Decimal]:
    """(held positions, pending entries' notionals at their reference price, held gross at
    marks). Positions with a working full exit free their slot and their exposure: sells
    fill before buys at the open."""
    exiting = fully_exiting(snap)
    held = [p for s, p in snap.positions.items() if s not in exiting]
    pending = [v.order.qty * v.order.ref_price for v in snap.working(OrderRole.ENTRY)]
    return len(held), pending, sum((abs(p.qty) * p.mark for p in held), ZERO)
