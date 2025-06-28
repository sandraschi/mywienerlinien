import os
import logging

# --- Logger Setup ---
LOG_DIR = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, 'smoke_test.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'), # Overwrite for a clean test
        logging.StreamHandler()
    ]
)

logging.info("--- Smoke Test Script Started ---")
logging.info("Logger test successful. If you see this, the environment is working.")
logging.info("--- Smoke Test Script Finished ---")
