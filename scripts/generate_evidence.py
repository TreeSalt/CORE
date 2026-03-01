#!/usr/bin/env python3
# ruff: noqa: E402, I001
"""
scripts/generate_evidence.py
MISSION v4.5.360: Walk-Forward Evidence Generation.
Orchestrates decoupled IS/OOS simulations with leakage guards and segregated reporting.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

# Bootstrap path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Standard imports
from antigravity_harness.config import EngineConfig, StrategyParams
from antigravity_harness.data_loader import ZeroCopyLoader
from antigravity_harness.metrics import profit_factor
from antigravity_harness.portfolio_engine import run_portfolio_backtest_verbose
from antigravity_harness.portfolio_policies import PolicyConfig
from antigravity_harness.portfolio_router import PortfolioRouter, RegimeConfig
from antigravity_harness.portfolio_safety_overlay import SafetyConfig
from antigravity_harness.reporting import (
    generate_no_trade_report,
    generate_walkforward_report,
    save_run_metadata,
)
from antigravity_harness.strategies import get_strategy
from antigravity_harness.capabilities import generate_capability_snapshot
from antigravity_harness.tradability import generate_viability_table, select_viable_smoke_universe
from antigravity_harness.execution.fill_tape import FillTape
from antigravity_harness.instruments.mes import MES_SPEC


def load_and_split(symbols: list[str], oos_split: float):
    is_map = {}
    oos_map = {}
    is_hashes = {}
    oos_hashes = {}
    for sym in symbols:
        data_path = REPO_ROOT / "data" / f"{sym.lower().replace('-', '_')}.parquet"
        if not data_path.exists():
            hits = list(REPO_ROOT.glob(f"**/data/**/{sym.lower().replace('-', '_')}.parquet"))
            if hits:
                data_path = hits[0]
            else:
                print(f"❌ Missing data for {sym} at {data_path}")
                sys.exit(1)
        print(f"📖 Loading {sym} from {data_path.name}...")
        df = ZeroCopyLoader.load_market_data(data_path)
        df_is, df_oos, is_h, oos_h = ZeroCopyLoader.split_is_oos(df, oos_split=oos_split)
        is_map[sym] = df_is
        oos_map[sym] = df_oos
        is_hashes[sym] = is_h
        oos_hashes[sym] = oos_h
    return is_map, oos_map, is_hashes, oos_hashes


def run_is_simulation(is_map, strategy_cls, engine_cfg, router, safety_cfg, policy_cfg, is_out, is_hashes):
    print("\n🚀 Running In-Sample (IS) Simulation...")
    acct, _, _ = run_portfolio_backtest_verbose(
        data_map=is_map,
        strategy_cls=strategy_cls,
        strat_params=StrategyParams(),
        engine_config=engine_cfg,
        router=router,
        safety_cfg=safety_cfg,
        policy_cfg=policy_cfg,
        out_dir=is_out,
    )
    is_trades = []
    for account in acct.accounts.values():
        is_trades.extend(account.trades)
    is_pf = profit_factor(is_trades)
    save_run_metadata(
        output_dir=str(is_out),
        config={"oos_split": 0.2, "phase": "IS"},
        extra={
            "is_data_hash": str(is_hashes), 
            "data_hash": "IS_MIXED",
            "manifest_sha256": "INTERNAL_FORGE_EMULATED",
            "payload_manifest_sha256": "INTERNAL_FORGE_EMULATED"
        }
    )
    print(f"✅ IS Complete. Profit Factor: {is_pf:.2f}")
    return acct, len(is_trades)


def run_oos_simulation(oos_map, strategy_cls, engine_cfg, router, safety_cfg, policy_cfg, oos_out, oos_hashes, base_out):
    print("\n🚀 Running Out-of-Sample (OOS) Simulation...")
    acct, _, _ = run_portfolio_backtest_verbose(
        data_map=oos_map,
        strategy_cls=strategy_cls,
        strat_params=StrategyParams(),
        engine_config=engine_cfg,
        router=router,
        safety_cfg=safety_cfg,
        policy_cfg=policy_cfg,
        out_dir=oos_out,
    )
    oos_trades = []
    for account in acct.accounts.values():
        oos_trades.extend(account.trades)
    oos_pf = profit_factor(oos_trades)
    save_run_metadata(
        output_dir=str(oos_out),
        config={"oos_split": 0.2, "phase": "OOS"},
        extra={
            "oos_data_hash": str(oos_hashes), 
            "data_hash": "OOS_MIXED",
            "manifest_sha256": "INTERNAL_FORGE_EMULATED",
            "payload_manifest_sha256": "INTERNAL_FORGE_EMULATED"
        }
    )
    exposure_bars = sum(1 for h in acct.history if any(v > 0 for v in h.allocation_pct.values()))
    intended_exposure = 1 if (exposure_bars > 0 or len(oos_trades) > 0) else 0
    oos_metrics = {
        "profit_factor": oos_pf,
        "sharpe": getattr(acct, "sharpe_ratio", 0.0),
        "fills": len(acct.fill_tape.records) if acct.fill_tape else 0,
    }
    status = generate_walkforward_report(
        output_dir=str(base_out),
        oos_metrics=oos_metrics,
        oos_fills_count=oos_metrics["fills"],
        oos_intended_exposure_bars=intended_exposure,
        oos_pf=oos_pf,
    )
    print(f"✅ OOS Complete. Status: {status} (PF: {oos_pf:.2f})")
    return status, len(oos_trades)


def main():  # noqa: PLR0915
    parser = argparse.ArgumentParser(description="TRADER_OPS Walk-Forward Evidence Generator")
    parser.add_argument("--symbols", required=True, help="Comma-separated symbols")
    parser.add_argument("--oos_split", type=float, default=0.2, help="Fraction for OOS data (default 0.2)")
    parser.add_argument("--outdir", required=True, help="Base output directory for walk-forward reports")
    parser.add_argument("--strategy", default="v040_alpha_prime", help="Strategy base name")
    parser.add_argument("--interval", default="5m", help="Data interval")
    parser.add_argument("--equity", action="store_true", help="Set engine to equity physics")
    parser.add_argument("--profile", help="Path to profile YAML (defaults to seed_profile.yaml)")
    parser.add_argument("--authorize", action="store_true", help="MISSION v4.5.423: Authorize execution for Evidence Truth Pack.")
    args = parser.parse_args()
    
    # MISSION v4.5.423: Propagate Authorization
    if args.authorize:
        os.environ["TRADER_OPS_AUTHORIZE"] = "1"
        os.environ["TRADER_OPS_MODE"] = "assisted"
    
    # MISSION v4.5.423: Force FillTape Activation
    os.environ["METADATA_RELEASE_MODE"] = "1"

    symbols = [s.strip() for s in args.symbols.split(",")]
    base_out = Path(args.outdir)
    is_out, oos_out = base_out / "IS", base_out / "OOS"
    is_out.mkdir(parents=True, exist_ok=True)
    oos_out.mkdir(parents=True, exist_ok=True)

    # MISSION v4.5.412: Early Allowlist Gate
    profile_path = Path(args.profile) if args.profile else REPO_ROOT / "profiles/seed_profile.yaml"
    reports_dir = base_out / "is_oos_smoke"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate Capabilities & Viability
    caps = generate_capability_snapshot(profile_path, reports_dir)
    vt = generate_viability_table(caps, reports_dir)
    viable_symbols = select_viable_smoke_universe(vt)
    
    # MISSION v4.5.412: Fail-Closed if requested symbols not in viable universe
    # MISSION v4.5.424: Identity Warden Check
    is_license_blocked = any(inst.get("reason") == "LICENSE_INVALID" for inst in vt.get("instruments", []))
    
    allowed_symbols = [s for s in symbols if s in viable_symbols]
    
    if is_license_blocked:
        print("🛑 FAIL-CLOSED: Identity Warden has blocked execution (LICENSE_INVALID).")
        generate_no_trade_report(
            output_dir=str(base_out),
            fills_count=0,
            capital=caps.get("buying_power_cash_usd", 0),
            reason="LICENSE_INVALID: Active license key required for execution."
        )
        tape = FillTape(output_dir=base_out, session_date="LICENSE_BLOCKED", spec=MES_SPEC)
        tape.close()

        results_path = base_out / "results.csv"
        with open(results_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "status", "fail_gate", "fail_reason", "profit_factor",
                "rebalance_events", "fills_count", "sharpe_ratio",
                "max_dd_pct", "total_return_pct",
            ])
            writer.writeheader()
            writer.writerow({
                "status": "SMOKE_BLOCKED_LICENSE_INVALID",
                "fail_gate": "LICENSE",
                "fail_reason": "LICENSE_INVALID: Active license key required for execution.",
                "profit_factor": "",
                "rebalance_events": 0,
                "fills_count": 0,
                "sharpe_ratio": "",
                "max_dd_pct": "",
                "total_return_pct": "",
            })

        save_run_metadata(
            str(base_out),
            config={"symbols": symbols, "fail_closed": True},
            cmd_args={k: str(v) for k, v in vars(args).items() if (hasattr(args, k) and k != "func")},
            extra={
                "fills_count": 0, 
                "status": "SMOKE_BLOCKED_LICENSE_INVALID",
                "allowlist_override_applied": vt.get("allowlist_override_applied", False),
                "override_sha256": vt.get("override_sha256", "N/A"),
                "license_status": caps.get("license_status", "UNKNOWN"),
                "manifest_sha256": caps.get("manifest_sha256", "UNKNOWN_LICENSE_BLOCK"),
                "payload_manifest_sha256": "UNKNOWN_LICENSE_BLOCK"
            }
        )
        return

    if not allowed_symbols:
        print(f"🚫 FAIL-CLOSED: No requested symbols {symbols} are viable (Allowlist Check).")
        generate_no_trade_report(
            output_dir=str(base_out),
            router_desired_weights={s: 1.0 for s in symbols},
            fills_count=0,
            capital=caps.get("buying_power_cash_usd", 0),
            reason=f"ALLOWLIST_DENIED: Requested symbols {symbols} not in viable smoke universe."
        )
        # Create empty header-only fill_tape.csv to satisfy downstream verification
        tape = FillTape(output_dir=base_out, session_date="FAIL_CLOSED", spec=MES_SPEC)
        tape.close()

        # MISSION v4.5.417: Emit results.csv for fail-closed compliance
        results_path = base_out / "results.csv"
        with open(results_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "status", "fail_gate", "fail_reason", "profit_factor",
                "rebalance_events", "fills_count", "sharpe_ratio",
                "max_dd_pct", "total_return_pct",
            ])
            writer.writeheader()
            writer.writerow({
                "status": "SMOKE_BLOCKED_ALLOWLIST_VIOLATION",
                "fail_gate": "ALLOWLIST",
                "fail_reason": f"ALLOWLIST_DENIED: Requested symbols {symbols} not in viable smoke universe.",
                "profit_factor": "",
                "rebalance_events": 0,
                "fills_count": 0,
                "sharpe_ratio": "",
                "max_dd_pct": "",
                "total_return_pct": "",
            })

        # Save metadata for audit trail
        save_run_metadata(
            str(base_out),
            config={"symbols": symbols, "fail_closed": True},
            cmd_args={k: str(v) for k, v in vars(args).items() if (hasattr(args, k) and k != "func")},
        extra={
            "fills_count": 0, 
            "status": "SMOKE_BLOCKED_ALLOWLIST_VIOLATION",
            "allowlist_override_applied": vt.get("allowlist_override_applied", False),
            "override_sha256": vt.get("override_sha256", "N/A"),
            "manifest_sha256": caps.get("manifest_sha256", "UNKNOWN_ALLOWLIST_BLOCK"),
            "payload_manifest_sha256": "UNKNOWN_ALLOWLIST_BLOCK"
        }
        )

        print(f"📋 Fail-closed report generated at {base_out}")
        return

    # Filter to only allowed symbols
    symbols = allowed_symbols
    print(f"✅ Filtered Symbols (Allowlist): {symbols}")

    # Load and split after allowlist check
    is_map, oos_map, is_hashes, oos_hashes = load_and_split(symbols, args.oos_split)

    engine_cfg = EngineConfig(interval=args.interval, is_crypto=not args.equity)
    # MISSION v4.5.412: Enforce 'backtest' adapter via environment or config flag
    # In generate_evidence.py, we are running backtests locally, but we must ensure
    # that no adapter attempts live connections. 
    os.environ["TRADER_OPS_EXECUTION_MODE"] = "backtest"
    
    router = PortfolioRouter(RegimeConfig(), PolicyConfig(), interval=args.interval)
    strategy_cls = get_strategy(args.strategy).__class__

    _, is_fills = run_is_simulation(is_map, strategy_cls, engine_cfg, router, SafetyConfig(), PolicyConfig(), is_out, is_hashes)

    final_status = "PASS_IS_ONLY"
    total_fills = is_fills
    if not any(df.empty for df in oos_map.values()):
        final_status, oos_fills = run_oos_simulation(
            oos_map, strategy_cls, engine_cfg, router, SafetyConfig(), PolicyConfig(), oos_out, oos_hashes, base_out
        )
        total_fills += oos_fills

    # Final metadata bind with override info
    save_run_metadata(
        str(base_out),
        config={"symbols": symbols},
        cmd_args={k: str(v) for k, v in vars(args).items() if (hasattr(args, k) and k != "func")},
        extra={
            "status": final_status,
            "fills_count": total_fills,
            "allowlist_override_applied": vt.get("allowlist_override_applied", False),
            "override_sha256": vt.get("override_sha256", "N/A"),
            "manifest_sha256": caps.get("manifest_sha256", "INTERNAL_FORGE_EMULATED"),
            "payload_manifest_sha256": "INTERNAL_FORGE_EMULATED",
            "data_hash": "WF_MIXED"
        }
    )

    print(f"\n✨ Walk-Forward Phase Complete. Final Verdict: {final_status}")


if __name__ == "__main__":
    main()
