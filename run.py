#!/usr/bin/env python3
"""Development entry point for Schmagent."""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_api_keys():
    """Check if API keys file exists."""
    secrets_path = os.getenv("SECRETS_PATH", os.path.expanduser("~/.secrets/schmagent"))
    api_keys_file = os.path.join(secrets_path, os.getenv("API_KEYS_FILE", "api_keys.json"))
    return os.path.exists(api_keys_file)

if __name__ == "__main__":
    # Detect Cursor IDE environment by checking for encodings import issue
    cursor_environment = False
    try:
        import encodings
        logger.debug("Encodings module imported successfully")
    except ImportError:
        logger.info("Encodings module import failed - likely running in Cursor IDE")
        cursor_environment = True

    # Check for API keys before proceeding
    if not check_api_keys():
        logger.error("API keys file not found. Please set up your API keys.")
        sys.exit(1)

    # Handle execution based on environment
    if cursor_environment:
        # In Cursor IDE: use the shell script workaround
        logger.info("Running in Cursor environment, using shell script workaround")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        run_script = os.path.join(script_dir, "run_unified.sh")
        os.chmod(run_script, 0o755)
        result = subprocess.call([run_script])
        sys.exit(result)
    else:
        # In normal environment: import and run the main function directly
        logger.info("Running in normal environment, importing main directly")
        try:
            # Try to import from main.py first
            try:
                from schmagent.main import main
                logger.info("Imported main from schmagent.main")
            except ImportError:
                # Fall back to __main__.py if main.py is not found
                from schmagent.__main__ import main
                logger.info("Imported main from schmagent.__main__")
            
            sys.exit(main())
        except ImportError as e:
            logger.error(f"Failed to import schmagent main module: {e}")
            logger.error("Make sure the schmagent package is in your PYTHONPATH")
            logger.error("Try running: export PYTHONPATH=$PYTHONPATH:$(pwd)")
            sys.exit(1)
