from .base import BaseStrategy
class v032_simple(BaseStrategy): # This name looks the same but we'll try to register it
    def generate_signals(self, df): return df['Close'] * 0
