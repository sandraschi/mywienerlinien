"""
Debug script for GTFS data processing.
This is a simplified version to help identify where the main script is hanging.
"""
import os
import sys
import time
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Directories
SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_DIR.parent.parent / 'frontend' / 'data'
GTFS_DIR = SCRIPT_DIR / 'gtfs_data'
GTFS_ZIP = GTFS_DIR / 'gtfs.zip'
GTFS_EXTRACT_DIR = GTFS_DIR

def check_directories():
    """Check if required directories exist."""
    logger.info("Checking directories...")
    for dir_path in [DATA_DIR, GTFS_DIR, GTFS_EXTRACT_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  • {dir_path} - {'exists' if dir_path.exists() else 'missing'}")

def check_gtfs_files():
    """Check if GTFS files exist and are valid."""
    logger.info("\nChecking GTFS files...")
    required_files = [
        'stops.txt',
        'routes.txt',
        'trips.txt',
        'stop_times.txt',
        'calendar.txt'
    ]
    
    for file in required_files:
        file_path = GTFS_EXTRACT_DIR / file
        exists = file_path.exists()
        size = file_path.stat().st_size if exists else 0
        logger.info(f"  • {file}: {'found' if exists else 'missing'} ({size} bytes)")

def read_sample_file(filename, lines=5):
    """Read sample lines from a file."""
    file_path = GTFS_EXTRACT_DIR / filename
    if not file_path.exists():
        logger.error(f"  • {filename} does not exist")
        return
        
    logger.info(f"\nSample from {filename}:")
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            # Read header
            header = f.readline().strip()
            logger.info(f"  • Header: {header}")
            
            # Read sample lines
            for i, line in enumerate(f):
                if i >= lines - 1:
                    break
                logger.info(f"  • Line {i+1}: {line.strip()}")
    except Exception as e:
        logger.error(f"  • Error reading {filename}: {e}")

def main():
    """Main function to run debug checks."""
    logger.info("=" * 50)
    logger.info("GTFS Data Debugger")
    logger.info("=" * 50)
    
    # Check directories
    check_directories()
    
    # Check GTFS files
    check_gtfs_files()
    
    # Read sample data from key files
    for file in ['stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt']:
        read_sample_file(file)
    
    logger.info("\nDebug check completed.")

if __name__ == "__main__":
    main()
