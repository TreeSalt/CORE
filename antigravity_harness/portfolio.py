from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

import antigravity_harness.wal as write_ahead_log
from antigravity_harness.compliance import ComplianceOfficer
from antigravity_harness.engine import SimulatedAccount
from antigravity_harness.execution.fill_tape import FillTape


@dataclass
class PortfolioMetrics:
    total_equity: float
    cash: float
    allocation_pct: Dict[str, float]


class PortfolioAccount:
    """
    Vanguard Protocol: Multi-Asset Portfolio Manager.
    Aggregates N SimulatedAccounts and manages capital flows between them.
    """

    def __init__(
        self,
        initial_cash: float,
        allow_fractional: bool = True,
        compliance: Optional[ComplianceOfficer] = None,
        wal: Optional[write_ahead_log.WriteAheadLog] = None,
        fill_tape: Optional[FillTape] = None,
    ):
        self.global_cash = float(initial_cash)
        self.fill_tape = fill_tape
        self.accounts: Dict[str, SimulatedAccount] = {}  # symbol -> Account
        self.allow_fractional = allow_fractional
        self.compliance = compliance
        self.wal = wal
        self.history: List[PortfolioMetrics] = []
        self._asset_configs: Dict[str, dict] = {}

    def add_asset(
        self,
        symbol: str,
        slippage: float = 0.001,
        comm_bps: float = 0.0,
        comm_fixed: float = 0.0,
        volume_limit_pct: float = 0.0,
    ) -> None:
        if symbol in self.accounts:
            return
        # Initialize sub-account with 0 cash. We will push cash to it during rebalance.
        # Actually, SimulatedAccount needs initial_cash in init.
        # We start them with 0 and rely on Portfolio to "inject" cash?
        # SimulatedAccount doesn't have "deposit".
        # We should treat SimulatedAccount as a "Position Tracker" mostly?
        # Or we initialize with 0 and modify cash directly.
        # Or we initialize with 0 and modify cash directly.
        acct = SimulatedAccount(
            initial_cash=0.0,
            slippage=slippage,
            allow_fractional=self.allow_fractional,
            fill_tape=self.fill_tape,
        )
        # Patch friction configs which usually come from EngineConfig
        # But SimulatedAccount doesn't store them, they are passed to buy/sell.
        # We need to store friction params here to pass to rebalance executions?
        # Better: Store them in a config dict per asset.
        self.accounts[symbol] = acct
        self._asset_configs[symbol] = {
            "slippage": slippage,
            "comm_bps": comm_bps,
            "comm_fixed": comm_fixed,
            "volume_limit_pct": volume_limit_pct,
        }

    def get_total_equity(self, current_prices: Dict[str, float]) -> float:
        """
        Sum of Global Cash + Sum of (SubAccount Equity).
        Note: Sub-accounts usually hold 'cash' from sells.
        In this architecture, sub-accounts should arguably sweep cash back to global?
        Or we stick to: Global Cash is 'Unallocated'. Sub-account cash is 'Allocated but idle'.
        """
        equity = self.global_cash
        for sym, acct in self.accounts.items():
            price = current_prices.get(sym, 0.0)
            if price > 0:
                equity += acct.total_value(price)
            else:
                # If no price, rely on cash + last known value?
                # For safety, if no price, we assume 0 value for qty?
                # Or use last entry price?
                # Strict: 0.
                equity += acct.cash
        return equity

    def rebalance(  # noqa: PLR0912
        self,
        target_weights: Dict[str, float],
        current_prices: Dict[str, float],
        timestamp: pd.Timestamp,
        current_volumes: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Execute trades to align portfolio with target weights.
        target_weights: { 'SPY': 0.5, 'TLT': 0.4 } (Sum <= 1.0)
        Remainder is kept in Global Cash.
        """
        total_eq = self.get_total_equity(current_prices)

        # 1. Sweep Phase:
        # In a real fund, cash sits in one pile.
        # Here, SimulatedAccounts have their own cash.
        # We calculate Net Target Equity for each asset.

        # We need to execute SELLS first to free up cash, then BUYS.

        orders = []  # (symbol, diff_usd)

        for sym, acct in self.accounts.items():
            price = current_prices.get(sym)
            if price is None or price <= 0:
                continue

            current_val = acct.total_value(price)
            target_pct = target_weights.get(sym, 0.0)
            target_val = total_eq * target_pct

            diff = target_val - current_val
            orders.append((sym, diff, price))

        # Sort: Sells first (diff < 0), then by Symbol for Determinism
        orders.sort(key=lambda x: (x[1], x[0]))

        friction_map = getattr(self, "_asset_configs", {})

        # 1. Execute SELLS
        for sym, diff, price in orders:
            if diff >= -1e-6:  # noqa: PLR2004
                continue  # Skip Buys or small diffs for now

            acct = self.accounts[sym]
            conf = friction_map.get(sym, {})
            # params

            # We need to reduce value by abs(diff)
            sell_val_usd = abs(diff)
            qty_to_sell = sell_val_usd / price

            # Cap at owned
            qty_to_sell = min(qty_to_sell, acct.qty)

            if qty_to_sell > 0:
                # Execute Sell
                acct.sell(
                    price,
                    timestamp,
                    "rebalance_sell",
                    qty=qty_to_sell,
                    volume=current_volumes.get(sym, 0.0) if current_volumes else np.inf,
                    limit_pct=conf.get("volume_limit_pct", 0.0),
                    comm_bps=conf.get("comm_bps", 0.0),
                    comm_fixed=conf.get("comm_fixed", 0.0),
                )

            # SWEEP CASH to Global
            # Currently acct.cash holds proceeds + leftover.
            if acct.cash > 0:
                self.global_cash += acct.cash
                acct.cash = 0.0

        # 2. Execute BUYS
        for sym, diff, price in orders:
            if diff <= 1e-6:  # noqa: PLR2004
                continue  # Skip Sells

            # How much can we buy?
            buy_val_usd = diff
            # Cap at Global Cash
            buy_val_usd = min(buy_val_usd, self.global_cash)

            if buy_val_usd < 1.0:
                continue  # Too small

            acct = self.accounts[sym]
            conf = friction_map.get(sym, {})

            # Transfer Cash
            acct.cash += buy_val_usd
            self.global_cash -= buy_val_usd

            # Execute Buy (SimulatedAccount calculates qty from cash)
            # We don't pass qty, we pass cash via account state.
            acct.buy(
                price,
                timestamp,
                volume=current_volumes.get(sym, 0.0) if current_volumes else np.inf,
                limit_pct=conf.get("volume_limit_pct", 0.0),
                comm_bps=conf.get("comm_bps", 0.0),
                comm_fixed=conf.get("comm_fixed", 0.0),
            )

            # Sweep Dust back?
            # If buy didn't use all cash (e.g. integer shares), return remainder to Global.
            if acct.cash > 0:
                self.global_cash += acct.cash
                acct.cash = 0.0

        # Record Metrics
        current_eq = self.get_total_equity(current_prices)
        alloc = {}
        for s, a in self.accounts.items():
            if current_eq > 0:
                alloc[s] = a.total_value(current_prices.get(s, 0.0)) / current_eq
            else:
                alloc[s] = 0.0

        self.history.append(PortfolioMetrics(total_equity=current_eq, cash=self.global_cash, allocation_pct=alloc))
