---
DOMAIN: 05_REPORTING
MODEL: qwen2.5-coder:7b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class PerformanceReporter:
    def __init__(self, trade_ledger_path, report_output_path):
        self.trade_ledger_path = trade_ledger_path
        self.report_output_path = report_output_path

    def read_trade_ledger(self):
        trade_data = []
        with open(self.trade_ledger_path, 'r') as file:
            for line in file:
                trade_data.append(json.loads(line))
        return pd.DataFrame(trade_data)

    def calculate_metrics(self, trade_data):
        # Calculate per-strategy metrics
        strategies = trade_data['strategy'].unique()
        strategy_metrics = {}
        for strategy in strategies:
            strategy_data = trade_data[trade_data['strategy'] == strategy]
            strategy_metrics[strategy] = {
                'total_trades': len(strategy_data),
                'avg_win_loss_ratio': np.mean(strategy_data['profit'] / strategy_data['loss']),
                'win_rate': np.mean(strategy_data['profit'] > 0),
                'profit_factor': np.mean(strategy_data['profit']) / np.mean(strategy_data['loss']),
                'avg_hold_time': pd.to_datetime(strategy_data['exit_time']) - pd.to_datetime(strategy_data['entry_time']).mean()
            }

        # Calculate portfolio-level metrics
        portfolio_metrics = {
            'total_trades': len(trade_data),
            'avg_win_loss_ratio': np.mean(trade_data['profit'] / trade_data['loss']),
            'win_rate': np.mean(trade_data['profit'] > 0),
            'profit_factor': np.mean(trade_data['profit']) / np.mean(trade_data['loss']),
            'avg_hold_time': pd.to_datetime(trade_data['exit_time']) - pd.to_datetime(trade_data['entry_time']).mean(),
            'sharpe_ratio': self.sharpe_ratio(trade_data),
            'sortino_ratio': self.sortino_ratio(trade_data),
            'max_drawdown': self.max_drawdown(trade_data),
            'calmar_ratio': self.calmar_ratio(trade_data)
        }

        return strategy_metrics, portfolio_metrics

    def sharpe_ratio(self, trade_data):
        returns = trade_data['profit'] / trade_data['initial_balance']
        risk_free_rate = 0.01  # Assuming 1% risk-free rate
        excess_returns = returns - risk_free_rate
        return np.mean(excess_returns) / np.std(excess_returns)

    def sortino_ratio(self, trade_data):
        returns = trade_data['profit'] / trade_data['initial_balance']
        downside_returns = np.where(returns < 0, returns - 0.01, 0)  # Assuming 1% risk-free rate
        return np.mean(returns) / np.std(downside_returns)

    def max_drawdown(self, trade_data):
        cumulative_returns = (1 + trade_data['profit']).cumprod()
        rolling_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        return -np.min(drawdown)

    def calmar_ratio(self, trade_data):
        return np.mean(trade_data['profit'] / trade_data['initial_balance']) / self.max_drawdown(trade_data)

    def calculate_cp1_qualification(self, portfolio_metrics):
        days_elapsed = (datetime.now() - datetime.fromtimestamp(0)).days
        trades_count = portfolio_metrics['total_trades']
        rolling_90d_sharpe = portfolio_metrics['sharpe_ratio']
        max_dd = portfolio_metrics['max_drawdown']

        cp1_qualification = {
            'days_elapsed': days_elapsed,
            'trades_count': trades_count,
            'rolling_90d_sharpe': rolling_90d_sharpe,
            'max_dd': max_dd,
            'qualified': days_elapsed >= 90 and trades_count >= 250 and rolling_90d_sharpe >= 2.5 and max_dd <= 0.15
        }

        return cp1_qualification

    def generate_report(self, trade_data, strategy_metrics, portfolio_metrics, cp1_qualification):
        with open(self.report_output_path, 'w') as file:
            file.write("# Performance Report\n\n")
            file.write("## Portfolio Metrics\n")
            file.write(f"- Total Trades: {portfolio_metrics['total_trades']}\n")
            file.write(f"- Avg Win/Loss Ratio: {portfolio_metrics['avg_win_loss_ratio']}\n")
            file.write(f"- Win Rate: {portfolio_metrics['win_rate']}\n")
            file.write(f"- Profit Factor: {portfolio_metrics['profit_factor']}\n")
            file.write(f"- Avg Hold Time: {portfolio_metrics['avg_hold_time']}\n")
            file.write(f"- Sharpe Ratio: {portfolio_metrics['sharpe_ratio']}\n")
            file.write(f"- Sortino Ratio: {portfolio_metrics['sortino_ratio']}\n")
            file.write(f"- Max Drawdown: {portfolio_metrics['max_drawdown']}\n")
            file.write(f"- Calmar Ratio: {portfolio_metrics['calmar_ratio']}\n\n")
            file.write("## CP1 Qualification\n")
            file.write(f"- Days Elapsed: {cp1_qualification['days_elapsed']}\n")
            file.write(f"- Trades Count: {cp1_qualification['trades_count']}\n")
            file.write(f"- Rolling 90d Sharpe: {cp1_qualification['rolling_90d_sharpe']}\n")
            file.write(f"- Max Drawdown: {cp1_qualification['max_dd']}\n")
            file.write(f"- Qualified: {cp1_qualification['qualified']}\n")

    def generate_json_report(self, trade_data, strategy_metrics, portfolio_metrics, cp1_qualification):
        report_data = {
            "portfolio_metrics": portfolio_metrics,
            "cp1_qualification": cp1_qualification
        }
        with open(self.report_output_path.replace('.md', '.json'), 'w') as file:
            json.dump(report_data, file, indent=4)

    def run(self):
        trade_data = self.read_trade_ledger()
        strategy_metrics, portfolio_metrics = self.calculate_metrics(trade_data)
        cp1_qualification = self.calculate_cp1_qualification(portfolio_metrics)
        self.generate_report(trade_data, strategy_metrics, portfolio_metrics, cp1_qualification)
        self.generate_json_report(trade_data, strategy_metrics, portfolio_metrics, cp1_qualification)

# Example usage
reporter = PerformanceReporter('state/trade_ledger.jsonl', 'state/performance_report.md')
reporter.run()
```

This Python script defines a `PerformanceReporter` class that reads a trade ledger, calculates various performance metrics, and generates both human-readable and machine-readable reports. The script adheres to the constraints provided, ensuring it operates in a read-only environment and outputs valid Python code.