# antigravity_harness/signal_physics.py
import pandas as pd
from scipy.stats import entropy


class SignalPhysicist:
    @staticmethod
    def calculate_shannon_entropy(signal_series: pd.Series) -> float:
        value_counts = signal_series.value_counts()
        probabilities = value_counts / len(signal_series)
        return entropy(probabilities, base=2)

    @staticmethod
    def vet_signal(signal_series: pd.Series, threshold_entropy: float = 0.9) -> bool:
        h = SignalPhysicist.calculate_shannon_entropy(signal_series)
        if h > threshold_entropy:
            print(f"🗑️ [NOISE] Signal Entropy {h:.2f} > {threshold_entropy}. REJECTED.")
            return False
        return True
