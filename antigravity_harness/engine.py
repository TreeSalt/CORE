from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast

import os

import numpy as np
import pandas as pd

from antigravity_harness.config import EngineConfig, StrategyParams
from antigravity_harness.metrics import compute_metrics
from antigravity_harness.phoenix import SovereignAuditor
from pathlib import Path


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    exit_price: float
    qty: float
    pnl_abs: float
    pnl_pct: float
    exit_reason: str


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: List[Trade]
    metrics: Dict[str, Any]
    config: Dict[str, Any]
    trace: pd.DataFrame = field(default_factory=pd.DataFrame)


def _apply_slippage(price: float, side: str, slippage: float) -> float:
    if side == "buy":
        return price * (1.0 + slippage)
    if side == "sell":
        return price * (1.0 - slippage)
    raise ValueError(f"Unknown side: {side}")


class SimulatedAccount:
    """
    Manages state (Cash, Position, Equity) and execution logic.
    Decouples 'Physics' (Market Data) from 'Accounting' (PnL).
    """

    def __init__(self, initial_cash: float, slippage: float, allow_fractional: bool):
        self.cash = float(initial_cash)
        self.qty = 0.0
        self.entry_price = 0.0
        self.entry_time: Optional[pd.Timestamp] = None
        self.slippage = slippage
        self.allow_fractional = allow_fractional
        self.trades: List[Trade] = []

    @property
    def in_position(self) -> bool:
        return self.qty > 0

    def total_value(self, current_price: float) -> float:
        return self.cash + (self.qty * current_price)

    def _calculate_commission(self, price: float, qty: float, bps: float, fixed: float) -> float:
        return (price * qty * bps) + fixed

    def buy(  # noqa: PLR0912
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
    ) -> bool:
        # Compatibility: comm_bps is legacy name; comm_frac is canonical (decimal fraction)
        if comm_frac == 0.0 and comm_bps != 0.0:
            comm_frac = float(comm_bps)

        fill_price = _apply_slippage(price, "buy", self.slippage)
        if fill_price <= 0:
            return False

        # Allocation Logic
        # 1. Default: Full Equity (Legacy)
        qty_to_buy = 0.0

        # 2. Risk-Based Sizing (Phase 6E+)
        if risk_pct > 0.0 and not np.isnan(stop_price) and stop_price < fill_price:
            equity = self.total_value(fill_price)
            risk_amt = equity * risk_pct
            risk_per_share = fill_price - stop_price
            if risk_per_share > 0:
                qty_risk = risk_amt / risk_per_share
                # Cap at Cash (No Leverage in v3.5)
                max_qty_cash = self.cash / fill_price
                qty_to_buy = min(qty_risk, max_qty_cash)
            else:
                qty_to_buy = self.cash / fill_price
        else:
            # Full Cash
            qty_to_buy = self.cash / fill_price

        # 3. Volume Check
        if limit_pct > 0.0 and volume > 0:
            max_vol_qty = volume * limit_pct
            qty_to_buy = min(qty_to_buy, max_vol_qty)

        if not self.allow_fractional:
            qty_to_buy = int(qty_to_buy)

        if qty_to_buy > 0:
            gross_cost = qty_to_buy * fill_price
            commission = self._calculate_commission(fill_price, qty_to_buy, comm_frac, comm_fixed)
            total_cost = gross_cost + commission

            if total_cost > self.cash:
                # Resize for commission if cash constrained
                # Cost = Q * P * (1 + bps) + fixed
                # Q = (Cash - fixed) / (P * (1 + bps))
                if self.cash > comm_fixed:
                    qty_to_buy = (self.cash - comm_fixed) / (fill_price * (1 + comm_frac))

                    if not self.allow_fractional:
                        qty_to_buy = int(qty_to_buy)
                    if qty_to_buy <= 0:
                        return False

                    gross_cost = qty_to_buy * fill_price
                    commission = self._calculate_commission(fill_price, qty_to_buy, comm_frac, comm_fixed)
                    total_cost = gross_cost + commission
                else:
                    return False

            self.cash -= total_cost

            # Weighted Average Entry Price
            if self.qty > 0:
                current_val = self.qty * self.entry_price
                new_val = qty_to_buy * fill_price
                self.entry_price = (current_val + new_val) / (self.qty + qty_to_buy)
            else:
                self.entry_price = fill_price
                self.entry_time = timestamp

            self.qty += qty_to_buy
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
        # Compatibility: comm_bps is legacy name; comm_frac is canonical (decimal fraction)
        if comm_frac == 0.0 and comm_bps != 0.0:
            comm_frac = float(comm_bps)

        if not self.in_position:
            return False

        # Determine base quantity to sell
        target_qty = self.qty
        if qty > 0.0:
            target_qty = min(qty, self.qty)

        # Apply Volume Limits
        qty_to_sell = target_qty
        if limit_pct > 0.0 and volume > 0:
            max_vol_qty = volume * limit_pct
            qty_to_sell = min(target_qty, max_vol_qty)

        if qty_to_sell <= 0:
            return False

        fill_price = _apply_slippage(price, "sell", self.slippage)
        gross_proceeds = qty_to_sell * fill_price
        commission = self._calculate_commission(fill_price, qty_to_sell, comm_frac, comm_fixed)
        net_proceeds = gross_proceeds - commission

        self.cash += net_proceeds
        self.qty -= qty_to_sell  # Handle partials

        # Record Trade (Partial or Full)
        # Entry price is weighted average? It is constant here since we don't scale in.
        pnl_abs = net_proceeds - (qty_to_sell * self.entry_price)
        # PnL % is on this chunk
        cost_basis = qty_to_sell * self.entry_price
        pnl_pct = (pnl_abs / cost_basis) if cost_basis > 0 else 0.0

        assert self.entry_time is not None, "Trade exit without entry time"
        self.trades.append(
            Trade(
                entry_time=cast(pd.Timestamp, self.entry_time),
                exit_time=timestamp,
                entry_price=self.entry_price,
                exit_price=fill_price,
                qty=qty_to_sell,
                pnl_abs=pnl_abs,
                pnl_pct=pnl_pct,
                exit_reason=reason if self.qty <= 0 else f"{reason}_partial",
            )
        )

        if self.qty <= 1e-9:  # Float tolerance
            self.qty = 0.0
            self.entry_price = 0.0
            self.entry_time = None

        return True


def run_backtest(  # noqa: PLR0912, PLR0915
    df: pd.DataFrame,
    prepared: pd.DataFrame,
    params: StrategyParams,
    engine_cfg: EngineConfig,
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


    # Warmup Validation
    required = ["entry_signal", "exit_signal"]
    if not params.disable_stop:
        required.append("ATR")

    # Quick check using numpy to avoid excessive pandas overhead
    # But for safety/readability we keep pandas check for now, it's once per run.
    valid_mask = sig[required].notna().all(axis=1)
    if not valid_mask.any():
        equity = pd.Series(engine_cfg.initial_cash, index=df.index, dtype=float)
        metrics = compute_metrics(equity, [], periods_per_year=engine_cfg.periods_per_year)
        return BacktestResult(
            equity, [], metrics, config={"engine": engine_cfg.model_dump(), "params": params.model_dump()}
        )

    first_valid_idx = int(np.argmax(valid_mask.values))
    start_ix = min(first_valid_idx + int(engine_cfg.warmup_extra_bars), len(sig) - 1)

    # 2. Signal Shift (Vectorized)
    # i is execution time. Signal comes from i-1.
    # Gold-Tier Explicit Conversion: uses nullable boolean dtype for safe NA handling
    # and then converts to numpy booleans with False as the default for NAs.
    entry_raw = sig["entry_signal"].astype("boolean").to_numpy(dtype=bool, na_value=False)
    exit_raw = sig["exit_signal"].astype("boolean").to_numpy(dtype=bool, na_value=False)

    # We execute at `i` based on signal at `i-1`.
    # Let's shift arrays so `entry_sig[i]` means "Enter at `i`".
    # Shift array right by 1, fill 0 with False.
    entry_sig = np.concatenate(([False], entry_raw[:-1]))
    exit_sig = np.concatenate(([False], exit_raw[:-1]))

    atr_shifted: Optional[np.ndarray] = None
    if not params.disable_stop:
        atr_raw = sig["ATR"].values
        atr_shifted = np.concatenate(([np.nan], atr_raw[:-1]))

    # 3. Numpy Conversion for Speed
    opens = df["Open"].values.astype(float)
    _highs = df["High"].values.astype(float)
    lows = df["Low"].values.astype(float)
    closes = df["Close"].values.astype(float)
    volumes = df["Volume"].values.astype(float)
    timestamps = df.index

    n_bars = len(df)
    equity_arr = np.full(n_bars, np.nan)
    cash_arr = np.full(n_bars, np.nan)
    qty_arr = np.full(n_bars, np.nan)
    in_pos_arr = np.zeros(n_bars, dtype=bool)
    stop_arr = np.full(n_bars, np.nan)

    # 4. Account Setup
    account = SimulatedAccount(
        initial_cash=engine_cfg.initial_cash,
        slippage=engine_cfg.slippage_per_side,
        allow_fractional=engine_cfg.allow_fractional_shares,
    )

    # Boot the Phoenix Protocol Auditor
    repo_root = Path(os.getcwd())
    auditor = SovereignAuditor(repo_root, account_id="Institutional-Gold-Account")
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

        if account.in_position and (bars_held > params.min_hold_bars) and exit_sig[i] and account.sell(
            o,
            current_ts,
            "signal_exit",
            volume=v_limit_ref,
            limit_pct=engine_cfg.volume_limit_pct,
            comm_frac=engine_cfg.commission_rate_frac,
            comm_fixed=engine_cfg.commission_fixed,
        ) and not account.in_position:
            # If partial sell, we are STILL in position.
            # bars_since_exit resets ONLY if FULL EXIT?
            # Simplification: If we sold ANY, we consider it an exit event for cooldown?
            # No, traditionally turnover is about round trips.
            # If qty > 0, we are still holding.
            bars_since_exit = 0
            executed_exit = True
            stop_price = np.nan

        if not account.in_position and not executed_exit and (bars_since_exit >= params.cooldown_bars) and entry_sig[i]:
            # Pre-calc Stop for Sizing
            proposed_stop = np.nan
            if not params.disable_stop:
                if atr_shifted is None:
                    raise ValueError("ATR data missing for stop calculation")
                atr_ref = atr_shifted[i]
                if np.isfinite(atr_ref) and atr_ref > 0:
                    stop_dist = float(params.stop_atr) * atr_ref
                    proposed_stop = o - stop_dist  # Assume entry at Open 'o'

            # Determine capped volume for invariant check
            proposed_vol = min(v_limit_ref, v_limit_ref * engine_cfg.volume_limit_pct)
            
            # Invariant Guard: Phoenix Protocol
            if auditor.check_invariants(account, proposed_vol, o):
                if account.buy(
                    o,
                    current_ts,
                    stop_price=proposed_stop,
                    risk_pct=params.risk_per_trade,
                    volume=v_limit_ref,
                    limit_pct=engine_cfg.volume_limit_pct,
                    comm_frac=engine_cfg.commission_rate_frac,
                    comm_fixed=engine_cfg.commission_fixed,
                ):
                    # If we have a stop but it was invalid (e.g. negative), we might have bought full equity
                    # But if we intended to have a stop and calculation failed?
                    # Current logic: proposed_stop is nan -> Full Equity.
                    # This matches "disable_stop" behavior.
                    bars_held = 1
                    stop_price = proposed_stop
            else:
                # Invariant violation logged by auditor
                pass

        # 3. Intrabar Risk (Stop Loss)
        if account.in_position and not np.isnan(stop_price) and low <= stop_price:
            # HIT!
            if o < stop_price:
                # Gap Down
                account.sell(
                    o,
                    current_ts,
                    "gap_stop",
                    volume=v_limit_ref,
                    limit_pct=engine_cfg.volume_limit_pct,
                    comm_frac=engine_cfg.commission_rate_frac,
                    comm_fixed=engine_cfg.commission_fixed,
                )
            else:
                # Intraday touch
                account.sell(
                    stop_price,
                    current_ts,
                    "stop",
                    volume=v_limit_ref,
                    limit_pct=engine_cfg.volume_limit_pct,
                    comm_frac=engine_cfg.commission_rate_frac,
                    comm_fixed=engine_cfg.commission_fixed,
                )
            stop_price = np.nan

        # 4. Mark to Market
        equity_arr[i] = account.total_value(c)
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
        equity_arr[-1] = account.total_value(last_price)  # Reflect cash

    # Cleanup
    # Cleanup - Fix FutureWarning: Explicit cast to avoid downcasting warning
    equity_series = pd.Series(equity_arr, index=timestamps).ffill().fillna(float(engine_cfg.initial_cash)).astype(float)
    metrics = compute_metrics(equity_series, account.trades, periods_per_year=engine_cfg.periods_per_year)

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

    # Raw Signal Counts (from original arrays)
    metrics["raw_entry_signals"] = int(np.sum(entry_raw))
    metrics["raw_exit_signals"] = int(np.sum(exit_raw))

    # Emit Fiduciary Audit Report (Phoenix Protocol)
    auditor.emit_audit_report(account)

    return BacktestResult(
        equity_curve=equity_series,
        trades=account.trades,
        metrics=metrics,
        config={"engine": engine_cfg.model_dump(), "params": params.model_dump()},
        trace=trace,
    )
