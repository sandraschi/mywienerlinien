import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# --- Test Script ---
# This script tests ONLY the logger configuration from the failing scripts.

# --- Logger Setup ---
LOG_DIR = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, 'logger_test_v2.log')

# Create logger
logger = logging.getLogger('ComplexLoggerTest')
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers
if logger.handlers:
    logger.handlers = []

# File handler with error reporting
try:
    file_handler = RotatingFileHandler(log_file, mode='w', maxBytes=1024, backupCount=1)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    # If this fails, print to stderr, which might be captured by the runner.
    print(f"CRITICAL_ERROR: Failed to configure file handler: {e}", file=sys.stderr)
    # Also try to log to a fallback file.
    with open(os.path.join(LOG_DIR, 'logger_fallback_error.log'), 'w') as f_err:
        f_err.write(f"Failed to configure RotatingFileHandler: {e}")
    sys.exit(1) # Exit with an error code

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

logger.info("--- Complex Logger Test Started ---")
logger.info("Logger test successful. If you see this, the getLogger/addHandler pattern is working.")
logger.warning("This is a test warning.")
logger.debug("This is a test debug message (should only be in the file).")
logger.info("--- Complex Logger Test Finished ---")
