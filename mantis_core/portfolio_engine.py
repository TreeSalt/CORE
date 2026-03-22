import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import numpy as np
import pandas as pd

from mantis_core.compliance import ComplianceOfficer
from mantis_core.config import EngineConfig, StrategyParams
from mantis_core.correlation import CorrelationGuard
from mantis_core.execution.fill_tape import FillTape
from mantis_core.instruments.mes import MES_SPEC
from mantis_core.instruments.spy import SPY_SPEC
from mantis_core.optimization import Optimizer
from mantis_core.portfolio import PortfolioAccount
from mantis_core.portfolio_policies import PolicyConfig, apply_concentration_caps
from mantis_core.portfolio_router import PortfolioRouter
from mantis_core.portfolio_safety_overlay import SafetyConfig, SafetyOverlay, SafetyState
from mantis_core.strategies.base import Strategy
from mantis_core.wal import WriteAheadLog


def run_portfolio_backtest_verbose(  # noqa: PLR0912, PLR0913, PLR0915
    data_map: Dict[str, pd.DataFrame],
    strategy_cls: Type[Strategy],
    strat_params: StrategyParams,
    engine_config: EngineConfig,
    rebalance_freq: str = "M",
    optimization_method: str = "inverse_volatility",
    initial_cash: float = 100_000.0,
    lookback_window: int = 60,
    router: Optional[PortfolioRouter] = None,
    safety_cfg: Optional[SafetyConfig] = None,
    policy_cfg: Optional[PolicyConfig] = None,
    out_dir: Optional[Path] = None,
) -> tuple[PortfolioAccount, List[Dict[str, Any]], pd.DataFrame]:
    """
    Execute a multi-asset backtest with portfolio-level rebalancing.
    Phase 9D: includes per-bar safety overlay and concentration caps.
    Returns (PortfolioAccount, regime_log, equity_curve_df).
    """

    # Defaults
    if safety_cfg is None:
        safety_cfg = SafetyConfig()
    if policy_cfg is None:
        policy_cfg = PolicyConfig()

    # 1. Alignment checks
    assert len(data_map) > 0, "No data provided"

    combined_index = None
    for _sym, df in data_map.items():
        combined_index = df.index if combined_index is None else combined_index.intersection(df.index)

    if combined_index is None:
        raise ValueError("No common price index found among assets.")
    combined_index = combined_index.sort_values()

    clean_data = {s: df.loc[combined_index] for s, df in data_map.items()}

    # 2. Initialize Portfolio
    # Instantiate Governance
    compliance = ComplianceOfficer()
    Path("state").mkdir(exist_ok=True, parents=True)
    wal = WriteAheadLog(Path("state/wal.db"))


    # 3. Initialize Strategies
    strategies = {}
    for sym, _ in clean_data.items():
        strat = strategy_cls()
        strategies[sym] = strat
        clean_data[sym] = strat.prepare_data(clean_data[sym], strat_params)

    # 4. Event Loop
    close_prices_df = pd.DataFrame({s: df["Close"] for s, df in clean_data.items()})
    
    # MISSION v4.5.301: Regime Resolution Alignment (Run Spec Truth)
    # Resample to rebalance cadence before preloading regimes.
    # This prevents stale labels when bar interval < rebalance freq.
    if router:
        try:
            resampled = close_prices_df.resample(rebalance_freq).last().dropna()
            if not resampled.empty:
                router.preload(resampled)
            else:
                router.preload(close_prices_df)
        except (ValueError, TypeError):
            # Non-fixed freq (M, W) — preload at bar level (regimes are fine at daily+)
            router.preload(close_prices_df)

    # Phase 10.5: Volume Physics
    volume_df = pd.DataFrame({s: df["Volume"] for s, df in clean_data.items()})
    # Shift volumes to enforce t-1 participation limits
    volume_df_shifted = volume_df.shift(1).fillna(0.0)

    dates = combined_index

    # Phase 9D: Forensic FillTape
    # MISSION v4.5.306: Force Integer Lots for Futures (MES)
    if "MES" in data_map or any("MES" in s for s in data_map):
        engine_config = engine_config.model_copy(update={"allow_fractional_shares": False})
        print("🛡️  Physics Mandate: allow_fractional_shares=False enforced for MES.")

    tape: Optional[FillTape] = None
    if os.environ.get("METADATA_RELEASE_MODE") == "1":
        if out_dir is None:
            out_dir = Path(os.getcwd()) / "reports/forge" / "ibkr_smoke"
        # Use simple date for portfolio session
        session_date = dates[-1].strftime("%Y-%m-%d") if not dates.empty else "unknown"
        # MISSION v4.5.382: Bind spec and expected_symbols (Patch B)
        # MISSION v4.7.11: Frankenstein-002 Purge — Do not hardcode MES_SPEC
        first_sym = list(data_map.keys())[0] if data_map else "GENERIC"
        if "MES" in first_sym:
            initial_spec = MES_SPEC
        elif "SPY" in first_sym:
            initial_spec = SPY_SPEC
        else:
            from mantis_core.instruments.base import InstrumentSpec  # noqa: PLC0415
            initial_spec = InstrumentSpec(
                symbol=first_sym,
                asset_class="generic",
                tick_size=0.01,
                multiplier=1.0,
                lot_size=0.001 if engine_config.allow_fractional_shares else 1.0
            )

        tape = FillTape(
            output_dir=out_dir, 
            session_date=session_date, 
            spec=initial_spec,
            expected_symbols=list(data_map.keys())
        )

    portfolio = PortfolioAccount(
        initial_cash=initial_cash,
        allow_fractional=engine_config.allow_fractional_shares,
        compliance=compliance,
        wal=wal,
        fill_tape=tape,
        max_position_size_contracts=engine_config.max_position_size_contracts,
        max_trades_per_day=engine_config.max_trades_per_day,
    )
    # Re-apply assets to the new portfolio (which now has the tape)
    for sym in clean_data:
        # MISSION v4.5.382: Map spec by symbol. For non-MES, create a target spec for the symbol.
        if "MES" in sym:
            spec = MES_SPEC
        elif "SPY" in sym:
            spec = SPY_SPEC
        else:
            from mantis_core.instruments.base import InstrumentSpec  # noqa: PLC0415
            spec = InstrumentSpec(
                symbol=sym,
                asset_class="generic",
                tick_size=0.01,
                multiplier=1.0,
                lot_size=0.001 if engine_config.allow_fractional_shares else 1.0
            )

        portfolio.add_asset(
            sym,
            spec=spec,
            slippage=engine_config.slippage_per_side,
            slippage_ticks=engine_config.slippage_ticks,
            comm_bps=engine_config.commission_rate_frac,
            comm_fixed=engine_config.commission_fixed,
            volume_limit_pct=engine_config.volume_limit_pct,
        )
    regime_log = []
    equity_history = []

    # State
    last_rebalance_ts = None
    current_target_weights: Dict[str, float] = {}
    overlay = SafetyOverlay(safety_cfg)

    for i, current_ts in enumerate(dates):
        # MISSION v4.5.290: Remove Look-Ahead Bias. 
        # Signals from i-1 execute at i-Open, not i-Close.
        current_prices = {s: clean_data[s]["Open"].iloc[i] for s in clean_data}

        # ── A. Per-Bar Safety Overlay (t-1 semantics) ──
        equity_values = [h["equity"] for h in equity_history] if equity_history else [initial_cash]
        safety_state, safety_reason, dd_asof, ath_asof = overlay.evaluate(
            equity_series=equity_values,
            close_prices_df=close_prices_df,
            asof_idx=i,
            dates=dates,
        )

        # ── B. Mission v4.5.290: No-Overnight Guard ──
        # If enabled, flatten all positions before the day ends.
        is_eod = False
        if i < len(dates) - 1:
            if current_ts.date() != dates[i+1].date():
                is_eod = True
        else:
            is_eod = True # Last bar of backtest

        # Force exit if no_overnight is enabled and it's EOD
        force_eod_flatten = False
        if getattr(engine_config, "no_overnight", False) and is_eod:
            force_eod_flatten = True

        # If overlay forces action or EOD, apply it immediately
        if safety_state in (SafetyState.RISK_OFF, SafetyState.HARD_FAIL_TRIGGER) or force_eod_flatten:
            # Force flatten to cash
            new_weights = {k: 0.0 for k in current_prices}
            if new_weights != current_target_weights:
                vol_at_i = volume_df_shifted.iloc[i].to_dict()
                portfolio.rebalance(new_weights, current_prices, current_ts, current_volumes=vol_at_i)
                current_target_weights = new_weights
        elif safety_state == SafetyState.RISK_REDUCE and current_target_weights:
            # Scale down existing weights
            reduced = overlay.apply_to_weights(current_target_weights, safety_state)
            if reduced != current_target_weights:
                vol_at_i = volume_df_shifted.iloc[i].to_dict()
                portfolio.rebalance(reduced, current_prices, current_ts, current_volumes=vol_at_i)
                # Don't overwrite current_target_weights — keep originals for recovery
                # safety_forced_rebalance = True

        # ── B. Rebalance Logic (only if safety allows) ──
        should_rebalance = False
        if i >= 1 and safety_state == SafetyState.NORMAL:
            # MISSION v4.5.290: Stabilize rebalance Frequency (Stop the 15m thrash)
            # Use floor() for sub-daily cadences to ensure we bucket correctly.
            # Fallback to to_period() for non-fixed frequencies like 'M', 'W'.
            # Fallback to to_period() for non-fixed frequencies like 'M', 'W'.
            try:
                curr_p = current_ts.floor(rebalance_freq)
                prev_p = dates[i - 1].floor(rebalance_freq)
            except (ValueError, TypeError):
                # Normalize frequency for to_period (e.g., 'ME' -> 'M')
                p_freq = rebalance_freq.replace("ME", "M").replace("h", "H")
                curr_p = current_ts.to_period(p_freq)
                prev_p = dates[i - 1].to_period(p_freq)

            if curr_p != prev_p or last_rebalance_ts is None:
                should_rebalance = True

        if should_rebalance:
            target_weights = {}
            regime_info = {}

            # Decision data: strictly t-1
            history_df = close_prices_df.iloc[:i]
            asof_ts = dates[i - 1]

            # ROUTER PATH
            if router is not None:
                target_weights, regime_state = router.route(history_df, asof_ts)
                raw_regime_label = getattr(router, "last_raw_label", regime_state.label)  # Pre-persistence label

                regime_info = {
                    "timestamp": current_ts,
                    "decision_asof": asof_ts,
                    "raw_regime": raw_regime_label,
                    "confirmed_regime": regime_state.label,
                    "trend_z": regime_state.metrics.get("trend_z", 0),
                    "trend_dir": regime_state.metrics.get("trend_dir", 0),
                    "vol_ratio": regime_state.metrics.get("vol_ratio", 0),
                    "drawdown": regime_state.metrics.get("drawdown", 0),
                    "avg_corr": regime_state.metrics.get("avg_corr", 0),
                    "corr_dropped_count": regime_state.metrics.get("corr_dropped_count", 0),
                    "dispersion_ratio": regime_state.metrics.get("dispersion_ratio", 0),
                    "flags": ",".join(regime_state.flags),
                    "chosen_policy": regime_state.metrics.get("chosen_policy", ""),
                    "risk_scale": regime_state.metrics.get("risk_scale", 1.0),
                    "vol_scalar": regime_state.metrics.get("vol_scalar", 1.0),
                    "realized_vol_annual": regime_state.metrics.get("realized_vol_annual", 0),
                    "gross_exposure": regime_state.metrics.get("gross_exposure", 0),
                    "safety_state": safety_state.value,
                    "safety_rate": overlay.cfg.reduce_multiplier if safety_state == SafetyState.RISK_REDUCE else (0.0 if safety_state != SafetyState.NORMAL else 1.0),
                    "final_leverage": 1.0 - ( (portfolio.global_cash + sum(a.cash for a in portfolio.accounts.values())) / portfolio.get_total_equity(current_prices) ) if portfolio.get_total_equity(current_prices) > 0 else 0.0,
                    "dd_asof": round(dd_asof, 6),
                    "ath_asof": round(ath_asof, 2),
                    "overlay_reason": safety_reason,
                    "top_weights": json.dumps(
                        {k: round(v, 4) for k, v in sorted(target_weights.items(), key=lambda x: -x[1])[:5]},
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "final_weights_hash": hashlib.sha256(
                        str(sorted((k, round(v, 6)) for k, v in target_weights.items())).encode()
                    ).hexdigest()[:12],
                }
                regime_log.append(regime_info)

                # MISSION v4.5.382: Move Proposal Generation HERE (Post-Weight Computation)
                # This ensures the proposal reflects the actual weights about to be rebalanced.
                from mantis_core.reporting import generate_trade_proposal  # noqa: F401, PLC0415
                generate_trade_proposal(
                    output_dir=str(out_dir) if out_dir else "reports/forge/ibkr_smoke",
                    symbols=list(target_weights.keys()),
                    desired_weights=target_weights,
                    capital=portfolio.get_total_equity(current_prices),
                    strategy_name="VanguardEffective",
                    broker="ibkr",
                    authorized=os.environ.get("TRADER_OPS_AUTHORIZE") == "1",
                    mode=os.environ.get("TRADER_OPS_MODE", "assisted"),
                )

            # LEGACY / OPTIMIZER PATH
            elif optimization_method:
                history_start = max(0, i - lookback_window)
                if i - history_start >= 2:  # noqa: PLR2004
                    subset = close_prices_df.iloc[history_start:i]
                    returns = subset.pct_change().dropna()
                    valid_assets = CorrelationGuard.filter(returns, threshold=engine_config.correlation_threshold)
                    if len(valid_assets) < len(returns.columns):
                        returns = returns[valid_assets]
                    if optimization_method == "inverse_volatility":
                        target_weights = Optimizer.inverse_volatility(returns)
                    else:
                        target_weights = Optimizer.equal_weight(list(clean_data.keys()))

            # Apply concentration caps
            if target_weights:
                target_weights = apply_concentration_caps(target_weights, policy_cfg)

            # Execute
            if target_weights:
                # MISSION v4.5.422: Dynamic Annualization Footing
                # Calculate observed bars per day from the current history
                if not history_df.empty:
                    unique_days = len(np.unique(history_df.index.date))
                    if unique_days > 0:
                        observed_bars_per_day = len(history_df) / unique_days
                        dynamic_ppy = int(observed_bars_per_day * 252)
                        # Patch performance metrics or engine config for logic that uses it
                        if engine_config.periods_per_year != dynamic_ppy:
                            # We don't want to spam, but we do want to record it
                            pass

                vol_at_i = volume_df_shifted.iloc[i].to_dict()
                portfolio.rebalance(target_weights, current_prices, current_ts, current_volumes=vol_at_i)
                current_target_weights = target_weights.copy()
                last_rebalance_ts = current_ts

        # ── C. Daily Tracking ──
        current_eq = portfolio.get_total_equity(current_prices)
        all_cash = portfolio.global_cash + sum(a.cash for a in portfolio.accounts.values())
        actual_exposure = 1.0 - (all_cash / current_eq) if current_eq > 0 else 0.0
        target_exposure = sum(current_target_weights.values()) if current_target_weights else 0.0

        # Determine implied exposure scale for reporting
        exposure_scale = 1.0
        if safety_state in (SafetyState.RISK_OFF, SafetyState.HARD_FAIL_TRIGGER):
            exposure_scale = 0.0
        elif safety_state == SafetyState.RISK_REDUCE:
            exposure_scale = safety_cfg.reduce_multiplier

        equity_history.append(
            {
                "timestamp": current_ts,
                "equity": current_eq,
                "cash": all_cash,
                "safety_state": safety_state.value,
                "exposure_scale": exposure_scale,
                "dd_asof": round(dd_asof, 6),
                "ath_asof": round(ath_asof, 2),
                "overlay_reason": safety_reason,
                "target_gross_exposure": round(target_exposure, 4),
                "actual_gross_exposure": round(max(0, actual_exposure), 4),
            }
        )

    # Close FillTape
    if tape:
        tape_path = tape.close()
        print(f"📊 Portfolio Forensic FillTape Saved: {tape_path.name}")

    # Convert to DataFrame
    equity_curve_df = pd.DataFrame(equity_history)
    if not equity_curve_df.empty:
        equity_curve_df.set_index("timestamp", inplace=True)
    else:
        # MISSION v4.5.339: Support empty history (Diagnostic Smoke)
        equity_curve_df = pd.DataFrame(columns=["timestamp", "equity", "cash", "returns"]).set_index("timestamp")

    # Phase 9D: includes benchmark and safety metrics
    return portfolio, regime_log, equity_curve_df


def run_portfolio_backtest(  # noqa: PLR0913
    data_map: Dict[str, pd.DataFrame],
    strategy_cls: Type[Strategy],
    strat_params: StrategyParams,
    engine_config: EngineConfig,
    rebalance_freq: str = "M",
    optimization_method: str = "inverse_volatility",
    initial_cash: float = 100_000.0,
    lookback_window: int = 60,
    router: Optional[PortfolioRouter] = None,
    safety_cfg: Optional[SafetyConfig] = None,
    policy_cfg: Optional[PolicyConfig] = None,
) -> PortfolioAccount:
    """
    Convenience wrapper for run_portfolio_backtest_verbose.
    Returns only the PortfolioAccount (backward compatibility).
    """
    portfolio, _, _ = run_portfolio_backtest_verbose(
        data_map=data_map,
        strategy_cls=strategy_cls,
        strat_params=strat_params,
        engine_config=engine_config,
        rebalance_freq=rebalance_freq,
        optimization_method=optimization_method,
        initial_cash=initial_cash,
        lookback_window=lookback_window,
        router=router,
        safety_cfg=safety_cfg,
        policy_cfg=policy_cfg,
    )
    return portfolio
