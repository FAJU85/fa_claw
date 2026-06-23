"""
Open Claw Headless Daemon - Main Entry Point

This is the main entry point for the Open Claw headless engine.
It integrates with Telegram and Hugging Face APIs.
Groq and OpenRouter integrations are optional and can be added later.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables (only Telegram and Hugging Face are mandatory)
REQUIRED_ENV_VARS = [
    'OPENCLAW_TELEGRAM_BOT_TOKEN',
    'OPENCLAW_HUGGINGFACE_API_KEY'
]

OPTIONAL_ENV_VARS = [
    'OPENCLAW_GROQ_API_KEY',
    'OPENCLAW_OPENROUTER_API_KEY',
    'OPENCLAW_HF_TOKEN'
]

def validate_environment():
    """Validate that all required environment variables are set."""
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    # Log which optional variables are set
    for var in OPTIONAL_ENV_VARS:
        if os.environ.get(var):
            logger.info(f"Optional environment variable {var} is set")
        else:
            logger.info(f"Optional environment variable {var} is not set (will not be available)")
    
    logger.info("All required environment variables are set")
    return True

def initialize_storage():
    """Initialize persistent storage at /data."""
    data_path = Path('/data')
    try:
        data_path.mkdir(parents=True, exist_ok=True)
        # Test write access
        test_file = data_path / '.write_test'
        test_file.write_text('test')
        test_file.unlink()
        logger.info(f"Persistent storage initialized at {data_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize storage at {data_path}: {e}")
        return False

def main():
    """Main entry point for the Open Claw daemon."""
    logger.info("Starting Open Claw Headless Daemon...")
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Initialize storage
    if not initialize_storage():
        sys.exit(1)
    
    # Log successful initialization
    logger.info("Open Claw Headless Daemon initialized successfully")
    logger.info("Required integrations: Telegram Bot, Hugging Face")
    logger.info("Optional integrations (not configured): Groq, OpenRouter")
    logger.info("Waiting for incoming requests...")
    
    # TODO: Implement actual daemon logic here
    # This could include:
    # - Telegram bot polling or webhook setup
    # - Hugging Face model loading or API setup
    # - Groq API client initialization (when key is provided)
    # - OpenRouter API client initialization (when key is provided)
    
    # Keep the daemon running
    try:
        while True:
            # Placeholder for actual event loop
            pass
    except KeyboardInterrupt:
        logger.info("Shutting down Open Claw Daemon...")
        sys.exit(0)

if __name__ == '__main__':
    main()
