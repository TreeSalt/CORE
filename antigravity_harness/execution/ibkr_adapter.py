"""
antigravity_harness/execution/ibkr_adapter.py
============================================
Sovereign Execution Adapter for Interactive Brokers (Paper Only).
Implements strict ORDER_INTENT binding and deterministic forensics.
"""

import json
import os
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import asyncio

# Deferred imports for ib_insync to avoid event loop errors in static analysis
IB = None
Order = None
Trade = None
Contract = None
MarketOrder = None
LimitOrder = None
StopOrder = None

from antigravity_harness.execution.adapter_base import (
    ExecutionAdapter,
    AdapterCapabilities,
    OrderIntent,
    OrderAck,
    Fill,
    Position,
    OrderStatus,
    OrderSide,
    OrderType,
)

class IBKRAdapter(ExecutionAdapter):
    """
    Interactive Brokers adapter with paper-only enforcement and fiduciary audit trail.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1, is_paper: bool = True):
        self._host = host
        self._port = port
        self._client_id = client_id
        self._is_paper = is_paper
        self._ib = None
        self._audit_file = None
        
    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_server_side_brackets=True,
            supports_oco=True,
            supports_cancel_replace=True,
            supports_order_status_push=True,
            supports_real_time_bars=True,
            supports_historical_bars=True,
            supports_paper_mode=True
        )

    @property
    def is_paper(self) -> bool:
        return self._is_paper

    async def connect(self) -> None:
        """Connect to IB. Fail closed if IBKR library missing or live mode attempted incorrectly."""
        global IB, Order, Trade, Contract, MarketOrder, LimitOrder, StopOrder
        try:
            from ib_insync import IB as _IB, Order as _Order, Trade as _Trade, Contract as _Contract, MarketOrder as _MarketOrder, LimitOrder as _LimitOrder, StopOrder as _StopOrder
            IB, Order, Trade, Contract, MarketOrder, LimitOrder, StopOrder = _IB, _Order, _Trade, _Contract, _MarketOrder, _LimitOrder, _StopOrder
        except ImportError:
            raise RuntimeError("IBKR FATAL: ib_insync library not installed or failed to import.")
            
        if not self._is_paper:
            # UNCONDITIONAL REFUSAL OF LIVE TRADING IN THIS ADAPTER VERSION
            raise RuntimeError("IBKR FATAL: Live trading explicitly DISABLED in this version. Use Paper mode only.")
            
        try:
            self._ib = IB()
            await self._ib.connectAsync(self._host, self._port, clientId=self._client_id)
        except Exception as e:
            raise RuntimeError(f"IBKR CONNECTION FAILED: {e}")

    async def disconnect(self) -> None:
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()

    async def get_position(self, symbol: str) -> Position:
        positions = await self.get_all_positions()
        for p in positions:
            if p.symbol == symbol:
                return p
        return Position(symbol, 0, Decimal("0"), 0.0, 0.0)

    async def get_all_positions(self) -> List[Position]:
        if not self._ib: return []
        ib_pos = self._ib.positions()
        res = []
        for p in ib_pos:
            res.append(Position(
                symbol=p.contract.localSymbol or p.contract.symbol,
                quantity=int(p.position),
                average_cost=Decimal(str(p.avgCost)),
                unrealized_pnl_usd=0.0,
                realized_pnl_today_usd=0.0
            ))
        return res

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderAck]:
        if not self._ib: return []
        trades = self._ib.openTrades()
        res = []
        for t in trades:
            if symbol and (t.contract.localSymbol != symbol and t.contract.symbol != symbol):
                continue
            res.append(self._map_trade_to_ack(t))
        return res

    def _map_trade_to_ack(self, trade: Any) -> OrderAck:
        ib_status = trade.orderStatus.status
        status = OrderStatus.PENDING
        if ib_status == "Submitted": status = OrderStatus.SUBMITTED
        elif ib_status == "Filled": status = OrderStatus.FILLED
        elif ib_status == "Cancelled": status = OrderStatus.CANCELLED
        elif ib_status == "Inactive": status = OrderStatus.REJECTED
        
        return OrderAck(
            broker_order_id=str(trade.order.orderId),
            client_order_id=trade.order.orderRef,
            status=status,
            submitted_at_utc=datetime.utcnow(),
            broker_raw=trade.order.__dict__
        )

    async def submit_order(self, intent: OrderIntent) -> OrderAck:
        if not self._ib: raise RuntimeError("Broker not connected.")
        
        # 1. Cryptographic Binding
        intent_envelope = {
            "symbol": intent.symbol,
            "side": intent.side.value,
            "qty": intent.quantity,
            "type": intent.order_type.value,
            "lmt": str(intent.limit_price) if intent.limit_price else None,
            "stp": str(intent.stop_price) if intent.stop_price else None,
            "tif": intent.time_in_force.value,
            "cid": intent.client_order_id,
            "ts_utc": datetime.utcnow().isoformat(),
            "nonce": os.urandom(8).hex()
        }
        envelope_json = json.dumps(intent_envelope, sort_keys=True).encode("utf-8")
        intent_sha = hashlib.sha256(envelope_json).hexdigest()
        
        # 2. Map to IB Order
        contract = self._get_contract(intent.symbol)
        ib_order = None
        if intent.order_type == OrderType.MARKET:
            ib_order = MarketOrder(intent.side.value, intent.quantity)
        elif intent.order_type == OrderType.LIMIT:
            ib_order = LimitOrder(intent.side.value, intent.quantity, float(intent.limit_price))
        elif intent.order_type == OrderType.STOP:
            ib_order = StopOrder(intent.side.value, intent.quantity, float(intent.stop_price))
            
        if not ib_order:
            raise ValueError(f"Unsupported order type: {intent.order_type}")
            
        ib_order.orderRef = intent.client_order_id
        
        # 3. Submit
        trade = self._ib.placeOrder(contract, ib_order)
        
        # 4. Audit Log
        event = {
            "order_intent_sha256": intent_sha,
            "client_order_id": intent.client_order_id,
            "broker_order_id_sha256": hashlib.sha256(str(ib_order.orderId).encode()).hexdigest(),
            "submit_ts": datetime.utcnow().isoformat(),
            "status": "SUBMITTED"
        }
        self._log_audit_event(event)
        
        return self._map_trade_to_ack(trade)

    def _get_contract(self, symbol: str) -> Contract:
        if "/" in symbol:
            parts = symbol.split("/")
            return Contract(localSymbol=parts[0], lastTradeDateOrContractMonth=parts[1], secType="FUT", exchange="GLOBEX", currency="USD")
        return Contract(symbol=symbol, secType="STK", exchange="SMART", currency="USD")

    async def cancel_order(self, broker_order_id: str) -> bool:
        if not self._ib: return False
        for trade in self._ib.openTrades():
            if str(trade.order.orderId) == broker_order_id:
                self._ib.cancelOrder(trade.order)
                return True
        return False

    async def get_account_cash(self) -> float:
        if not self._ib: return 0.0
        tags = [t for t in self._ib.accountSummary() if t.tag == "AvailableFunds"]
        if tags:
            return float(tags[0].value)
        return 0.0

    async def get_realized_pnl_today(self) -> float:
        return 0.0

    def set_audit_path(self, path: str):
        self._audit_file = path

    def _log_audit_event(self, event: Dict[str, Any]):
        if not self._audit_file: return
        os.makedirs(os.path.dirname(self._audit_file), exist_ok=True)
        with open(self._audit_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _get_reality_gap_metrics(self) -> Dict[str, Any]:
        return {
            "median_slippage_bps": 0.0,
            "p95_slippage_bps": 0.0,
            "median_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "sample_count": 0
        }
