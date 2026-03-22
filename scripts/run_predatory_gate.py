#!/usr/bin/env python3
"""
scripts/run_predatory_gate.py — Predatory Gate v2
==================================================
FIXES FROM v1:
  - BaseStrategy import: inject alias so E1 strategies load
  - Scenarios extended to 500+ bars so strategies actually trigger
  - params=None handling for E2 strategies that call params.get()
  - Better class detection for dynamic loading
"""
import json
import re
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

def _make_ohlcv(close_series, seed=42):
    rng = np.random.RandomState(seed)
    n = len(close_series)
    noise = rng.uniform(0.001, 0.005, n)
    high = close_series * (1 + noise)
    low = close_series * (1 - noise)
    open_ = np.roll(close_series, 1); open_[0] = close_series[0]
    volume = rng.randint(1000, 50000, n).astype(float)
    spikes = rng.choice(n, size=max(1, n//20), replace=False)
    volume[spikes] *= 5
    idx = pd.date_range("2026-01-02 09:30", periods=n, freq="5min")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close_series, "volume": volume}, index=idx)

def scenario_covid_crash():
    bars_per_day = 78
    n = bars_per_day * 15
    rng = np.random.RandomState(1)
    close = np.zeros(n)
    close[0] = 5000.0
    for i in range(1, n):
        day = i // bars_per_day
        if day < 10:
            drift = 0.001 / bars_per_day
            vol = 0.001
        else:
            drift = -0.05 / bars_per_day
            vol = 0.003 * (1 + (day - 10) * 0.3)
        close[i] = close[i-1] * (1 + drift + rng.normal(0, vol))
    return _make_ohlcv(close, seed=1)

def scenario_flash_crash():
    bars_per_day = 78
    n_warmup = bars_per_day * 5
    n_crash = 200
    n_recovery = 200
    n = n_warmup + n_crash + n_recovery
    rng = np.random.RandomState(2)
    close = np.zeros(n)
    close[0] = 5000.0
    for i in range(1, n_warmup):
        close[i] = close[i-1] * (1 + 0.0002 + rng.normal(0, 0.001))
    for i in range(n_warmup, n_warmup + n_crash):
        close[i] = close[i-1] * (1 - 0.004 + rng.normal(0, 0.001))
    for i in range(n_warmup + n_crash, n):
        close[i] = close[i-1] * (1 + 0.005 + rng.normal(0, 0.001))
    return _make_ohlcv(close, seed=2)

def scenario_fed_pivot():
    bars_per_day = 78
    n = bars_per_day * 8
    rng = np.random.RandomState(3)
    close = np.zeros(n)
    close[0] = 5000.0
    for i in range(1, n):
        day = i // bars_per_day
        bar = i % bars_per_day
        if day < 5:
            close[i] = close[i-1] * (1 + 0.0001 + rng.normal(0, 0.001))
        else:
            if bar < 26: drift = -0.03 / 26
            elif bar < 52: drift = 0.04 / 26
            else: drift = -0.025 / 26
            close[i] = close[i-1] * (1 + drift + rng.normal(0, 0.002))
    return _make_ohlcv(close, seed=3)

def scenario_gap_down():
    bars_per_day = 78
    n = bars_per_day * 8
    rng = np.random.RandomState(4)
    close = np.zeros(n)
    close[0] = 5000.0
    for i in range(1, n):
        day = i // bars_per_day
        bar = i % bars_per_day
        if day < 5:
            close[i] = close[i-1] * (1 + 0.0002 + rng.normal(0, 0.001))
        elif day == 5 and bar == 0:
            close[i] = close[i-1] * 0.97
        else:
            close[i] = close[i-1] * (1 + 0.0003 + rng.normal(0, 0.0008))
    return _make_ohlcv(close, seed=4)

SCENARIOS = {
    "COVID_CRASH": scenario_covid_crash,
    "FLASH_CRASH": scenario_flash_crash,
    "FED_PIVOT": scenario_fed_pivot,
    "GAP_DOWN": scenario_gap_down,
}

def extract_strategies_from_proposals():
    strategies = {}
    for proposal in sorted(PROPOSALS_DIR.glob("PROPOSAL_00_PHYSICS_ENGINE_*.md")):
        content = proposal.read_text()
        if "RATIFIED" not in content:
            continue
        code_blocks = re.findall(r'```python\s*\n(.*?)```', content, re.DOTALL)
        if not code_blocks:
            continue
        code = code_blocks[0]
        class_match = re.search(r'class\s+(\w+)', code)
        if not class_match:
            continue
        class_name = class_match.group(1)
        if "generate_covid_crash" in code or "predatory" in code.lower():
            continue
        variant = "unknown"
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
        if variant in strategies:
            if proposal.name > strategies[variant]["proposal"]:
                strategies[variant] = {"class_name": class_name, "code": code, "proposal": proposal.name}
        else:
            strategies[variant] = {"class_name": class_name, "code": code, "proposal": proposal.name}
    return strategies

def load_strategy_class(name, code):
    preamble = textwrap.dedent("""\
    import pandas as pd
    import numpy as np
    from collections import namedtuple

    class Strategy:
        name = "base"
        def prepare_data(self, df, params=None, intelligence=None, vector_cache=None):
            raise NotImplementedError
        def generate_signals(self, bars):
            raise NotImplementedError

    BaseStrategy = Strategy

    class StrategyParams:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
        def get(self, key, default=None):
            return getattr(self, key, default)
        def __getattr__(self, name):
            return None
    """)
    cleaned_code = re.sub(r'^from\s+mantis_core\S*\s+import\s+.*$', '# (import shimmed)', code, flags=re.MULTILINE)
    full_code = preamble + "\n" + cleaned_code
    tmp = Path(REPO_ROOT / "state" / f"_gate_{name.replace(' ', '_').replace('/', '_')}.py")
    tmp.write_text(full_code)
    spec = importlib.util.spec_from_file_location(f"strategy_{name}", str(tmp))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        return None, str(e)
    skip = {"Strategy", "BaseStrategy", "StrategyParams"}
    for attr_name in dir(mod):
        if attr_name.startswith("_") or attr_name in skip:
            continue
        obj = getattr(mod, attr_name)
        if not isinstance(obj, type):
            continue
        if issubclass(obj, getattr(mod, 'Strategy')):
            try:
                instance = obj()
                return instance, None
            except TypeError:
                try:
                    instance = obj.__new__(obj)
                    return instance, None
                except:
                    pass
    return None, "No strategy class found"

def compute_max_drawdown(equity_curve):
    if equity_curve.empty or len(equity_curve) < 2:
        return 0.0
    cummax = equity_curve.cummax()
    drawdown = (cummax - equity_curve) / cummax
    return float(drawdown.max()) * 100

def simulate_strategy(strategy, bars):
    trades = 0
    try:
        has_prepare = hasattr(strategy, 'prepare_data')
        has_signals = hasattr(strategy, 'generate_signals')
        if has_prepare:
            try:
                result = strategy.prepare_data(bars.copy(), None)
            except (AttributeError, TypeError):
                from types import SimpleNamespace
                params = SimpleNamespace()
                result = strategy.prepare_data(bars.copy(), params)
            if isinstance(result, pd.DataFrame) and 'entry_signal' in result.columns:
                entries = result['entry_signal'].fillna(False).astype(bool)
                exits = result['exit_signal'].fillna(False).astype(bool)
            else:
                return 0.0, 0
        elif has_signals:
            signals = strategy.generate_signals(bars.copy())
            entries = signals > 0
            exits = signals < 0
        else:
            return 0.0, 0
    except Exception as e:
        print(f"    ⚠️  Execution error: {e}")
        return 99.9, 0

    equity = 10000.0
    position = 0
    entry_price = 0.0
    equity_curve = [equity]
    close = bars['close'].values
    for i in range(len(close)):
        try:
            is_entry = bool(entries.iloc[i])
            is_exit = bool(exits.iloc[i])
        except (IndexError, KeyError):
            continue
        if is_entry and position == 0:
            position = 1
            entry_price = close[i]
            trades += 1
        elif is_exit and position == 1:
            pnl = (close[i] - entry_price) * 5.0
            equity += pnl
            position = 0
        equity_curve.append(equity)
    return compute_max_drawdown(pd.Series(equity_curve)), trades

def main():
    print("=" * 60)
    print("PREDATORY GATE v2 — BLACK SWAN STRESS TEST")
    print("=" * 60)
    max_dd_threshold = 15.0
    if CHECKPOINTS.exists():
        try:
            cp = yaml.safe_load(CHECKPOINTS.read_text())
            if isinstance(cp, dict):
                for key, val in cp.items():
                    if isinstance(val, dict) and 'max_drawdown_pct' in val:
                        max_dd_threshold = float(val['max_drawdown_pct'])
                        break
        except Exception:
            pass
    print(f"Drawdown threshold: {max_dd_threshold}%")
    print(f"Scenarios: {', '.join(SCENARIOS.keys())}")
    print(f"Scenario length: 624-1170 bars (warmup + stress)\n")

    print("Discovering Zoo strategies from proposals...")
    strategies = extract_strategies_from_proposals()
    print(f"Found {len(strategies)} ratified strategies (deduplicated)\n")
    if not strategies:
        print("No strategies found.")
        sys.exit(1)

    report = {"version": "2.0", "timestamp": datetime.now(timezone.utc).isoformat(), "drawdown_threshold_pct": max_dd_threshold, "strategies": {}}
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
        total_trades = 0
        for scenario_name, generator in SCENARIOS.items():
            bars = generator()
            dd, t = simulate_strategy(strategy, bars)
            scenario_results[scenario_name] = {"max_dd_pct": round(dd, 2), "trades": t}
            worst_dd = max(worst_dd, dd)
            total_trades += t
            icon = "✅" if dd <= max_dd_threshold else "💀"
            tn = f" ({t} trades)" if t > 0 else " (no trades)"
            print(f"    {scenario_name}: {dd:.2f}% DD{tn} {icon}")
        passed = worst_dd <= max_dd_threshold
        report["strategies"][variant] = {"status": "PASS" if passed else "KILLED", "class_name": info['class_name'], "proposal": info['proposal'], "scenarios": scenario_results, "worst_drawdown_pct": round(worst_dd, 2), "total_trades": total_trades}
        if passed:
            activity = "ACTIVE" if total_trades > 0 else "DORMANT"
            print(f"    ✅ SURVIVED — worst DD: {worst_dd:.2f}% | {activity} ({total_trades} trades)")
            survivors.append({"variant": variant, "trades": total_trades, "worst_dd": round(worst_dd, 2)})
        else:
            print(f"    💀 KILLED — worst DD: {worst_dd:.2f}% > {max_dd_threshold}%")
            graveyard_entries.append((variant, f"Predatory Gate v2: {worst_dd:.2f}% DD"))

    (STATE_DIR / "PREDATORY_GATE_REPORT.json").write_text(json.dumps(report, indent=2))
    survivors_data = {"version": "2.0", "timestamp": datetime.now(timezone.utc).isoformat(), "threshold_pct": max_dd_threshold, "survivors": survivors, "active_survivors": [s for s in survivors if s["trades"] > 0], "dormant_survivors": [s for s in survivors if s["trades"] == 0], "killed": [v for v in strategies if v not in [s["variant"] for s in survivors]]}
    (STATE_DIR / "predatory_gate_survivors.json").write_text(json.dumps(survivors_data, indent=2))

    if graveyard_entries and GRAVEYARD.exists():
        with open(GRAVEYARD, "a") as f:
            f.write(f"\n\n## Predatory Gate v2 — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n")
            for variant, reason in graveyard_entries:
                f.write(f"- **{variant}**: {reason}\n")

    active = [s for s in survivors if s["trades"] > 0]
    dormant = [s for s in survivors if s["trades"] == 0]
    print(f"\n{'='*60}")
    print(f"PREDATORY GATE v2 COMPLETE")
    print(f"{'='*60}")
    print(f"Tested:     {len(strategies)}")
    print(f"Survived:   {len(survivors)} ({len(active)} active, {len(dormant)} dormant)")
    print(f"Killed:     {len(strategies) - len(survivors)}")
    print(f"{'='*60}")
    if active:
        print(f"\n🏆 ACTIVE SURVIVORS (traded during stress):")
        for s in active:
            print(f"  🏆 {s['variant']} — {s['trades']} trades, {s['worst_dd']}% max DD")
    if dormant:
        print(f"\n😴 DORMANT SURVIVORS (entry conditions never fired):")
        for s in dormant:
            print(f"  😴 {s['variant']}")
    if not survivors:
        print(f"\n⚠️ No survivors. Graveyard enriched for Epoch 3.")

if __name__ == "__main__":
    main()
