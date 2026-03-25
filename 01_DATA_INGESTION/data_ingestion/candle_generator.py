"""Synthetic candle generator for backtesting and stress testing."""
import random
import time


def _make_candle(ts, o, h, l, c, v):
    return {"timestamp": ts, "open": round(o, 2), "high": round(h, 2),
            "low": round(l, 2), "close": round(c, 2), "volume": round(v, 2)}


def generate_trending(n, start_price=100.0, drift_pct=0.1, noise_pct=0.5, seed=None):
    if seed is not None:
        random.seed(seed)
    candles = []
    price = start_price
    ts = int(time.time()) - n * 60
    for i in range(n):
        drift = price * drift_pct / 100
        noise = price * noise_pct / 100 * (random.random() * 2 - 1)
        c = price + drift + noise
        h = max(price, c) * (1 + random.random() * noise_pct / 200)
        l = min(price, c) * (1 - random.random() * noise_pct / 200)
        vol = random.uniform(100, 1000)
        candles.append(_make_candle(ts + i * 60, price, h, l, c, vol))
        price = c
    return candles


def generate_mean_reverting(n, center_price=100.0, amplitude_pct=5.0, noise_pct=0.5, seed=None):
    if seed is not None:
        random.seed(seed)
    candles = []
    price = center_price
    ts = int(time.time()) - n * 60
    for i in range(n):
        reversion = (center_price - price) * 0.1
        noise = center_price * noise_pct / 100 * (random.random() * 2 - 1)
        amplitude = center_price * amplitude_pct / 100 * (random.random() * 2 - 1) * 0.3
        c = price + reversion + noise + amplitude
        h = max(price, c) * (1 + random.random() * 0.005)
        l = min(price, c) * (1 - random.random() * 0.005)
        vol = random.uniform(100, 1000)
        candles.append(_make_candle(ts + i * 60, price, h, l, c, vol))
        price = c
    return candles


def generate_volatile(n, start_price=100.0, volatility_pct=3.0, seed=None):
    if seed is not None:
        random.seed(seed)
    candles = []
    price = start_price
    ts = int(time.time()) - n * 60
    for i in range(n):
        move = price * volatility_pct / 100 * (random.random() * 2 - 1)
        c = price + move
        h = max(price, c) * (1 + random.random() * volatility_pct / 100)
        l = min(price, c) * (1 - random.random() * volatility_pct / 100)
        vol = random.uniform(500, 5000)
        candles.append(_make_candle(ts + i * 60, price, h, l, c, vol))
        price = c
    return candles


def generate_flash_crash(n, start_price=100.0, crash_bar=50, crash_pct=30.0, recovery_bars=20, seed=None):
    if seed is not None:
        random.seed(seed)
    candles = []
    price = start_price
    ts = int(time.time()) - n * 60
    for i in range(n):
        if i == crash_bar:
            c = price * (1 - crash_pct / 100)
            l = c * 0.98
            h = price
        elif crash_bar < i <= crash_bar + recovery_bars:
            recovery_target = start_price * 0.9
            recovery_step = (recovery_target - price) / max(1, crash_bar + recovery_bars - i)
            noise = price * 0.005 * (random.random() * 2 - 1)
            c = price + recovery_step + noise
            h = max(price, c) * 1.005
            l = min(price, c) * 0.995
        else:
            noise = price * 0.003 * (random.random() * 2 - 1)
            c = price + noise
            h = max(price, c) * 1.002
            l = min(price, c) * 0.998
        vol = random.uniform(100, 1000) * (10 if i == crash_bar else 1)
        candles.append(_make_candle(ts + i * 60, price, h, l, c, vol))
        price = c
    return candles
