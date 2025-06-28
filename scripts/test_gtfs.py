import os
import sys
from pathlib import Path

print("Test GTFS script started")

# Configuration
GTFS_URL = "https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip"
DATA_DIR = Path(__file__).parent.parent / "frontend" / "data"
GTFS_DIR = Path(__file__).parent / "gtfs_data"

print(f"DATA_DIR: {DATA_DIR}")
print(f"GTFS_DIR: {GTFS_DIR}")

# Ensure directories exist
print("Creating directories...")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GTFS_DIR, exist_ok=True)
print("Directories created")

# Test file writing
try:
    test_file = DATA_DIR / "test_file.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Test successful!")
    print(f"Successfully wrote to {test_file}")
except Exception as e:
    print(f"Error writing test file: {e}")

print("Test GTFS script completed")
