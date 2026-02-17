"""
antigravity_harness/execution/adapter_base.py
=============================================
Broker-agnostic adapter interfaces for TRADER_OPS.

These ABCs define the contracts that ALL broker adapters must satisfy.
No broker library (ib_insync, rithmic, tradovate, ccxt) is imported here
or anywhere in the core engine. Broker-specific code lives only in
execution/<broker_name>_adapter.py.

Architecture rule: the engine imports these interfaces.
The interfaces never import the engine. Dependency flows one way.

Does NOT: contain broker logic, live calls, or strategy code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

# ─── Value Types ──────────────────────────────────────────────────────────────


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"   # Immediate or Cancel
    FOK = "FOK"   # Fill or Kill


@dataclass(frozen=True)
class OrderIntent:
    """
    A proposed order, before it reaches the broker.
    Produced by strategy layer. Vetted by safety layer. Sent via adapter.
    Contains NO broker-specific fields.
    """
    symbol: str
    side: OrderSide
    quantity: int                        # Contracts for futures
    order_type: OrderType
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    client_order_id: str = ""            # Idempotency key, set by WAL
    parent_order_id: Optional[str] = None  # For bracket leg linkage


@dataclass
class OrderAck:
    """Broker's acknowledgement of a submitted order."""
    broker_order_id: str
    client_order_id: str
    status: OrderStatus
    submitted_at_utc: datetime
    broker_raw: Dict[str, Any] = field(default_factory=dict)  # original broker payload


@dataclass
class Fill:
    """A single execution (partial or complete fill)."""
    broker_order_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    filled_qty: int
    fill_price: Decimal
    fill_time_utc: datetime
    commission_usd: float
    slippage_realized_ticks: Optional[int] = None  # Set by FillTape after recording
    broker_raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Position:
    """Current position state for one instrument."""
    symbol: str
    quantity: int                # Positive = long, negative = short, 0 = flat
    average_cost: Decimal
    unrealized_pnl_usd: float
    realized_pnl_today_usd: float


@dataclass(frozen=True)
class Bar:
    """One OHLCV bar from any timeframe."""
    symbol: str
    timestamp_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str               # e.g. "5m", "1h", "1d"


# ─── Capability Flags ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AdapterCapabilities:
    """
    Describes what a specific broker adapter can do natively.
    The safety and flatten layers use these to decide execution strategy.

    If a capability is False, the adapter layer emulates it in software
    (e.g., software stop tracking instead of server-side brackets).
    """
    # Order management
    supports_server_side_brackets: bool = False
    """Broker will manage stop + target as a bracket order natively."""

    supports_oco: bool = False
    """Broker supports One-Cancels-Other order pairs."""

    supports_cancel_replace: bool = False
    """Broker supports atomic cancel-and-replace for order modification."""

    supports_order_status_push: bool = False
    """Broker pushes order status updates via WebSocket (vs. polling only)."""

    # Market data
    supports_real_time_bars: bool = False
    """Adapter can stream real-time bars (not just snapshots)."""

    supports_historical_bars: bool = True
    """Adapter can fetch historical OHLCV bars for DataTape population."""

    supports_level2: bool = False
    """Adapter can provide order book depth data."""

    # Account
    supports_paper_mode: bool = True
    """Adapter can switch to paper/simulation without code changes."""

    # Futures-specific
    supports_rollover_query: bool = False
    """Adapter can query active contract and expiry date directly."""


# ─── Execution Adapter ABC ────────────────────────────────────────────────────


class ExecutionAdapter(ABC):
    """
    Broker-agnostic execution interface.

    Implementations: IBKRAdapter, TradovateAdapter, SimExecutionAdapter.
    The safety layer and engine import THIS class, never a concrete implementation.

    Lifecycle:
        adapter.connect()
        # ... trading ...
        adapter.disconnect()   # always in a finally block
    """

    @property
    @abstractmethod
    def capabilities(self) -> AdapterCapabilities:
        """Declare what this broker supports natively."""
        ...

    @property
    @abstractmethod
    def is_paper(self) -> bool:
        """True if connected to a paper/simulation account."""
        ...

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to broker. Raise on failure."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Cleanly close connection. Always call in finally block."""
        ...

    @abstractmethod
    async def get_position(self, symbol: str) -> Position:
        """Return current position for symbol. Returns qty=0 if flat."""
        ...

    @abstractmethod
    async def get_all_positions(self) -> List[Position]:
        """Return all open positions."""
        ...

    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderAck]:
        """Return all open (unfilled, uncanccelled) orders, optionally filtered by symbol."""
        ...

    @abstractmethod
    async def submit_order(self, intent: OrderIntent) -> OrderAck:
        """Submit an order. Returns broker acknowledgement. Raise on rejection."""
        ...

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel an order by broker ID. Returns True if cancelled, False if already filled."""
        ...

    @abstractmethod
    async def get_account_cash(self) -> float:
        """Return available cash in USD."""
        ...

    @abstractmethod
    async def get_realized_pnl_today(self) -> float:
        """Return realized P&L for current session in USD."""
        ...


# ─── Market Data Adapter ABC ──────────────────────────────────────────────────


class MarketDataAdapter(ABC):
    """
    Broker-agnostic market data interface.

    In research/backtest mode, this is backed by a DataTape (file on disk).
    In paper/live mode, this streams from the broker.
    The engine never knows the difference — it only sees this interface.
    """

    @property
    @abstractmethod
    def capabilities(self) -> AdapterCapabilities:
        ...

    @abstractmethod
    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start_utc: datetime,
        end_utc: datetime,
        rth_only: bool = True,
    ) -> List[Bar]:
        """Fetch historical OHLCV bars. RTH-only enforced for RTH strategies."""
        ...

    @abstractmethod
    async def get_latest_bar(self, symbol: str, timeframe: str) -> Bar:
        """Fetch the most recently completed bar."""
        ...

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """Fetch current mid price (or last trade price)."""
        ...


# ─── Calendar Adapter ABC ─────────────────────────────────────────────────────


class CalendarAdapter(ABC):
    """
    Trading calendar interface.

    Enforces RTH session rules, early-close days (day after Thanksgiving,
    Christmas Eve, etc.), DST transitions, and market holidays.
    Used by safety layer to gate new order submissions.

    Does NOT: contain strategy logic or broker calls.
    """

    @abstractmethod
    def is_trading_day(self, d: date) -> bool:
        """True if the market is open on this calendar date."""
        ...

    @abstractmethod
    def session_open_utc(self, d: date) -> Optional[datetime]:
        """RTH session open as UTC datetime. None if market closed."""
        ...

    @abstractmethod
    def session_close_utc(self, d: date) -> Optional[datetime]:
        """RTH session close as UTC datetime. Accounts for early closes."""
        ...

    @abstractmethod
    def is_early_close(self, d: date) -> bool:
        """True if this is an early-close day (e.g. day before major holiday)."""
        ...

    @abstractmethod
    def next_trading_day(self, d: date) -> date:
        """Return the next calendar date on which the market is open."""
        ...

    def no_new_positions_time_utc(self, d: date) -> Optional[datetime]:
        """
        Latest time to enter new positions. Default: 10 min before session close.
        Override in subclass if broker/firm has different rule.
        """
        close = self.session_close_utc(d)
        if close is None:
            return None
        return close - timedelta(minutes=10)

    def flatten_by_utc(self, d: date) -> Optional[datetime]:
        """
        Hard flatten deadline. Default: 5 min before session close.
        All positions must be flat at or before this time.
        """
        close = self.session_close_utc(d)
        if close is None:
            return None
        return close - timedelta(minutes=5)


# ─── Event Adapter ABC ────────────────────────────────────────────────────────


class EventAdapter(ABC):
    """
    News and economic event interface.

    In research mode: reads from EventTape (file on disk).
    In live mode: streams from a news provider.
    Used by news-blackout filter in safety layer and signal enrichment.

    Does NOT: make trading decisions. Does NOT call brokers.
    """

    @abstractmethod
    async def get_events_for_session(
        self,
        d: date,
        symbols: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return all economic/news events for a trading session.
        Each event dict must contain: event_id, event_time_utc, tier (1/2/3), headline.
        """
        ...

    @abstractmethod
    def is_news_blackout(
        self,
        check_time_utc: datetime,
        symbol: str,
        blackout_minutes_before: int = 2,
        blackout_minutes_after: int = 2,
    ) -> bool:
        """
        True if check_time_utc falls within a Tier 1 news blackout window.
        Blackout = [event_time - before, event_time + after].
        """
        ...
