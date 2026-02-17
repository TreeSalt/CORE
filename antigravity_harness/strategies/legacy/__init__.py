"""
antigravity_harness/strategies/legacy/__init__.py
==================================================
Legacy strategies package. 

All strategies here use deprecated base classes. 
Provided for regression testing and comparison only.
"""
from .v050_trend_momentum import V050TrendMomentum

__all__ = ["V050TrendMomentum"]
