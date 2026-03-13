#!/usr/bin/env python3
"""
scripts/run_predatory_gate.py — Predatory Gate Stress Test Runner
=================================================================
AUTHOR: Claude (Hostile Auditor) — Supreme Council
DATE: 2026-03-13

Executes the Predatory Gate against all Zoo strategy proposals.
Generates synthetic Black Swan scenarios as proper OHLCV DataFrames,
extracts strategy code from proposal markdown files, and runs each
strategy through each scenario to measure max drawdown.

USAGE:
  cd ~/TRADER_OPS/v9e_stage
  python3 scripts/run_predatory_gate.py
"""
import json
import re
import ast
import sys
import importlib.util
import tempfile
import textwrap
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSALS_DIR = REPO_ROOT / "08_IMPLEMENTATION_NOTES"
CHECKPOINTS = REPO_ROOT / "CHECKPOINTS.yaml"
STATE_DIR = REPO_ROOT / "state"
GRAVEYARD = REPO_ROOT / "docs" / "GRAVEYARD.md"

STATE_DIR.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO GENERATORS — produce realistic OHLCV DataFrames
# ══════════════════════════════════════════════════════════════════════════════

def _make_ohlcv(close_series: np.ndarray, seed: int = 42) -> pd.DataFrame:
    """Convert a close price series into a full OHLCV DataFrame."""
    rng = np.random.RandomState(seed)
    n = len(close_series)
    noise = rng.uniform(0.001, 0.005, n)
    
    high = close_series * (1 + noise)
    low = close_series * (1 - noise)
    open_ = np.roll(close_series, 1)
    open_[0] = close_series[0]
    volume = rng.randint(1000, 50000, n).astype(float)
    
    idx = pd.date_range("2026-01-02 09:30", periods=n, freq="5min")
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, 
        "close": close_series, "volume": volume
    }, index=idx)


def scenario_covid_crash() -> pd.DataFrame:
    """5 days of cascading -5% daily drops with expanding volatility."""
    bars_per_day = 78  # 6.5h * 12 bars/h
    n = bars_per_day * 5
    rng = np.random.RandomState(1)
    close = np.zeros(n)
    close[0] = 5000.0
    for i in range(1, n):
        day = i // bars_per_day
        daily_drift = -0.05 / bars_per_day
        vol = 0.002 * (1 + day * 0.5)  # expanding vol
        close[i] = close[i-1] * (1 + daily_drift + rng.normal(0, vol))
    return _make_ohlcv(close, seed=1)


def scenario_flash_crash() -> pd.DataFrame:
    """200 bars cascading down, then V-recovery."""
    n = 400
    rng = np.random.RandomState(2)
    close = np.zeros(n)
    close[0] = 5000.0
    for i in range(1, 200):
        close[i] = close[i-1] * (1 - 0.005 + rng.normal(0, 0.001))
    for i in range(200, n):
        close[i] = close[i-1] * (1 + 0.006 + rng.normal(0, 0.001))
    return _make_ohlcv(close, seed=2)


def scenario_fed_pivot() -> pd.DataFrame:
    """3 violent intraday reversals of 2%+ each."""
    n = 234  # 3 sessions
    rng = np.random.RandomState(3)
    close = np.zeros(n)
    close[0] = 5000.0
    for i in range(1, n):
        session = i // 78
        bar_in_session = i % 78
        if bar_in_session < 26:
            drift = -0.025 / 26
        elif bar_in_session < 52:
            drift = 0.03 / 26
        else:
            drift = -0.02 / 26
        close[i] = close[i-1] * (1 + drift + rng.normal(0, 0.001))
    return _make_ohlcv(close, seed=3)


def scenario_gap_down() -> pd.DataFrame:
    """Overnight -3% gap, then slow recovery over the session."""
    n = 156  # 2 sessions
    rng = np.random.RandomState(4)
    close = np.zeros(n)
    close[0] = 5000.0
    for i in range(1, 78):
        close[i] = close[i-1] * (1 + rng.normal(0.0001, 0.001))
    close[78] = close[77] * 0.97  # gap down
    for i in range(79, n):
        close[i] = close[i-1] * (1 + 0.0004 + rng.normal(0, 0.0008))
    return _make_ohlcv(close, seed=4)


SCENARIOS = {
    "COVID_CRASH": scenario_covid_crash,
    "FLASH_CRASH": scenario_flash_crash,
    "FED_PIVOT": scenario_fed_pivot,
    "GAP_DOWN": scenario_gap_down,
}

# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY EXTRACTION — pull Python classes from proposal markdown
# ══════════════════════════════════════════════════════════════════════════════

def extract_strategies_from_proposals() -> dict:
    """Find all Zoo strategy proposals and extract their Python code."""
    strategies = {}
    
    for proposal in sorted(PROPOSALS_DIR.glob("PROPOSAL_00_PHYSICS_ENGINE_*.md")):
        content = proposal.read_text()
        if "RATIFIED" not in content:
            continue
        
        # Extract python code blocks
        code_blocks = re.findall(r'```python\s*\n(.*?)```', content, re.DOTALL)
        if not code_blocks:
            continue
        
        code = code_blocks[0]
        
        # Find the class name
        class_match = re.search(r'class\s+(\w+)', code)
        if not class_match:
            continue
        
        class_name = class_match.group(1)
        
        # Determine which Zoo variant this is
        variant = "unknown"
        for pattern in ["ZOO_E1_", "ZOO_E2_", "E1_", "E2_", "VARIANT:"]:
            vm = re.search(rf'{pattern}(\d{{3}})', content)
            if vm:
                epoch_match = re.search(r'E(\d)', content[:500])
                epoch = epoch_match.group(1) if epoch_match else "?"
                variant = f"E{epoch}_{vm.group(1)}"
                break
        
        # Try to identify by strategy name in content
        for keyword, label in [
            ("volatility_gatekeeper", "E1_001_VOLATILITY_GATEKEEPER"),
            ("mean_reversion", "E1_002_MEAN_REVERSION_SNIPER"),
            ("regime_chameleon", "E1_003_REGIME_CHAMELEON"),
            ("opening_range", "E1_004_OPENING_RANGE_BREAKOUT"),
            ("momentum_decay", "E1_005_MOMENTUM_DECAY_HARVESTER"),
            ("bollinger", "E2_001_BOLLINGER_SQUEEZE"),
            ("vwap", "E2_002_VWAP_REVERSION"),
            ("triple_ema", "E2_003_TRIPLE_EMA_CASCADE"),
            ("volume_climax", "E2_004_VOLUME_CLIMAX_FADE"),
            ("gap_fill", "E2_005_GAP_FILL_HUNTER"),
        ]:
            if keyword.lower() in content.lower():
                variant = label
                break
        
        strategies[variant] = {
            "class_name": class_name,
            "code": code,
            "proposal": proposal.name,
        }
    
    return strategies


def load_strategy_class(name: str, code: str):
    """Dynamically load a strategy class from extracted code."""
    # Add missing imports if needed
    preamble = textwrap.dedent("""
    import pandas as pd
    import numpy as np
    try:
        from antigravity_harness.strategies.base import Strategy
    except ImportError:
        class Strategy:
            name = "base"
            def prepare_data(self, df, params=None, intelligence=None, vector_cache=None):
                raise NotImplementedError
    try:
        from antigravity_harness.config import StrategyParams
    except ImportError:
        class StrategyParams:
            pass
    class BaseStrategy(Strategy):
        pass
    """)
    
    full_code = preamble + "\n" + code
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, 
                                      dir=str(REPO_ROOT / "state")) as f:
        f.write(full_code)
        f.flush()
        
        spec = importlib.util.spec_from_file_location(f"strategy_{name}", f.name)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            return None, str(e)
    
    # Find the strategy class (not Strategy/BaseStrategy/StrategyParams)
    for attr_name in dir(mod):
        obj = getattr(mod, attr_name)
        if (isinstance(obj, type) and 
            attr_name not in ("Strategy", "BaseStrategy", "StrategyParams") and
            hasattr(obj, 'generate_signals') or hasattr(obj, 'prepare_data')):
            try:
                instance = obj()
                return instance, None
            except Exception as e:
                try:
                    instance = obj.__new__(obj)
                    return instance, None
                except:
                    pass
    
    return None, "No strategy class found"


# ══════════════════════════════════════════════════════════════════════════════
# DRAWDOWN COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

def compute_max_drawdown(equity_curve: pd.Series) -> float:
    """Compute maximum drawdown percentage from an equity curve."""
    if equity_curve.empty or len(equity_curve) < 2:
        return 0.0
    cummax = equity_curve.cummax()
    drawdown = (cummax - equity_curve) / cummax
    return float(drawdown.max()) * 100  # as percentage


def simulate_strategy(strategy, bars: pd.DataFrame) -> float:
    """Run a strategy on bars and return max drawdown percentage."""
    try:
        # Try prepare_data interface (E2 strategies)
        if hasattr(strategy, 'prepare_data'):
            result = strategy.prepare_data(bars.copy(), None)
            if isinstance(result, pd.DataFrame) and 'entry_signal' in result.columns:
                entries = result['entry_signal'].fillna(False).astype(bool)
                exits = result['exit_signal'].fillna(False).astype(bool)
            else:
                return 0.0  # no signals generated
        # Try generate_signals interface (E1 strategies)
        elif hasattr(strategy, 'generate_signals'):
            signals = strategy.generate_signals(bars.copy())
            entries = signals > 0
            exits = signals < 0
        else:
            return 0.0
    except Exception as e:
        print(f"    ⚠️  Strategy execution error: {e}")
        return 99.9  # treat errors as catastrophic failure
    
    # Simple equity simulation: flat $10,000 start, 1 contract MES ($5/tick)
    equity = 10000.0
    position = 0
    entry_price = 0.0
    equity_curve = [equity]
    
    close = bars['close'].values
    for i in range(len(close)):
        try:
            is_entry = bool(entries.iloc[i]) if hasattr(entries, 'iloc') else bool(entries[i])
            is_exit = bool(exits.iloc[i]) if hasattr(exits, 'iloc') else bool(exits[i])
        except (IndexError, KeyError):
            continue
            
        if is_entry and position == 0:
            position = 1
            entry_price = close[i]
        elif is_exit and position == 1:
            pnl = (close[i] - entry_price) * 5.0  # MES $5/point
            equity += pnl
            position = 0
        
        equity_curve.append(equity)
    
    return compute_max_drawdown(pd.Series(equity_curve))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("PREDATORY GATE — BLACK SWAN STRESS TEST")
    print("=" * 60)
    
    # Load drawdown threshold
    max_dd_threshold = 15.0  # default
    if CHECKPOINTS.exists():
        try:
            cp = yaml.safe_load(CHECKPOINTS.read_text())
            # Navigate to find max_drawdown_pct
            if isinstance(cp, dict):
                for key, val in cp.items():
                    if isinstance(val, dict) and 'max_drawdown_pct' in val:
                        max_dd_threshold = float(val['max_drawdown_pct'])
                        break
        except Exception:
            pass
    print(f"Drawdown threshold: {max_dd_threshold}%\n")
    
    # Extract strategies
    print("Discovering Zoo strategies from proposals...")
    strategies = extract_strategies_from_proposals()
    print(f"Found {len(strategies)} ratified strategy proposals\n")
    
    if not strategies:
        print("❌ No strategies found. Check 08_IMPLEMENTATION_NOTES/ for RATIFIED proposals.")
        sys.exit(1)
    
    # Run scenarios
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "drawdown_threshold_pct": max_dd_threshold,
        "strategies": {},
    }
    survivors = []
    graveyard_entries = []
    
    for variant, info in sorted(strategies.items()):
        print(f"━━━ {variant} ({info['class_name']}) ━━━")
        print(f"    Source: {info['proposal']}")
        
        strategy, error = load_strategy_class(variant, info['code'])
        if error:
            print(f"    ❌ LOAD FAILED: {error}")
            report["strategies"][variant] = {"status": "LOAD_FAILED", "error": error}
            graveyard_entries.append((variant, f"Load failed: {error}"))
            continue
        
        scenario_results = {}
        worst_dd = 0.0
        
        for scenario_name, generator in SCENARIOS.items():
            bars = generator()
            dd = simulate_strategy(strategy, bars)
            scenario_results[scenario_name] = round(dd, 2)
            worst_dd = max(worst_dd, dd)
            status = "✅" if dd <= max_dd_threshold else "💀"
            print(f"    {scenario_name}: {dd:.2f}% max DD {status}")
        
        passed = worst_dd <= max_dd_threshold
        report["strategies"][variant] = {
            "status": "PASS" if passed else "KILLED",
            "class_name": info['class_name'],
            "proposal": info['proposal'],
            "scenarios": scenario_results,
            "worst_drawdown_pct": round(worst_dd, 2),
        }
        
        if passed:
            print(f"    ✅ SURVIVED — worst DD: {worst_dd:.2f}%")
            survivors.append(variant)
        else:
            print(f"    💀 KILLED — worst DD: {worst_dd:.2f}% > {max_dd_threshold}%")
            graveyard_entries.append((variant, f"Predatory Gate: {worst_dd:.2f}% DD"))
    
    # Write report
    report_path = STATE_DIR / "PREDATORY_GATE_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n📋 Report: {report_path}")
    
    # Write survivors
    survivors_path = STATE_DIR / "predatory_gate_survivors.json"
    survivors_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threshold_pct": max_dd_threshold,
        "survivors": survivors,
        "killed": [v for v in strategies if v not in survivors],
    }
    survivors_path.write_text(json.dumps(survivors_data, indent=2))
    print(f"🏆 Survivors: {survivors_path}")
    
    # Write graveyard entries
    if graveyard_entries and GRAVEYARD.exists():
        with open(GRAVEYARD, "a") as f:
            f.write(f"\n\n## Predatory Gate — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n")
            for variant, reason in graveyard_entries:
                f.write(f"- **{variant}**: {reason}\n")
        print(f"⚰️  Graveyard: {len(graveyard_entries)} entries added")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"PREDATORY GATE COMPLETE")
    print(f"{'='*60}")
    print(f"Tested:    {len(strategies)}")
    print(f"Survived:  {len(survivors)}")
    print(f"Killed:    {len(strategies) - len(survivors)}")
    print(f"{'='*60}")
    
    if survivors:
        print(f"\nSurvivors ready for CP1 paper trading:")
        for s in survivors:
            print(f"  🏆 {s}")
    else:
        print(f"\n⚠️  No survivors. Epoch 3 Alpha Synthesis will learn from the Graveyard.")


if __name__ == "__main__":
    main()
