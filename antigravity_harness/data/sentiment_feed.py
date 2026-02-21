import pandas as pd
import numpy as np

class SentimentFeed:
    """
    Feeds auxiliary sentiment data into the TRADER_OPS physics engine context.
    Expects a pandas Series aligned to the main price asset index, with scores from -1.0 to 1.0.
    """
    def __init__(self, data: pd.Series):
        if not isinstance(data, pd.Series):
            raise ValueError("SentimentFeed requires a pandas Series")
        self.data = data
        
    def inject_to_context(self, context) -> None:
        """Injects this feed into a generic context.intelligence dictionary."""
        if not hasattr(context, "intelligence") or context.intelligence is None:
            context.intelligence = {}
        context.intelligence["sentiment"] = self.data
