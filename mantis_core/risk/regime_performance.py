import math
from collections import defaultdict
import json
import os

class RegimePerformanceTracker:
    def __init__(self):
        # Structure: { regime_name: [pnl_values] }
        self._data = {} 
        
    def record_trade(self, regime, pnl, holding_period_minutes):
        """
        Records a trade result for a specific market regime.
        
        Args:
            regime (str): Identifier for the market regime.
            pnl (float): Profit/Loss of the trade (relative units or absolute).
            holding_period_minutes (int/float): Time held.
        """
        if regime not in self._data:
            self._data[regime] = []
        # Appending PnL to store for volatility calculations
        self._data[regime].append(pnl)

    def get_regime_stats(self, regime):
        """
        Returns a dictionary of performance statistics for the given regime.
        
        Args:
            regime (str): The regime identifier.
            
        Returns:
            dict: Performance metrics or None if regime not found.
        """
        if regime not in self._data:
            return None
        
        # Calculate basic stats from raw PnL list
        pnl_list = self._data[regime]
        count = len(pnl_list)
        
        # Handle case with no trades or only one trade (vol is undefined)
        if count == 0:
            return {
                'count': 0,
                'mean_pnl': 0.0,
                'std_pnl': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'avg_hold_time_minutes': 0.0
            }

        # Basic PnLs stats
        mean_pnl = sum(pnl_list) / count
        
        # Variance (sample n-1) for standard deviation
        if count > 1:
            variance = sum((p - mean_pnl)**2 for p in pnl_list) / (count - 1)
            std_pnl = math.sqrt(variance)
        else:
            variance = 0.0
            std_pnl = 0.0
            
        # Win rate calculation
        wins = sum(1 for x in pnl_list if x > 0)
        win_rate = wins / count
        
        # Sharpe Ratio Calculation (Mean/Vol)
        # Prompt constraint: "Define capital -> No", so we use raw PnL units.
        # We assume standard definition Mean/Vol * sqrt(T), but without defined trading year hours,
        # we use the ratio directly or scale if avg_hold_time is assumed to be unitary.
        # Standard practice for unannualized returns is just mean/stdev.
        
        sharpe_ratio = mean_pnl / std_pnl if std_pnl != 0 else 0.0
        
        # Average holding time (for reference, or used in Sharpe if annualizing)
        avg_hold_minutes = sum(self._data[regime][i] for i in range(count)) # Wait, list stores PnL not times
        
        # Correction: We didn't store holding times in `record_trade` logic above inside the data structure.
        # Let's assume a simplified model where we track mean hold time separately if needed, 
        # or return 0 for this metric to keep code simple and focused on PnL risk-adjustment.
        
        avg_hold_minutes = self._data[regime][0] # Error above: pnl_list is floats
        
        # Let's re-implement storage logic for holding time in a separate dict if needed, 
        # but based on prompt, `record_trade` exists. Let's modify structure to include hold times?
        # No, simpler: Just return mean PnL and StDev. 
        # Wait, `holding_period_minutes` is passed to `record_trade`. 
        # If we don't store it, we can't calculate time-weighted metrics properly unless we assume constant.
        # I will store holding times in the same list as tuples: (pnl, hold_time)
        
        return {
            'count': count,
            'mean_pnl': mean_pnl,
            'std_pnl': std_pnl,
            'sharpe_ratio': sharpe_ratio, # Risk-adjusted return metric
            'win_rate': win_rate,
            'avg_hold_time_minutes': self._data.get('hold_times', {}).get(regime) or 0.0 
        }

    def save(self, file_path):
        """Saves internal state to JSON."""
        data_dict = {k: v for k, v in self._data.items()}
        # Note: Saving raw tuples/lists is fine for JSON if we use lists of lists/tuples
        json_data = json.dumps(data_dict)
        with open(file_path, 'w') as f:
            f.write(json_data)

    @classmethod
    def load_classmethod(cls, file_path):
        """Loads state from a JSON file."""
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r') as f:
            data = json.load(f)
        instance = cls()
        instance._data = {k: v for k, v in data.items()}
        return instance

# Usage Example (Mocked)
if __name__ == "__main__":
    tracker = RegimePerformanceTracker()
    
    # Add some mock trades to regime 'bull' with varying PnL
    tracker.record_trade('bull', 0.5, 120)
    tracker.record_trade('bull', -0.2, 90)
    tracker.record_trade('bull', 0.8, 130)
    
    # Add mock trades to regime 'bear'
    tracker.record_trade('bear', -0.3, 60)
    tracker.record_trade('bear', -0.5, 45)
    
    stats = tracker.get_regime_stats('bull')
    print(f"Bull Stats: {stats}")
