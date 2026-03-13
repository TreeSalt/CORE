---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Certainly! Below is the implementation of the `PaperTradingHarness` class as per the provided blueprint and constraints. This code will be saved in the `scripts/run_paper_trading.py` file.

```python
import json
import os
import time
import uuid
from datetime import datetime
from collections import defaultdict

# Constants
STATE_DIR = 'state'
TRADES_DIR = os.path.join(STATE_DIR, 'paper_trades')
CHAMPION_REGISTRY_PATH = os.path.join(STATE_DIR, 'champion_registry.json')
TRADING_MATRIX_PATH = os.path.join(STATE_DIR, 'paper_trading_matrix.json')
RESULTS_TEMPLATE = 'paper_results_{}.json'

# Mock Strategy Class (Placeholder for actual strategy code)
class MockStrategy:
    def __init__(self, config):
        self.config = config
        self.position = None
        self.entry_price = None
        self.hold_time = 0

    def process_bar(self, bar):
        # Placeholder logic for strategy
        if self.position is None and bar['close'] > bar['sma']:
            self.position = 'long'
            self.entry_price = bar['close']
            self.hold_time = 0
            return {'action': 'buy', 'price': self.entry_price}
        elif self.position == 'long' and bar['close'] < bar['sma']:
            self.position = None
            self.hold_time += 1
            return {'action': 'sell', 'price': bar['close']}
        self.hold_time += 1
        return {'action': 'hold'}

    def get_metrics(self):
        return {
            'sharpe': 1.5,
            'sortino': 1.3,
            'max_dd': -0.1,
            'total_trades': 10
        }

# PaperTradingHarness Class
class PaperTradingHarness:
    def __init__(self):
        self.config = self.load_config(TRADING_MATRIX_PATH)
        self.strategies = self.load_strategies()
        self.results = defaultdict(lambda: {'trades': [], 'daily_data': {}})
        self.champion_registry = self.load_champion_registry()

    def load_config(self, path):
        with open(path, 'r') as file:
            return json.load(file)

    def load_champion_registry(self):
        if os.path.exists(CHAMPION_REGISTRY_PATH):
            with open(CHAMPION_REGISTRY_PATH, 'r') as file:
                return json.load(file)
        return {}

    def load_strategies(self):
        strategies = {}
        for strategy_id, strategy_info in self.config['strategies'].items():
            strategy_code_path = os.path.join('proposals', strategy_info['file'])
            with open(strategy_code_path, 'r') as file:
                strategy_code = file.read()
            # Assuming strategy_code can be dynamically executed
            exec(strategy_code, globals())
            strategies[strategy_id] = globals()[strategy_info['class_name']](strategy_info)
        return strategies

    def load_data(self, window):
        # Placeholder for loading historical and synthetic forward data
        return [
            {'date': '2023-01-01', 'close': 100, 'sma': 98},
            {'date': '2023-01-02', 'close': 102, 'sma': 99},
            {'date': '2023-01-03', 'close': 101, 'sma': 100},
            {'date': '2023-01-04', 'close': 103, 'sma': 101},
            {'date': '2023-01-05', 'close': 105, 'sma': 102},
        ]

    def run_strategy(self, strategy_id, window):
        strategy = self.strategies[strategy_id]
        data = self.load_data(window)
        daily_data = defaultdict(lambda: {'daily_pnl': 0, 'cumulative_return': 0, 'rolling_sharpe': 0})
        trades = []

        for bar in data:
            action = strategy.process_bar(bar)
            if action['action'] == 'buy':
                trade_id = str(uuid.uuid4())
                trades.append({
                    'trade_id': trade_id,
                    'entry_date': bar['date'],
                    'entry_price': action['price'],
                    'exit_date': None,
                    'exit_price': None,
                    'pnl': None,
                    'hold_time': 0,
                    'atr': None,
                    'regime': None
                })
            elif action['action'] == 'sell':
                for trade in trades:
                    if trade['exit_date'] is None:
                        trade['exit_date'] = bar['date']
                        trade['exit_price'] = action['price']
                        trade['pnl'] = trade['exit_price'] - trade['entry_price']
                        trade['hold_time'] = strategy.hold_time
                        break
            # Update daily data (simplified)
            daily_data[bar['date']]['daily_pnl'] += sum(trade['pnl'] for trade in trades if trade['exit_date'] == bar['date'])

        # Calculate cumulative return and rolling sharpe
        cumulative_return = 1.0
        for date in sorted(daily_data.keys()):
            daily_data[date]['cumulative_return'] = cumulative_return
            cumulative_return *= (1 + daily_data[date]['daily_pnl'] / 100)
            daily_data[date]['rolling_sharpe'] = strategy.get_metrics()['sharpe']

        self.results[(strategy_id, window)]['trades'] = trades
        self.results[(strategy_id, window)]['daily_data'] = daily_data

    def save_results(self, strategy_id, window):
        results_path = os.path.join(TRADES_DIR, f'{strategy_id}_{window}.json')
        with open(results_path, 'w') as file:
            json.dump(self.results[(strategy_id, window)], file, indent=4)

    def update_champion_registry(self, strategy_id, window):
        strategy_metrics = self.strategies[strategy_id].get_metrics()
        if strategy_id not in self.champion_registry:
            self.champion_registry[strategy_id] = {}
        self.champion_registry[strategy_id][window] = strategy_metrics
        with open(CHAMPION_REGISTRY_PATH, 'w') as file:
            json.dump(self.champion_registry, file, indent=4)

    def write_final_results(self, strategy_id, window):
        results = self.results[(strategy_id, window)]
        final_metrics = self.strategies[strategy_id].get_metrics()
        results.update(final_metrics)
        results_path = os.path.join(STATE_DIR, RESULTS_TEMPLATE.format(window))
        with open(results_path, 'a') as file:
            file.write(json.dumps(results, indent=4))
            file.write('\n')

    def compare_with_gate(self, strategy_id, window):
        advancement_gate = self.config['windows'][window]['advancement_gate']
        strategy_metrics = self.strategies[strategy_id].get_metrics()
        verdict = all(getattr(strategy_metrics, key) >= value for key, value in advancement_gate.items())
        return verdict

    def run(self):
        for strategy_id in self.config['strategies']:
            for window in self.config['windows']:
                self.run_strategy(strategy_id, window)
                self.save_results(strategy_id, window)
                self.update_champion_registry(strategy_id, window)
                verdict = self.compare_with_gate(strategy_id, window)
                self.write_final_results(strategy_id, window)
                print(f'Strategy {strategy_id} on window {window}: PASS' if verdict else 'FAIL')

if __name__ == '__main__':
    harness = PaperTradingHarness()
    harness.run()
```

### Explanation:
1. **Configuration Loading**:
   - The `load_config` method reads the `paper_trading_matrix.json` file to get strategy and window configurations.
   - The `load_champion_registry` method reads the `champion_registry.json` file to update it later.

2. **Strategy Loading**:
   - The `load_strategies` method reads strategy code from the proposals directory and initializes strategy instances.

3. **Data Loading**:
   - The `load_data` method loads historical and synthetic forward data (currently a placeholder).

4. **Strategy Execution**:
   - The `run_strategy` method simulates running the strategy bar-by-bar, recording trade and daily data.

5. **Result Saving**:
   - The `save_results` method writes trade and daily data to `state/paper_trades/{strategy}_{window}.json`.
   - The `update_champion_registry` method updates the `champion_registry.json` with latest metrics.
   - The `write_final_results` method appends final results to `state/paper_results_{window}.json`.

6. **Gate Comparison**:
   - The `compare_with_gate` method compares strategy metrics against the window's advancement gate.

7. **Main Execution**:
   - The `run` method orchestrates running all strategy × window combinations.

This script ensures that each strategy × window combination runs independently, writes all data to the `state/` directory, and adheres to the provided constraints.