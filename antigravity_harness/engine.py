from __future__ import annotations

import contextlib
import ctypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import numpy as np
import pandas as pd

from antigravity_harness.config import EngineConfig, StrategyParams
from antigravity_harness.execution.adapter_base import Fill, OrderSide
from antigravity_harness.execution.fill_tape import FillTape

# Removed local dataclasses in favor of antigravity_harness.models
from antigravity_harness.execution.slippage import PhysicsViolationError  # noqa: F401
from antigravity_harness.instruments.base import InstrumentSpec
from antigravity_harness.instruments.mes import MES_SPEC
from antigravity_harness.metrics import compute_metrics
from antigravity_harness.models import BacktestResult, MetricSet, Trade
from antigravity_harness.phoenix import SovereignAuditor


def _apply_slippage(price: float, side: str, slippage_ticks: float, spec: InstrumentSpec = MES_SPEC) -> float:
    # MISSION v4.5.301: Friction Unlocked (Run Spec Truth)
    # Uses the configured slippage_ticks parameter instead of hardcoding 1 tick.
    # MISSION v4.5.382: Bind tick_size from spec to prevent Frankenstein Fills.
    tick_size = spec.tick_size
    # Enforce tick grid quantization
    quantized_price = round(price / tick_size) * tick_size

    if os.environ.get("TRADER_OPS_NO_SLIPPAGE") == "1":
        return float(quantized_price)

    # Dynamic friction: slippage_ticks * tick_size
    slip = slippage_ticks * tick_size
    fill_price = quantized_price + slip if side.lower() == "buy" else quantized_price - slip
    return float(fill_price)


class SimulatedAccount:
    """
    Manages state (Cash, Position, Equity) and execution logic.
    Decouples 'Physics' (Market Data) from 'Accounting' (PnL).
    """

    def __init__(self, initial_cash: float, symbol: str = "UNKNOWN", slippage: float = 0.0, slippage_ticks: Optional[float] = None, allow_fractional: bool = True,    fill_tape: Optional[FillTape] = None, # noqa: PLR0912, PLR0915
    spec: InstrumentSpec = MES_SPEC,
    sizing_multiplier: float = 1.0,
 use_kelly: bool = False, kelly_multiplier: float = 0.5, kelly_max_risk: float = 0.05, var_limit_pct: float = 0.0, var_confidence: float = 0.95, var_lookback: int = 30, use_alpha_decay: bool = False, decay_lookback_trades: int = 10, decay_threshold_win_rate: float = 0.4, decay_penalty_multiplier: float = 0.5, use_sentiment: bool = False, sentiment_threshold: float = 0.5, sentiment_sizing_multiplier: float = 1.25, use_cpp_mirror: bool = False, max_position_size_contracts: int = 1_000_000, max_trades_per_day: int = 1_000_000):  # noqa: PLR0913, PLR0915
        self.cash = float(initial_cash)
        self.symbol = symbol
        self.qty = 0  # MISSION v4.5.290: Integer quantity
        self.entry_price = 0.0
        self.entry_time: Optional[pd.Timestamp] = None
        # MISSION v4.5.306: Compatibility Map
        if slippage_ticks is None:
            self.slippage_ticks = slippage
        else:
            self.slippage_ticks = slippage_ticks
        self.allow_fractional = allow_fractional
        self.fill_tape = fill_tape
        self.spec = spec
        self.sizing_multiplier = sizing_multiplier
        self.use_kelly = use_kelly
        self.kelly_multiplier = kelly_multiplier
        self.kelly_max_risk = kelly_max_risk
        
        # Item 8: VaR Governor State
        self.var_limit_pct = var_limit_pct
        self.var_confidence = var_confidence
        self.var_lookback = var_lookback
        self.equity_history: List[float] = [float(initial_cash)]
        
        # Item 16: Alpha Decay State
        self.use_alpha_decay = use_alpha_decay
        self.decay_lookback_trades = decay_lookback_trades
        self.decay_threshold_win_rate = decay_threshold_win_rate
        self.decay_penalty_multiplier = decay_penalty_multiplier

        # Item 18: Sentiment-Weighted Alpha
        self.use_sentiment = use_sentiment
        self.sentiment_threshold = sentiment_threshold
        self.sentiment_sizing_multiplier = sentiment_sizing_multiplier
        
        # MISSION v4.5.306: Risk Enforcement State
        self.max_position_size_contracts = max_position_size_contracts
        self.max_trades_per_day = max_trades_per_day
        self.daily_trades_count = 0
        self.last_trade_date = None
        
        self.trades: List[Trade] = []

        # Item 21: C++ (C) Physics Mirror
        self._c_account = None
        if use_cpp_mirror or os.environ.get("TRADER_OPS_USE_CPP_MIRROR") == "1":
            try:
                lib_path = Path(__file__).parent / "physics" / "libphysics.so"
                if lib_path.exists():
                    self._lib = ctypes.CDLL(str(lib_path))
                    
                    # Setup Argument/Return Types
                    self._lib.Account_new.argtypes = [ctypes.c_double, ctypes.c_double]
                    self._lib.Account_new.restype = ctypes.c_void_p
                    
                    self._lib.Account_delete.argtypes = [ctypes.c_void_p]
                    self._lib.Account_delete.restype = None
                    
                    self._lib.Account_buy.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double]
                    self._lib.Account_buy.restype = ctypes.c_bool
                    
                    self._lib.Account_sell.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double]
                    self._lib.Account_sell.restype = ctypes.c_bool
                    
                    self._lib.Account_get_cash.argtypes = [ctypes.c_void_p]
                    self._lib.Account_get_cash.restype = ctypes.c_double
                    
                    self._lib.Account_get_qty.argtypes = [ctypes.c_void_p]
                    self._lib.Account_get_qty.restype = ctypes.c_double
                    
                    self._lib.Account_get_entry_price.argtypes = [ctypes.c_void_p]
                    self._lib.Account_get_entry_price.restype = ctypes.c_double
                    
                    self._c_account = self._lib.Account_new(float(initial_cash), float(slippage))
            except Exception as e:
                print(f"⚠️ Warning: Failed to load C Physics Mirror: {e}")

    def __del__(self):
        """Cleanup C memory."""
        if hasattr(self, "_c_account") and self._c_account and hasattr(self, "_lib"):
            with contextlib.suppress(BaseException):
                self._lib.Account_delete(self._c_account)

    @property
    def in_position(self) -> bool:
        return abs(self.qty) > 1e-9

    def total_value(self, current_price: float) -> float:
        # MISSION v4.5.382: Use multiplier from spec
        return self.cash + (float(self.qty) * float(current_price) * self.spec.multiplier)

    def _calculate_commission(self, price: float, qty: int, bps: float, fixed: float) -> float:  # noqa: PLR0913
        # MISSION v4.5.290: $0.85 per side per contract (Institutional Baseline)
        if os.environ.get("TRADER_OPS_FREE_FILLS") == "1":
            return 0.0
        
        # Priority: Fixed > Fractional > Baseline
        if fixed > 0:
            return fixed
        if bps > 0:
            # Baseline baseline physics uses multiplier from spec
            return price * qty * self.spec.multiplier * bps
            
        return (0.85 * qty)

    def buy(  # noqa: PLR0912, PLR0915
        self,
        price: float,
        timestamp: pd.Timestamp,
        stop_price: float = np.nan,
        risk_pct: float = 0.0,
        volume: float = np.inf,
        limit_pct: float = 0.0,
        comm_frac: float = 0.0,
        comm_bps: float = 0.0,
        comm_fixed: float = 0.0,
        current_sentiment: float = 0.0,
        qty: float = 0.0,  # Explicit quantity to buy (0.0 = use risk/cash logic)
        reason: str = "buy",
    ) -> bool:
        # Compatibility: comm_bps is legacy name; comm_frac is canonical (decimal fraction)
        if comm_frac == 0.0 and comm_bps != 0.0:
            comm_frac = float(comm_bps)

        # MISSION v4.5.290 Baseline: Multiplier from Spec
        multiplier = self.spec.multiplier
        
        fill_price = _apply_slippage(price, "buy", self.slippage_ticks, spec=self.spec)
        if fill_price <= 0:
            return False
        
        # 1. Default: Full Equity (Legacy) / Explicit Qty
        qty_to_buy = 0.0

        if qty > 0.0:
            qty_to_buy = float(qty)
        # 2. Risk-Based Sizing (Phase 6E+)
        elif risk_pct > 0.0 and not np.isnan(stop_price) and stop_price < fill_price:
            equity = self.total_value(fill_price)
            # Apply Sizing Multiplier (Autonomous Plateau Scaling)
            risk_amt = equity * risk_pct * self.sizing_multiplier

            # Item 7: Kelly Criterion Scaling
            if self.use_kelly:
                from antigravity_harness.metrics import kelly_fraction  # noqa: PLC0415
                k = kelly_fraction(self.trades) if self.trades else 0.0
                if k > 0:
                    kelly_risk = min(k * self.kelly_multiplier, self.kelly_max_risk)
                    risk_amt = equity * kelly_risk * self.sizing_multiplier

            # Item 8: VaR Governor Scaling
            if self.var_limit_pct > 0 and len(self.equity_history) >= 2:
                from antigravity_harness.metrics import calculate_var  # noqa: PLC0415
                hist_s = pd.Series(self.equity_history[-(self.var_lookback + 1):])
                current_var = calculate_var(hist_s, confidence=self.var_confidence)
                if current_var > self.var_limit_pct:
                    scaling_factor = self.var_limit_pct / current_var
                    risk_amt *= scaling_factor
                    
            # Item 16: Alpha Decay Scaling
            if self.use_alpha_decay and len(self.trades) >= self.decay_lookback_trades:
                recent_trades = self.trades[-self.decay_lookback_trades:]
                wins = sum(1 for t in recent_trades if t.pnl_abs > 0)
                win_rate = wins / self.decay_lookback_trades
                if win_rate < self.decay_threshold_win_rate:
                    risk_amt *= self.decay_penalty_multiplier
                    
            # Item 18: Sentiment Scaling
            if self.use_sentiment and current_sentiment != 0.0:
                if current_sentiment >= self.sentiment_threshold:
                    risk_amt *= self.sentiment_sizing_multiplier
                elif current_sentiment <= -self.sentiment_threshold:
                    risk_amt *= (1.0 / self.sentiment_sizing_multiplier)

            unit_comm = 0.85 if (comm_frac == 0 and comm_fixed == 0) else 0.0
            if comm_frac > 0:
                unit_comm = fill_price * comm_frac * multiplier
            
            available_cash = self.cash - comm_fixed if comm_fixed > 0 else self.cash
            risk_per_share = (fill_price - stop_price) * multiplier 
            if risk_per_share > 0:
                qty_risk = risk_amt / risk_per_share
                max_qty_cash = available_cash / (fill_price * multiplier + unit_comm)
                qty_to_buy = min(qty_risk, max_qty_cash)
            else:
                qty_to_buy = available_cash / (fill_price * multiplier + unit_comm)
        else:
            # Full Cash
            unit_comm = 0.85 if (comm_frac == 0 and comm_fixed == 0) else 0.0
            if comm_frac > 0:
                unit_comm = fill_price * comm_frac * multiplier
            available_cash = self.cash - comm_fixed if comm_fixed > 0 else self.cash
            qty_to_buy = available_cash / (fill_price * multiplier + unit_comm)

        # 2.5 MISSION v4.5.306: Risk Enforcement
        # Reset count on date change
        if self.last_trade_date is None or timestamp.date() > self.last_trade_date:
            self.daily_trades_count = 0
            self.last_trade_date = timestamp.date()

        # Check explicit qty first if passed
        if qty > 0.0:
            qty_to_buy = float(qty)

        # Daily Trade Limit (New Risk Only)
        is_new_risk = (self.qty >= 0) or (self.qty < 0 and (self.qty + qty_to_buy) > 0)
        if is_new_risk and self.daily_trades_count >= self.max_trades_per_day:
            return False

        # Max Position Size
        if self.qty >= 0:
            # Long side
            if (self.qty + qty_to_buy) > self.max_position_size_contracts:
                qty_to_buy = max(0, self.max_position_size_contracts - self.qty)
        else:
            # Covering Short (Buy to Cover)
            remaining_to_flatten = abs(self.qty)
            if qty_to_buy > remaining_to_flatten:
                over_flatten = qty_to_buy - remaining_to_flatten
                over_flatten = min(over_flatten, float(self.max_position_size_contracts))
                qty_to_buy = remaining_to_flatten + over_flatten

        # 3. Volume Check
        if limit_pct > 0.0 and volume > 0:
            max_vol_qty = volume * limit_pct
            qty_to_buy = min(qty_to_buy, max_vol_qty)

        if not self.allow_fractional:
            # MISSION v4.5.332: Integer lot enforcement — floor to whole contracts
            qty_to_buy = int(qty_to_buy)

        if qty_to_buy > 0:
            gross_cost = qty_to_buy * fill_price * multiplier # MISSION v4.5.290: Multiplier
            commission = self._calculate_commission(fill_price, qty_to_buy, comm_frac, comm_fixed)
            total_cost = gross_cost + commission

            # If covering a short, we still pay cash to buy the contract back
            if total_cost > self.cash:
                # Resize for commission if cash constrained
                if self.cash > comm_fixed:
                    eff_unit_comm = 0.0
                    if comm_frac > 0:
                        eff_unit_comm = fill_price * multiplier * comm_frac
                    elif comm_fixed == 0:
                        eff_unit_comm = 0.85
                        
                    eff_price = fill_price * multiplier + eff_unit_comm
                    qty_to_buy = (self.cash - comm_fixed) / eff_price

                    if not self.allow_fractional:
                        qty_to_buy = int(qty_to_buy)
                    if qty_to_buy <= 0:
                        return False

                    gross_cost = qty_to_buy * fill_price * multiplier 
                    commission = self._calculate_commission(fill_price, qty_to_buy, comm_frac, comm_fixed)
                    total_cost = gross_cost + commission
                else:
                    return False

            # ACTION: Record trade PnL if this BUY is covering a SHORT
            if self.qty < 0:
                # BTC (Buy to Cover)
                qty_covered = min(qty_to_buy, abs(self.qty))
                pnl_abs = (self.entry_price - fill_price) * qty_covered * multiplier - commission
                cost_basis = qty_covered * self.entry_price * multiplier
                pnl_pct = (pnl_abs / cost_basis) if cost_basis > 0 else 0.0

                self.trades.append(
                    Trade(
                        entry_time=cast(pd.Timestamp, self.entry_time if self.entry_time is not None else timestamp),
                        exit_time=timestamp,
                        entry_price=float(self.entry_price),
                        exit_price=float(fill_price),
                        qty=float(qty_covered),
                        pnl_abs=float(pnl_abs),
                        pnl_pct=float(pnl_pct),
                        exit_reason=reason,
                    )
                )

            self.cash -= total_cost

            # Increment trade count if new long or flip
            if is_new_risk:
                self.daily_trades_count += 1

            # Weighted Average Entry Price (Points)
            if self.qty > 0:
                current_val = self.qty * self.entry_price * multiplier 
                new_val = qty_to_buy * fill_price * multiplier
                self.entry_price = (current_val + new_val) / ((self.qty + qty_to_buy) * multiplier)
            elif self.qty < 0:
                # BTC logic: if we don't flip to long, entry_price stays same (or reset if closed)
                if (self.qty + qty_to_buy) > 1e-9:
                    # Flipped to Long
                    self.entry_price = fill_price
                    self.entry_time = timestamp
                elif abs(self.qty + qty_to_buy) < 1e-9:
                    # Full close
                    self.entry_price = 0.0
                    self.entry_time = None
                else:
                    # Still short, entry_price (avg short price) remains same
                    pass
            else:
                # New Long
                self.entry_price = fill_price
                self.entry_time = timestamp

            self.qty += qty_to_buy
            
            # Record in FillTape
            if self.fill_tape:
                # Use BUY for long entries and covers (Buy to Cover)
                fill_side = OrderSide.BUY
                fill = Fill(
                    broker_order_id=f"sim-{timestamp.isoformat()}",
                    client_order_id=f"sim-{timestamp.isoformat()}",
                    symbol=self.spec.symbol, 
                    side=fill_side,
                    filled_qty=qty_to_buy,
                    fill_price=fill_price,
                    fill_time_utc=timestamp.to_pydatetime(),
                    commission_usd=commission
                )
                self.fill_tape.record(fill, expected_price=price, spec=self.spec)

            return True
        return False

    def sell(
        self,
        price: float,
        timestamp: pd.Timestamp,
        reason: str,
        volume: float = np.inf,
        limit_pct: float = 0.0,
        comm_frac: float = 0.0,
        comm_bps: float = 0.0,
        comm_fixed: float = 0.0,
        qty: float = 0.0,  # Explicit quantity to sell (0.0 = All)
    ) -> bool:
        if comm_frac == 0.0 and comm_bps != 0.0:
            comm_frac = float(comm_bps)

        if self.qty <= 0:
            return self._sell_to_open(price, timestamp, reason, qty, comm_frac, comm_fixed)

        return self._sell_to_close(price, timestamp, reason, volume, limit_pct, comm_frac, comm_fixed, qty)

    def _sell_to_open(self, price: float, timestamp: pd.Timestamp, reason: str, qty: float, comm_frac: float, comm_fixed: float) -> bool:
        if qty <= 0.0:
            return False

        # MISSION v4.5.422: Cash Account Shorting Gate (Physical Layer)
        # We need access to account_type. We'll check the spec or an env var fallback.
        # But safer is to check if it's even allowed.
        # For now, we'll assume SimulatedAccount is initialized with knowledge of its profile.
        # If multiplier exists but we are on a cash profile, block.
        if os.environ.get("TRADER_OPS_ACCOUNT_TYPE") == "cash":
            print(f"⛔ PHYSICAL VIOLATION: Attempted to sell-to-open {self.symbol} on CASH account.")
            return False

        # --- MISSION v4.5.306: Risk Enforcement ---
        if self.last_trade_date is None or timestamp.date() > self.last_trade_date:
            self.daily_trades_count = 0
            self.last_trade_date = timestamp.date()

        if self.daily_trades_count >= self.max_trades_per_day:
            return False

        qty_to_sell = float(qty)
        # Max Position Size
        if abs(self.qty - qty_to_sell) > self.max_position_size_contracts:
            qty_to_sell = max(0, self.max_position_size_contracts - abs(self.qty))

        if not self.allow_fractional:
            # MISSION v4.5.332: Integer lot enforcement — floor to whole contracts
            qty_to_sell = int(qty_to_sell)
        
        if qty_to_sell <= 0:
            return False

        multiplier = 5.0 if "MES" in self.symbol else 1.0
        fill_price = _apply_slippage(price, "sell", self.slippage_ticks)
        gross_proceeds = qty_to_sell * fill_price * multiplier
        commission = self._calculate_commission(fill_price, qty_to_sell, comm_frac, comm_fixed)
        
        self.cash += (gross_proceeds - commission)
        
        if self.qty < 0:
            current_val = abs(self.qty) * self.entry_price * multiplier
            new_val = qty_to_sell * fill_price * multiplier
            self.entry_price = (current_val + new_val) / ((abs(self.qty) + qty_to_sell) * multiplier)
        else:
            self.entry_price = fill_price
            self.entry_time = timestamp
        
        self.qty -= qty_to_sell
        self.daily_trades_count += 1
        self._record_fill(timestamp, OrderSide.SELL, qty_to_sell, fill_price, commission, price)
        return True

    def _sell_to_close(self, price: float, timestamp: pd.Timestamp, reason: str, volume: float, limit_pct: float, comm_frac: float, comm_fixed: float, qty: float) -> bool:
        target_qty = self.qty if qty <= 0.0 else min(qty, self.qty)
        qty_to_sell = target_qty
        if limit_pct > 0.0 and volume > 0:
            qty_to_sell = min(target_qty, volume * limit_pct)

        if qty_to_sell <= 0:
            return False
        
        # MISSION v4.5.306: Reset daily count even on close
        if self.last_trade_date is None or timestamp.date() > self.last_trade_date:
            self.daily_trades_count = 0
            self.last_trade_date = timestamp.date()

        if not self.allow_fractional:
            # MISSION v4.5.332: Integer lot enforcement — floor to whole contracts
            qty_to_sell = int(qty_to_sell)

        fill_price = _apply_slippage(price, "sell", self.slippage_ticks, spec=self.spec)
        multiplier = self.spec.multiplier
        gross_proceeds = qty_to_sell * fill_price * multiplier
        commission = self._calculate_commission(fill_price, qty_to_sell, comm_frac, comm_fixed)
        net_proceeds = gross_proceeds - commission

        self.cash += net_proceeds
        self.qty -= qty_to_sell 

        self._record_fill(timestamp, OrderSide.SELL, qty_to_sell, fill_price, commission, price)

        pnl_abs = net_proceeds - (qty_to_sell * self.entry_price * multiplier)
        cost_basis = qty_to_sell * self.entry_price * multiplier
        pnl_pct = (pnl_abs / cost_basis) if cost_basis > 0 else 0.0

        assert self.entry_time is not None, "Trade exit without entry time"
        
        # MISSION v4.5.291: Audit trail for gap_stops
        final_reason = reason if self.qty <= 0 else f"{reason}_partial"
        
        self.trades.append(
            Trade(
                entry_time=cast(pd.Timestamp, self.entry_time if self.entry_time is not None else timestamp),
                exit_time=timestamp,
                entry_price=float(self.entry_price),
                exit_price=float(fill_price),
                qty=float(qty_to_sell),
                pnl_abs=float(pnl_abs),
                pnl_pct=float(pnl_pct),
                exit_reason=final_reason,
            )
        )

        if abs(self.qty) < 1e-9:
            self.qty = 0.0
            self.entry_price = 0.0
            self.entry_time = None

        return True

    def _record_fill(self, timestamp: pd.Timestamp, side: OrderSide, qty: float, fill_price: float, commission: float, expected_price: float):
        if self.fill_tape:
            fill = Fill(
                broker_order_id=f"sim-{timestamp.isoformat()}",
                client_order_id=f"sim-{timestamp.isoformat()}",
                symbol=self.spec.symbol, 
                side=side,
                filled_qty=qty,
                fill_price=fill_price,
                fill_time_utc=timestamp.to_pydatetime(),
                commission_usd=commission
            )
            self.fill_tape.record(fill, expected_price=expected_price, spec=self.spec)


def run_backtest(  # noqa: PLR0912, PLR0915
    df: pd.DataFrame,
    prepared: pd.DataFrame,
    params: StrategyParams,
    engine_cfg: EngineConfig,
    debug: bool = False,
    out_dir: Optional[Path] = None,
    intelligence: Optional[Dict[str, Any]] = None,
) -> BacktestResult:
    """
    Fortress Protocol v2.1.0 - Optimized Physics Engine
    Uses Numpy arrays for core loop speedup (~50x).
    Uses SimulatedAccount for state management.
    """
    np.random.seed(engine_cfg.seed)

    # 1. Prepare Data
    # Avoid copying main DF, access numpy views directly

    # Align Signals (Fast Path)
    sig = prepared if prepared.index.equals(df.index) else prepared.reindex(df.index)


    # Ensure all required signals exist (for backward compatibility with long-only tests)
    for col in ["short_entry_signal", "short_exit_signal"]:
        if col not in sig.columns:
            sig[col] = False

    # Warmup Validation
    required = ["entry_signal", "exit_signal", "short_entry_signal", "short_exit_signal"]
    if not params.disable_stop:
        required.append("ATR")

    # Quick check using numpy to avoid excessive pandas overhead
    # But for safety/readability we keep pandas check for now, it's once per run.
    valid_mask = sig[required].notna().all(axis=1)
    if not valid_mask.any():
        equity = pd.Series(engine_cfg.initial_cash, index=df.index, dtype=float)
        m_dict = compute_metrics(equity, [], periods_per_year=engine_cfg.periods_per_year)
        metrics = MetricSet(**m_dict)
        return BacktestResult(
            equity_curve=equity,
            trades=[],
            metrics=metrics,
            config={"engine": engine_cfg.model_dump(), "params": params.model_dump()},
        )

    first_valid_idx = int(np.argmax(valid_mask.values))
    start_ix = min(first_valid_idx + int(engine_cfg.warmup_extra_bars), len(sig) - 1)

    # 2. Signal Shift (Vectorized)
    # i is execution time. Signal comes from i-1.
    # Gold-Tier Explicit Conversion: uses nullable boolean dtype for safe NA handling
    # and then converts to numpy booleans with False as the default for NAs.
    entry_raw = sig["entry_signal"].astype("boolean").to_numpy(dtype=bool, na_value=False)
    exit_raw = sig["exit_signal"].astype("boolean").to_numpy(dtype=bool, na_value=False)
    short_entry_raw = sig["short_entry_signal"].astype("boolean").to_numpy(dtype=bool, na_value=False)
    short_exit_raw = sig["short_exit_signal"].astype("boolean").to_numpy(dtype=bool, na_value=False)

    # We execute at `i` based on signal at `i-1`.
    entry_sig = np.concatenate(([False], entry_raw[:-1]))
    exit_sig = np.concatenate(([False], exit_raw[:-1]))
    short_entry_sig = np.concatenate(([False], short_entry_raw[:-1]))
    short_exit_sig = np.concatenate(([False], short_exit_raw[:-1]))

    atr_shifted: Optional[np.ndarray] = None
    if not params.disable_stop:
        atr_raw = sig["ATR"].values
        atr_shifted = np.concatenate(([np.nan], atr_raw[:-1]))

    # Item 10: Regime Pre-calculation
    from antigravity_harness.regimes import (  # noqa: PLC0415
        RegimeConfig,
        RegimeLabel,
        compute_regime_indicators,
        infer_regimes_from_metrics,
    )
    regime_cfg = RegimeConfig()
    regime_metrics = compute_regime_indicators(df[["Close"]], regime_cfg)
    regime_states = infer_regimes_from_metrics(regime_metrics, regime_cfg)
    regime_labels = [s.label for s in regime_states]
    
    # Map regimes to multipliers
    multiplier_map = {
        RegimeLabel.TREND_LOW_VOL: params.stop_mult_trend_low_vol,
        RegimeLabel.TREND_HIGH_VOL: params.stop_mult_trend_high_vol,
        RegimeLabel.RANGE_LOW_VOL: params.stop_mult_range_low_vol,
        RegimeLabel.RANGE_HIGH_VOL: params.stop_mult_range_high_vol,
        RegimeLabel.PANIC: params.stop_mult_panic,
        RegimeLabel.UNKNOWN: 1.0,
    }
    regime_multipliers = np.array([multiplier_map.get(lbl, 1.0) for lbl in regime_labels])

    # 3. Numpy Conversion for Speed
    opens = df["Open"].values.astype(float)
    _highs = df["High"].values.astype(float)
    lows = df["Low"].values.astype(float)
    closes = df["Close"].values.astype(float)
    volumes = df["Volume"].values.astype(float)
    timestamps = df.index

    # Intelligence Extraction (Item 18)
    sentiment_arr = np.zeros(len(df), dtype=float)
    if params.use_sentiment and intelligence and "sentiment" in intelligence:
        intel_sentiment = intelligence["sentiment"]
        if isinstance(intel_sentiment, pd.Series):
            # Align to our master index and forward fill gaps
            aligned = intel_sentiment.reindex(df.index).ffill().fillna(0.0)
            sentiment_arr = aligned.values.astype(float)
        elif isinstance(intel_sentiment, np.ndarray) and len(intel_sentiment) == len(df):
            sentiment_arr = intel_sentiment

    n_bars = len(df)
    equity_arr = np.full(n_bars, np.nan)
    cash_arr = np.full(n_bars, np.nan)
    qty_arr = np.full(n_bars, np.nan)
    in_pos_arr = np.zeros(n_bars, dtype=bool)
    stop_arr = np.full(n_bars, np.nan)

    # 4. Account Setup
    # MISSION v4.5.382: Bind spec and expected_symbols (Patch B)
    # For engine.py, we assume a single instrument run unless specified.
    # Fallback to dynamic symbol spec if not provided to avoid breaking generic tests.
    if hasattr(params, "spec") and params.spec:
        spec = params.spec
    else:
        # Infer symbol from df if possible
        inferred_sym = getattr(df, "name", "GENERIC")
        from antigravity_harness.instruments.base import InstrumentSpec  # noqa: PLC0415
        spec = InstrumentSpec(
            symbol=str(inferred_sym),
            asset_class="generic",
            tick_size=0.01,
            multiplier=1.0,
            lot_size=1.0
        )

    # 4. Account Setup
    # Initialize FillTape if in Release Mode
    tape: Optional[FillTape] = None
    if os.environ.get("METADATA_RELEASE_MODE") == "1":
        if out_dir is None:
            out_dir = Path(os.getcwd()) / "reports/fills"
        
        # Try to infer session date from df
        session_date = df.index[-1].strftime("%Y-%m-%d") if not df.empty else "unknown"
        
        tape = FillTape(
            output_dir=out_dir, 
            session_date=session_date, 
            spec=spec,
            expected_symbols=getattr(params, "symbols", [spec.symbol])
        )

    account = SimulatedAccount(
        initial_cash=engine_cfg.initial_cash,
        slippage_ticks=engine_cfg.slippage_ticks,
        allow_fractional=engine_cfg.allow_fractional_shares,
        fill_tape=tape,
        spec=spec, # Match tape spec
        sizing_multiplier=params.sizing_multiplier,
        use_kelly=params.use_kelly,
        kelly_multiplier=params.kelly_multiplier,
        kelly_max_risk=params.kelly_max_risk,
        var_limit_pct=params.var_limit_pct,
        var_confidence=params.var_confidence,
        var_lookback=params.var_lookback,
        use_alpha_decay=params.use_alpha_decay,
        decay_lookback_trades=params.decay_lookback_trades,
        decay_threshold_win_rate=params.decay_threshold_win_rate,
        decay_penalty_multiplier=params.decay_penalty_multiplier,
        use_sentiment=params.use_sentiment,
        sentiment_threshold=params.sentiment_threshold,
        sentiment_sizing_multiplier=params.sentiment_sizing_multiplier,
    )

    # Boot the Phoenix Protocol Auditor
    repo_root = Path(os.getcwd())
    auditor = SovereignAuditor(repo_root, account_id="Institutional-Gold-Account", debug_mode=debug)
    auditor.boot_audit(account.cash, account.qty)

    # State Vars
    bars_held = 0
    bars_since_exit = 999999
    stop_price = np.nan

    # -------------------------------------------------------------------------
    # OPTIMIZED SIMULATION LOOP
    # -------------------------------------------------------------------------

    for i in range(n_bars):
        # Warmup check
        if i < start_ix:
            equity_arr[i] = account.cash
            cash_arr[i] = account.cash
            qty_arr[i] = account.qty
            in_pos_arr[i] = account.in_position
            stop_arr[i] = stop_price
            continue

        current_ts = timestamps[i]
        o = opens[i]
        low = lows[i]
        c = closes[i]


        # Counters
        if account.in_position:
            bars_held += 1
            bars_since_exit = 0
        else:
            bars_held = 0
            bars_since_exit += 1

        # 1. Execute Scheduled Orders
        executed_exit = False

        # T-1 Volume for at-open execution (no lookahead)
        v_limit_ref = volumes[i-1] if i > 0 else 0.0

        # --- A. EXIT LOGIC ---
        if account.qty > 0 and (bars_held > params.min_hold_bars) and exit_sig[i]:
            # Close Long
            if account.sell(
                o,
                current_ts,
                "signal_exit",
                volume=v_limit_ref,
                limit_pct=engine_cfg.volume_limit_pct,
                comm_frac=engine_cfg.commission_rate_frac,
                comm_fixed=engine_cfg.commission_fixed,
            ) and not account.in_position:
                    auditor.log_decision(i, current_ts, "FULL_EXIT", {"reason": "signal_exit", "price": o})
                    bars_since_exit = 0
                    executed_exit = True
                    stop_price = np.nan
        
        elif account.qty < 0 and (bars_held > params.min_hold_bars) and short_exit_sig[i]:
            # Close Short (Buy back)
            # SimulatedAccount.buy handles BTC when qty < 0
            # We need to pass explicit qty if we want to close full short
            short_qty = abs(account.qty)
            if account.buy(
                o,
                current_ts,
                qty=short_qty,
                volume=v_limit_ref,
                limit_pct=engine_cfg.volume_limit_pct,
                comm_frac=engine_cfg.commission_rate_frac,
                comm_fixed=engine_cfg.commission_fixed,
                reason="short_signal_exit",
            ) and not account.in_position:
                    auditor.log_decision(i, current_ts, "FULL_SHORT_EXIT", {"reason": "short_signal_exit", "price": o})
                    bars_since_exit = 0
                    executed_exit = True
                    stop_price = np.nan

        # --- B. ENTRY LOGIC ---
        if not account.in_position and not executed_exit and (bars_since_exit >= params.cooldown_bars):
            if entry_sig[i]:
                # Long Entry
                proposed_stop = np.nan
                if not params.disable_stop:
                    atr_ref = atr_shifted[i] if atr_shifted is not None else 0.0
                    if np.isfinite(atr_ref) and atr_ref > 0:
                        multiplier = regime_multipliers[i]
                        stop_dist = float(params.stop_atr) * atr_ref * multiplier
                        proposed_stop = o - stop_dist
                
                proposed_vol = min(v_limit_ref, v_limit_ref * engine_cfg.volume_limit_pct)
                
                # MISSION v4.5.306: Provide a realistic qty estimate to the Auditor
                equity_ref = account.total_value(o)
                risk_amt_ref = equity_ref * params.risk_per_trade * account.sizing_multiplier
                risk_per_share_ref = abs(o - proposed_stop) * 5.0 if not np.isnan(proposed_stop) else (o * 0.02 * 5.0)
                est_qty = risk_amt_ref / risk_per_share_ref if risk_per_share_ref > 0 else 0
                est_qty = min(est_qty, proposed_vol)

                if auditor.check_invariants(account, est_qty, o) and account.buy(
                    o,
                    current_ts,
                    stop_price=proposed_stop,
                    risk_pct=params.risk_per_trade,
                    volume=v_limit_ref,
                    limit_pct=engine_cfg.volume_limit_pct,
                    comm_frac=engine_cfg.commission_rate_frac,
                    comm_fixed=engine_cfg.commission_fixed,
                    current_sentiment=sentiment_arr[i],
                ):
                        auditor.log_decision(i, current_ts, "LONG_ENTRY", {"price": o, "stop": proposed_stop})
                        bars_held = 1
                        stop_price = proposed_stop
            
            elif short_entry_sig[i]:
                # Short Entry
                proposed_stop = np.nan
                if not params.disable_stop:
                    atr_ref = atr_shifted[i] if atr_shifted is not None else 0.0
                    if np.isfinite(atr_ref) and atr_ref > 0:
                        multiplier = regime_multipliers[i]
                        stop_dist = float(params.stop_atr) * atr_ref * multiplier
                        proposed_stop = o + stop_dist # Stop is ABOVE for shorts
                
                # For Shorts, we use the same risk-based sizing logic? 
                # account.sell() doesn't have it, so we calculate qty here.
                equity = account.total_value(o)
                risk_amt = equity * params.risk_per_trade * account.sizing_multiplier
                risk_per_share = abs(proposed_stop - o) * 5.0 if not np.isnan(proposed_stop) else (o * 0.02 * 5.0) 
                qty_to_short = risk_amt / risk_per_share
                
                if not engine_cfg.allow_fractional_shares:
                    qty_to_short = int(qty_to_short)
                
                if qty_to_short > 0 and account.sell(
                    o,
                    current_ts,
                    "short_entry",
                    qty=qty_to_short,
                    volume=v_limit_ref,
                    limit_pct=engine_cfg.volume_limit_pct,
                    comm_frac=engine_cfg.commission_rate_frac,
                    comm_fixed=engine_cfg.commission_fixed,
                ):
                    auditor.log_decision(i, current_ts, "SHORT_ENTRY", {"price": o, "stop": proposed_stop})
                    bars_held = 1
                    stop_price = proposed_stop

        # 3. Intrabar Risk (Stop Loss)
        if account.in_position and not np.isnan(stop_price):
            hit = False
            if account.qty > 0 and low <= stop_price:
                hit = True
                exec_p = min(o, stop_price) # Gap down or touch
            elif account.qty < 0 and _highs[i] >= stop_price:
                hit = True
                exec_p = max(o, stop_price) # Gap up or touch
            
            if hit:
                # MISSION v4.5.291: Determine if it was a GAP stop for audit fidelity
                reason = "stop"
                if (account.qty > 0 and exec_p < stop_price) or (account.qty < 0 and exec_p > stop_price):
                    reason = "gap_stop"

                if account.qty > 0:
                    account.sell(exec_p, current_ts, reason)
                else:
                    account.buy(exec_p, current_ts, qty=abs(account.qty), reason=reason)
                
                auditor.log_decision(i, current_ts, "STOP_LOSS", {"type": "intraday", "exec_price": exec_p, "stop": stop_price, "reason": reason})
                stop_price = np.nan

        # 4. Mark to Market
        equity_arr[i] = account.total_value(c)
        account.equity_history.append(equity_arr[i])
        cash_arr[i] = account.cash
        qty_arr[i] = account.qty
        in_pos_arr[i] = account.in_position
        stop_arr[i] = stop_price

    # 6. Force Close
    if account.in_position:
        last_price = closes[-1]
        # Force close uses T-0 volume because it's the end of the state, but typically it shouldn't matter.
        # For simplicity we use the last known volume.
        account.sell(
            last_price,
            timestamps[-1],
            "force_close",
            volume=volumes[-1],
            comm_frac=engine_cfg.commission_rate_frac,
            comm_fixed=engine_cfg.commission_fixed,
        )
        auditor.log_decision(len(closes) - 1, timestamps[-1], "FORCE_CLOSE", {"price": last_price})
        equity_arr[-1] = account.total_value(last_price)  # Reflect cash

    # Cleanup
    # Cleanup - Fix FutureWarning: Explicit cast to avoid downcasting warning
    equity_series = pd.Series(equity_arr, index=timestamps).ffill().fillna(float(engine_cfg.initial_cash)).astype(float)
    m_dict = compute_metrics(equity_series, account.trades, periods_per_year=engine_cfg.periods_per_year)
    
    # 7. Trace Production
    trace = pd.DataFrame(
        {
            "time": timestamps,
            "open": opens,
            "high": _highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
            "entry_signal_exec": entry_sig,
            "exit_signal_exec": exit_sig,
            "in_position": in_pos_arr,
            "qty": qty_arr,
            "cash": cash_arr,
            "equity": equity_series.values,
            "stop_price": stop_arr,
        }
    )
    if "regime" in sig.columns:
        trace["regime"] = sig["regime"].values
    if "confirmed_regime" in sig.columns:
        trace["confirmed_regime"] = sig["confirmed_regime"].values

    # Pass all metrics to constructor
    m_dict["raw_entry_signals"] = int(np.sum(entry_raw))
    m_dict["raw_exit_signals"] = int(np.sum(exit_raw))
    m_dict["raw_short_entry_signals"] = int(np.sum(short_entry_raw))
    m_dict["raw_short_exit_signals"] = int(np.sum(short_exit_raw))
    metrics = MetricSet(**m_dict)

    # Emit Fiduciary Audit Report (Phoenix Protocol)
    auditor.emit_audit_report(account)

    # Close FillTape
    if tape:
        tape_path = tape.close()
        # MISSION v4.5.339: Evidence Completeness — FillTape MUST exist with
        # headers even on 0 fills so the auditor always finds the artifact.
        if not tape_path.exists() or tape_path.stat().st_size == 0:
            import csv as _csv  # noqa: PLC0415

            from antigravity_harness.execution.fill_tape import FillRecord  # noqa: PLC0415
            fieldnames = list(FillRecord.__dataclass_fields__.keys())
            tape_path.parent.mkdir(parents=True, exist_ok=True)
            with open(tape_path, "w", newline="") as _f:
                writer = _csv.DictWriter(_f, fieldnames=fieldnames)
                writer.writeheader()
            print(f"📊 Forensic FillTape (headers-only, 0 fills): {tape_path.name}")
        else:
            print(f"📊 Forensic FillTape Saved: {tape_path.name}")

    return BacktestResult(
        equity_curve=equity_series,
        trades=account.trades,
        metrics=metrics,
        config={"engine": engine_cfg.model_dump(), "params": params.model_dump()},
        trace=trace,
    )
