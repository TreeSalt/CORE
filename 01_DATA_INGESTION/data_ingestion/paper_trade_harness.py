"""Paper Trading Harness — simulates order execution for strategy validation."""
import uuid
import time
import logging

log = logging.getLogger(__name__)


class PaperTradeHarness:
    def __init__(self, initial_cash=100000.0, default_slippage_pct=0.1):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.default_slippage_pct = default_slippage_pct
        self.positions = {}
        self.orders = []

    def submit_order(self, symbol, side, qty, price, slippage_pct=None):
        if side not in ("buy", "sell"):
            raise ValueError(f"Invalid side: {side}")
        slip = slippage_pct if slippage_pct is not None else self.default_slippage_pct
        fill_price = price * (1 + slip / 100) if side == "buy" else price * (1 - slip / 100)
        order_id = str(uuid.uuid4())[:8]
        cost = fill_price * qty
        if side == "buy":
            if cost > self.cash:
                return {"order_id": order_id, "status": "REJECTED", "reason": "INSUFFICIENT_CASH", "fill_price": 0.0}
            self.cash -= cost
            pos = self.positions.get(symbol, {"qty": 0.0, "total_cost": 0.0})
            pos["total_cost"] += cost
            pos["qty"] += qty
            pos["avg_price"] = pos["total_cost"] / pos["qty"] if pos["qty"] > 0 else 0.0
            self.positions[symbol] = pos
        else:
            pos = self.positions.get(symbol)
            if not pos or pos["qty"] < qty:
                return {"order_id": order_id, "status": "REJECTED", "reason": "INSUFFICIENT_POSITION", "fill_price": 0.0}
            self.cash += cost
            pos["qty"] -= qty
            if pos["qty"] <= 0:
                del self.positions[symbol]
            else:
                pos["total_cost"] = pos["avg_price"] * pos["qty"]
        order = {"order_id": order_id, "status": "FILLED", "symbol": symbol, "side": side,
                 "qty": qty, "price": price, "fill_price": round(fill_price, 6), "timestamp": time.time()}
        self.orders.append(order)
        return order

    def get_position(self, symbol, current_price=None):
        pos = self.positions.get(symbol)
        if not pos:
            return {"qty": 0.0, "avg_price": 0.0, "unrealized_pnl": 0.0}
        unrealized = (current_price - pos["avg_price"]) * pos["qty"] if current_price else 0.0
        return {"qty": pos["qty"], "avg_price": round(pos["avg_price"], 6), "unrealized_pnl": round(unrealized, 6)}

    def get_portfolio(self, prices=None):
        positions_summary = {}
        position_value = 0.0
        for symbol, pos in self.positions.items():
            price = prices.get(symbol, pos["avg_price"]) if prices else pos["avg_price"]
            value = pos["qty"] * price
            position_value += value
            positions_summary[symbol] = {"qty": pos["qty"], "avg_price": pos["avg_price"], "market_value": round(value, 2)}
        return {"cash": round(self.cash, 2), "positions": positions_summary, "total_equity": round(self.cash + position_value, 2)}
