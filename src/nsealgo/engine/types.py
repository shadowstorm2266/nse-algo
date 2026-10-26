"""Intents, orders, fills and rejections shared by strategies, the RiskGovernor and brokers.

Strategies speak in floats (`OrderIntent`); everything after the RiskGovernor is
Decimal rupees so fills and P&L are exact. Timestamps are tz-aware Asia/Kolkata.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

import pandas as pd

from nsealgo.costs import CostBreakdown


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"

    @property
    def sign(self) -> int:
        return 1 if self is Side.BUY else -1

    def opposite(self) -> "Side":
        return Side.SELL if self is Side.BUY else Side.BUY


class Product(StrEnum):
    MIS = "MIS"
    CNC = "CNC"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class IntentKind(StrEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class OrderRole(StrEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"  # strategy exit or a forced exit (market)
    STOP = "STOP"  # bracket stop-loss child
    TARGET = "TARGET"  # bracket target child


class OrderStatus(StrEnum):
    WORKING = "WORKING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class ExitReason(StrEnum):
    STOP = "stop"
    TARGET = "target"
    STRATEGY = "strategy"
    FLAT_BY = "flat_by"
    SESSION_END_FALLBACK = "session_end_fallback"
    END_OF_RUN = "end_of_run"


class RejectReason(StrEnum):
    KILL_SWITCH = "KILL_SWITCH"
    DRAWDOWN_HALT = "DRAWDOWN_HALT"
    NO_TRADE_SESSION = "NO_TRADE_SESSION"
    BEFORE_ENTRY_START = "BEFORE_ENTRY_START"
    AFTER_ENTRY_END = "AFTER_ENTRY_END"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    MAX_TRADES_PER_DAY = "MAX_TRADES_PER_DAY"
    MAX_ORDERS_PER_DAY = "MAX_ORDERS_PER_DAY"
    MAX_POSITIONS = "MAX_POSITIONS"
    POSITION_EXISTS = "POSITION_EXISTS"
    INVALID_INTENT = "INVALID_INTENT"
    INVALID_GROUP = "INVALID_GROUP"
    GROUP_LEG_REJECTED = "GROUP_LEG_REJECTED"
    INVALID_STOP = "INVALID_STOP"
    NO_PRICE = "NO_PRICE"
    QTY_BELOW_ONE = "QTY_BELOW_ONE"
    PRICE_ABOVE_POSITION_CAP = "PRICE_ABOVE_POSITION_CAP"
    SHORT_NOT_ALLOWED = "SHORT_NOT_ALLOWED"
    SWING_DISABLED = "SWING_DISABLED"
    WRONG_PRODUCT = "WRONG_PRODUCT"
    NO_POSITION = "NO_POSITION"
    DUPLICATE_EXIT = "DUPLICATE_EXIT"
    NO_NEXT_SESSION = "NO_NEXT_SESSION"
    INSUFFICIENT_CASH = "INSUFFICIENT_CASH"  # raised by the broker at fill time


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """What a strategy wants. The RiskGovernor decides whether and how much.

    Entries: `side` is required; `price` is the trigger (STOP) or limit (LIMIT);
    MIS entries need `stop_loss`. Exits close `qty` shares (None = all) at market.
    Two STOP/LIMIT MIS entry legs sharing `group_id` form an OCO entry group.
    """

    kind: IntentKind
    symbol: str
    product: Product
    side: Side | None = None
    order_type: OrderType = OrderType.MARKET
    price: float | None = None
    stop_loss: float | None = None
    target: float | None = None
    qty: int | None = None
    rank: int | None = None
    group_id: str | None = None
    tag: str = ""


@dataclass(frozen=True, slots=True)
class Order:
    """An order approved by the RiskGovernor (or a bracket child made by the broker)."""

    symbol: str
    product: Product
    side: Side
    qty: int
    order_type: OrderType
    role: OrderRole
    created_at: pd.Timestamp
    price: Decimal | None = None  # trigger (STOP) or limit (LIMIT)
    ref_price: Decimal | None = None  # price used for sizing
    stop_loss: Decimal | None = None  # entries: bracket stop child
    target: Decimal | None = None  # entries: bracket target child
    exit_reason: ExitReason | None = None
    group_id: str | None = None
    parent_id: int | None = None
    rank: int | None = None
    not_before: date | None = None  # first session the order may fill in
    expires_at: pd.Timestamp | None = None  # expires on bars starting after this
    tag: str = ""


@dataclass(frozen=True, slots=True)
class OrderView:
    """Read-only state of one broker order."""

    order_id: int
    order: Order
    status: OrderStatus


@dataclass(frozen=True, slots=True)
class Fill:
    order_id: int
    symbol: str
    product: Product
    side: Side
    qty: int
    ts: pd.Timestamp  # start of the bar in which the order filled
    session_date: date
    price: Decimal  # including slippage
    ref_price: Decimal  # before slippage
    charges: CostBreakdown
    role: OrderRole
    exit_reason: ExitReason | None = None
    group_id: str | None = None
    stop_loss: Decimal | None = None

    @property
    def value(self) -> Decimal:
        return self.price * self.qty

    @property
    def slippage(self) -> Decimal:
        return abs(self.price - self.ref_price) * self.qty


@dataclass(frozen=True, slots=True)
class Rejection:
    now: pd.Timestamp
    symbol: str
    reason: RejectReason
    detail: str
    kind: str  # ENTRY, EXIT or BROKER
    price: float | None = None
    rank: int | None = None
    group_id: str | None = None


@dataclass(frozen=True, slots=True)
class HaltRecord:
    """The first time the account drawdown reached the halt threshold."""

    date: date
    at: pd.Timestamp
    drawdown_pct: float
    equity: Decimal
    peak: Decimal
