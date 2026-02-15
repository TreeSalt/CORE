import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import pandas as pd

from antigravity_harness.compliance import ComplianceOfficer
from antigravity_harness.config import EngineConfig, StrategyParams
from antigravity_harness.correlation import CorrelationGuard
from antigravity_harness.optimization import Optimizer
from antigravity_harness.portfolio import PortfolioAccount
from antigravity_harness.portfolio_policies import PolicyConfig, apply_concentration_caps
from antigravity_harness.portfolio_router import PortfolioRouter
from antigravity_harness.portfolio_safety_overlay import SafetyConfig, SafetyOverlay, SafetyState
from antigravity_harness.strategies.base import Strategy
from antigravity_harness.wal import WriteAheadLog


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

    portfolio = PortfolioAccount(
        initial_cash=initial_cash,
        allow_fractional=engine_config.allow_fractional_shares,
        compliance=compliance,
        wal=wal,
    )
    for sym in clean_data:
        portfolio.add_asset(
            sym,
            slippage=engine_config.slippage_per_side,
            comm_frac=engine_config.commission_rate_frac,
            comm_fixed=engine_config.commission_fixed,
            volume_limit_pct=engine_config.volume_limit_pct,
        )

    # 3. Initialize Strategies
    strategies = {}
    for sym, _ in clean_data.items():
        strat = strategy_cls()
        strategies[sym] = strat
        clean_data[sym] = strat.prepare_data(clean_data[sym], strat_params)

    # 4. Event Loop
    close_prices_df = pd.DataFrame({s: df["Close"] for s, df in clean_data.items()})
    # Phase 10.5: Volume Physics
    volume_df = pd.DataFrame({s: df["Volume"] for s, df in clean_data.items()})
    # Shift volumes to enforce t-1 participation limits
    volume_df_shifted = volume_df.shift(1).fillna(0.0)

    dates = combined_index
    regime_log = []
    equity_history = []

    # State
    last_rebalance_ts = None
    current_target_weights: Dict[str, float] = {}
    overlay = SafetyOverlay(safety_cfg)

    for i, current_ts in enumerate(dates):
        current_prices = {s: clean_data[s]["Close"].iloc[i] for s in clean_data}

        # ── A. Per-Bar Safety Overlay (t-1 semantics) ──
        equity_values = [h["equity"] for h in equity_history] if equity_history else [initial_cash]
        safety_state, safety_reason, dd_asof, ath_asof = overlay.evaluate(
            equity_series=equity_values,
            close_prices_df=close_prices_df,
            asof_idx=i,
            dates=dates,
        )

        # If overlay forces action, apply it immediately
        # safety_forced_rebalance = False
        if safety_state in (SafetyState.RISK_OFF, SafetyState.HARD_FAIL_TRIGGER):
            # Force flatten to cash
            new_weights = {k: 0.0 for k in current_prices}
            if new_weights != current_target_weights:
                vol_at_i = volume_df_shifted.iloc[i].to_dict()
                portfolio.rebalance(new_weights, current_prices, current_ts, current_volumes=vol_at_i)
                current_target_weights = new_weights
                # safety_forced_rebalance = True
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
            period_freq = rebalance_freq.replace("ME", "M")
            curr_p = current_ts.to_period(period_freq)
            prev_p = dates[i - 1].to_period(period_freq)
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
                    "dispersion_ratio": regime_state.metrics.get("dispersion_ratio", 0),
                    "flags": ",".join(regime_state.flags),
                    "chosen_policy": regime_state.metrics.get("chosen_policy", ""),
                    "risk_scale": regime_state.metrics.get("risk_scale", 1.0),
                    "vol_scalar": regime_state.metrics.get("vol_scalar", 1.0),
                    "realized_vol_annual": regime_state.metrics.get("realized_vol_annual", 0),
                    "gross_exposure": regime_state.metrics.get("gross_exposure", 0),
                    "safety_state": safety_state.value,
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

    # Convert to DataFrame
    equity_curve_df = pd.DataFrame(equity_history)
    equity_curve_df.set_index("timestamp", inplace=True)

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
