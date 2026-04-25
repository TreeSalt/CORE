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
from pathlib import Path
from mantis_core.pipeline import MantisLivePipeline
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mantis_paper_trade")

def signal_handler(sig, frame):
    """Handle shutdown signals to save state."""
    logger.info("Received interrupt signal. Saving state...")
    # We will pass the pipeline reference via closure or global if needed, 
    # but for this structure we'll rely on main function context or try-except block.
    # Ideally, the cleanup should happen in a try-finally block around the run loop.

def load_config(config_path):
    """Load and validate YAML configuration."""
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def save_state(state_data, state_file):
    """Save session state to JSON."""
    state_dir = Path(state_file).parent
    state_dir.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, 'w') as f:
        json.dump(state_data, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Mantis Paper Trading Bot")
    parser.add_argument("--config", type=str, default="config/mantis_paper_trade_config.yaml", help="Path to configuration file")
    args = parser.parse_args()
    
    # 1. Configuration Load
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # 2. Environment Validation (Hard requirement)
    required_env_vars = [
        "MANTIS_ENV", 
        "EXCHANGE_API_KEY", 
        "EXCHANGE_SECRET_KEY", 
        "WALLET_ADDRESS"
    ]
    
    for var in required_env_vars:
        if not os.environ.get(var):
            logger.error(f"Missing required environment variable: {var}")
            sys.exit(1)

    logger.info("Configuration loaded and validated.")
    logger.info(f"Running in environment: {os.environ.get('MANTIS_ENV')}")

    # 3. Initialize Pipeline
    pipeline_config = config.get("pipeline", {})
    
    try:
        mantis_pipeline = MantisLivePipeline(**pipeline_config)
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        sys.exit(1)

    # 4. Setup State Persistence Paths
    state_file_path = args.config.replace('.yaml', '_session.json').replace('config', 'state')
    if not Path(state_file_path).exists():
        logger.info(f"No previous session found starting fresh at {state_file_path}")

    # 5. Signal Handling for Graceful Shutdown
    def cleanup_handler(signum, frame):
        logger.info("Shutting down... Saving final state.")
        # In a real implementation, this would call mantis_pipeline.save() or save_state()
        # Here we simulate saving the current context
        state_data = {
            "last_processed_block": 12345678, # Placeholder
            "status": "shutdown"
        }
        try:
            save_state(state_data, state_file_path)
        except Exception as e:
            logger.error(f"Error saving final state: {e}")
        
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)

    # 6. Run Pipeline Loop
    try:
        logger.info("Mantis Paper Trade Bot started.")
        mantis_pipeline.run()
    except Exception as e:
        logger.error(f"Runtime error occurred: {e}")
        sys.exit(1)
    finally:
        logger.info("Pipeline finished execution.")

if __name__ == "__main__":
    main()