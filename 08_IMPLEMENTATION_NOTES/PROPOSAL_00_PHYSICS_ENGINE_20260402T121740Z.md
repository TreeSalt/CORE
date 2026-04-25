---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import sys
import signal
import argparse
import logging
from pathlib import Path
import yaml
from mantis_core.pipeline import MantisLivePipeline

def main():
    # 1. Parse Command Line Arguments
    parser = argparse.ArgumentParser(description="Run Live Trading Strategy")
    parser.add_argument('--config', type=str, required=True, help='Path to YAML config file')
    parser.add_argument('--symbol', type=str, help='Override symbol in config (e.g., AAPL)')
    args = parser.parse_args()

    # 2. Load Configuration from YAML
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            logging.error(f"Config file not found: {config_path}")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        sys.exit(1)

    # Override symbol if provided via CLI (CLI takes precedence)
    if args.symbol:
        if 'symbols' in config and isinstance(config['symbols'], list):
            config['symbols'] = [args.symbol]
        elif 'symbol' in config:
            config['symbol'] = args.symbol

    # 3. Validate Environment Variables (ALPACA credentials)
    os_module = __import__('os')
    api_key = os_module.environ.get('ALPACA_API_KEY')
    secret_key = os_module.environ.get('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        logging.error("Environment variables ALPACA_API_KEY and ALPACA_SECRET_KEY must be set.")
        sys.exit(1)

    # Add keys to config for pipeline initialization if needed, assuming pipeline reads env or accepts them
    # Typically Mantis pipelines read from env directly, but let's ensure they are available in context if passed
    config['alpaca_api_key'] = api_key
    config['alpaca_secret_key'] = secret_key

    # 4. Initialize Pipeline
    try:
        pipeline = MantisLivePipeline(**config)
    except TypeError as e:
        logging.error(f"Failed to initialize MantisLivePipeline with provided config: {e}")
        sys.exit(1)

    # 5. Handle Interrupt Signal (Ctrl+C)
    def handle_sigint(signum, frame):
        logging.info("Interrupt signal received. Saving state and exiting...")
        save_session_state(pipeline)
        pipeline.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    # 6. Run Pipeline Loop
    try:
        logging.info("Starting Live Trading Pipeline...")
        pipeline.run()
    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        save_session_state(pipeline)
        sys.exit(1)
    finally:
        # Save state on normal exit too
        save_session_state(pipeline)

def save_session_state(pipeline):
    json_module = __import__('json')
    save_dir = Path('state')
    save_dir.mkdir(exist_ok=True, parents=True)
    save_path = save_dir / 'mantis_session.json'
    
    # Attempt to retrieve a serializable state. 
    # Assuming pipeline has a .get_state() or exposes config/logs.
    # If not, we serialize the most recent configuration/context as a fallback.
    try:
        session_data = pipeline.get_state() if hasattr(pipeline, 'get_state') else {}
    except:
        session_data = {}

    # Merge config if not in state for better traceability
    if hasattr(pipeline, 'config'):
        session_data['last_config'] = pipeline.config
    
    with open(save_path, 'w') as f:
        json_module.dump(session_data, f, indent=2, default=str)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()