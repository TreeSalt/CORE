---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import sys
import time
import logging
import argparse
import signal
from pathlib import Path
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.physics.trend_signal import TrendSignalGenerator
from mantis_core.risk.position_sizer import PositionSizer
from mantis_core.pipeline import MantisLivePipeline


def validate_environment() -> bool:
    """Check that required environment variables are set and valid."""
    env_vars = ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'MANTIS_ENV']

    for var in env_vars:
        value = os.environ.get(var)
        if not value:
            logging.warning(f"Missing environment variable: {var}")
            return False

    if os.environ.get('MANTIS_ENV') != 'paper':
        logging.error("MANTIS_ENV must be 'paper' for paper trading mode")
        return False

    return True


def build_pipeline(equity: float) -> MantisLivePipeline:
    """Instantiate all components and inject them into a new MantisLivePipeline."""
    regime_detector = RegimeDetector()
    trend_signal_generator = TrendSignalGenerator()
    position_sizer = PositionSizer()

    pipeline = MantisLivePipeline(
        regime_detector=regime_detector,
        signal_generator=trend_signal_generator,
        position_sizer=position_sizer,
        equity=equity
    )

    return pipeline


def main() -> int:
    """CLI entry point for the MANTIS paper trading launcher."""
    parser = argparse.ArgumentParser(description='MANTIS Paper Trading Launcher')
    parser.add_argument('--equity', type=float, default=10000.0, help='Starting equity')
    parser.add_argument('--symbol', type=str, default='BTC/USD', help='Trading symbol')
    parser.add_argument('--interval', type=int, default=60, help='Tick interval in seconds')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s UTC] %(levelname)s: %(message)s'
    )
    logger = logging.getLogger(__name__)

    if not validate_environment():
        logger.error("Environment validation failed")
        return 1

    pipeline = build_pipeline(args.equity)

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting MANTIS paper trading loop")
    logger.info(f"Symbol: {args.symbol}, Interval: {args.interval}s, Equity: ${args.equity}")

    while True:
        try:
            result = pipeline.tick(symbol=args.symbol)
            if result:
                logger.info(
                    f"Tick - Regime: {result.regime}, "
                    f"Signal: {result.signal_action}, "
                    f"Position Qty: {result.position_quantity}"
                )
        except Exception as e:
            logger.error(f"Tick failed: {e}")

        time.sleep(args.interval)

    return 0


if __name__ == '__main__':
    sys.exit(main())
```