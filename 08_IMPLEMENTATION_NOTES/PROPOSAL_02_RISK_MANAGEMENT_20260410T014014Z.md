---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class DecayAnalysisResult:
    timestamp: datetime
    paper_alpha: float
    live_alpha: float
    actual_decay_pct: float
    expected_decay_pct: float = 0.4
    decomposition: Dict[str, float]
    alert_triggered: bool
    recommended_action: str

class AlphaDecayMonitor:
    def __init__(self, expected_decay_rate: float = 0.4, window_size: int = 20):
        """
        Initialize the Monitor with research-derived decay expectation.
        
        :param expected_decay_rate: Expected decay from paper alpha to live alpha (0.4).
        :param window_size: Rolling window size for comparison analysis.
        """
        self.expected_decay_rate = expected_decay_rate
        self.window_size = window_size
        self.signal_history: List[Tuple[datetime, float, float]] = []

    def update_signals(self, paper_alpha: float, live_alpha: float) -> None:
        """
        Record current paper and live alpha signals for rolling analysis.
        
        :param paper_alpha: Theoretical/paper backtest alpha.
        :param live_alpha: Actual executed/live alpha.
        """
        timestamp = datetime.now()
        self.signal_history.append((timestamp, paper_alpha, live_alpha))

    def rolling_window_comparison(self) -> List[DecayAnalysisResult]:
        """
        Perform rolling window comparison of expected decay vs actual observed decay.
        
        :return: List of analysis results for each rolling window.
        """
        reports = []
        if len(self.signal_history) < self.window_size:
            return reports

        # Iterate through windows to compare stability and decay rates
        for i in range(len(self.signal_history) - self.window_size + 1):
            window_data = self.signal_history[i:i + self.window_size]
            
            avg_paper_alpha = sum(x[1] for x in window_data) / len(window_data)
            avg_live_alpha = sum(x[2] for x in window_data) / len(window_data)
            
            # Calculate actual decay percentage observed in this window
            current_decay_pct = 1 - (avg_live_alpha / avg_paper_alpha) if avg_paper_alpha != 0 else 0
            
            report = DecayAnalysisResult(
                timestamp=window_data[-1][0],
                paper_alpha=avg_paper_alpha,
                live_alpha=avg_live_alpha,
                actual_decay_pct=current_decay_pct,
                expected_decay_pct=self.expected_decay_rate,
                decomposition={
                    "slippage": 0.0,
                    "adverse_selection": 0.0,
                    "other": 0.0
                },
                alert_triggered=False,
                recommended_action="Monitor"
            )
            reports.append(report)
        return reports

    def decompose_decay_source(self, current_delta: float, slippage_factor: float = 0.25, 
                              adverse_selection_factor: float = 0.30, other_factor: float = 0.45) -> Dict[str, float]:
        """
        Decompose total decay into specific source components.
        
        :param current_delta: Total difference between paper and live alpha.
        :param slippage_factor: Weight for execution slippage attribution.
        :param adverse_selection_factor: Weight for market movement attribution.
        :param other_factor: Weight for miscellaneous fees or latency issues.
        """
        total_delta = abs(current_delta)
        
        return {
            "slippage": total_delta * slippage_factor,
            "adverse_selection": total_delta * adverse_selection_factor,
            "other": total_delta * other_factor
        }

    def identify_alerts(self, threshold_pct: float = 0.15) -> List[DecayAnalysisResult]:
        """
        Identify instances where decay significantly deviates from research expectation.
        
        :param threshold_pct: Percentage deviation from expected decay to trigger alert (0.15).
        """
        alerts = []
        for report in self.rolling_window_comparison():
            deviation = abs(report.actual_decay_pct - self.expected_decay_rate) / self.expected_decay_rate
            
            # Determine specific sources for the deviation if alerted
            if deviation > threshold_pct:
                source_breakdown = self.decompose_decay_source(report.actual_decay_pct)
                
                alert_report = DecayAnalysisResult(
                    timestamp=report.timestamp,
                    paper_alpha=report.paper_alpha,
                    live_alpha=report.live_alpha,
                    actual_decay_pct=report.actual_decay_pct,
                    expected_decay_pct=self.expected_decay_rate,
                    decomposition=source_breakdown,
                    alert_triggered=True,
                    recommended_action="Investigate Market Regime"
                )
                alerts.append(alert_report)
        return alerts

    def get_latest_state(self) -> Optional[DecayAnalysisResult]:
        """
        Return the most recent analysis result including source decomposition.
        
        :return: Latest analysis or None if no data exists.
        """
        if not self.signal_history:
            return None
            
        latest_signal = self.signal_history[-1]
        paper_alpha, live_alpha = latest_signal[1], latest_signal[2]
        
        decay_pct = 1 - (live_alpha / paper_alpha) if paper_alpha != 0 else 0
        
        # Decompose the current state for better insight
        source_breakdown = self.decompose_decay_source(decay_pct)
        
        alerts = self.identify_alerts()
        triggered_report = None
        
        for report in alerts:
            if report.alert_triggered:
                triggered_report = report
                break
        
        if triggered_report:
            return triggered_report
            
        default_report = DecayAnalysisResult(
            timestamp=datetime.now(),
            paper_alpha=paper_alpha,
            live_alpha=live_alpha,
            actual_decay_pct=decay_pct,
            expected_decay_pct=self.expected_decay_rate,
            decomposition=source_breakdown,
            alert_triggered=False,
            recommended_action="Continue Standard Trading"
        )
        return default_report
```<|endoftext|><|im_start|>user