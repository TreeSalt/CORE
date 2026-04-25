---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import argparse
import yaml
import logging
import signal
import sys
import os
import json
from pathlib import Path
from mantis_core.pipeline import MantisLivePipeline


def parse_args():
    parser = argparse.ArgumentParser(description='MANTIS Paper Trading Launcher')
    parser.add_argument('--config', type=str, default='profiles/mantis_paper_btc.yaml', help='Path to YAML config file')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode without executing trades')
    parser.add_argument('--symbol', type=str, help='Trading symbol (e.g., BTC/USD)')
    parser.add_argument('--interval', type=int, help='Data interval in seconds')
    return parser.parse_args()


def load_config(config_path, overrides):
    config_file = Path(config_path)
    if not config_file.exists():
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    for key, value in overrides.items():
        if value is not None:
            config[key] = value
    
    return config


def validate_api_keys():
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or not secret_key:
        logging.error("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY environment variables")
        sys.exit(1)


def signal_handler(sig, frame):
    global shutdown_flag
    shutdown_flag = True
    logging.info("Shutdown signal received. Saving state...")


def save_state(state, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(state, f)
    
    logging.info(f"Final state saved to {output_path}")


def main():
    global shutdown_flag
    shutdown_flag = False
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Parse arguments
    args = parse_args()
    
    # Build overrides from CLI args
    overrides = {
        'symbol': args.symbol,
        'interval': args.interval,
        'dry_run': args.dry_run
    }
    
    # Load and validate config
    config = load_config(args.config, {k: v for k, v in overrides.items() if v is not None})
    validate_api_keys()
    
    # Initialize pipeline
    pipeline = MantisLivePipeline(config=config)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run pipeline loop
    try:
        while not shutdown_flag:
            pipeline.run_step()
    except KeyboardInterrupt:
        logging.info("Shutdown initiated by keyboard interrupt")
    finally:
        # Save final state
        state = pipeline.get_state()
        save_state(state, Path('state/mantis_session.json'))


if __name__ == '__main__':
    main()