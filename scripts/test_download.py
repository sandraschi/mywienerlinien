"""Simple script to test GTFS data download."""

import urllib.request
import os
from pathlib import Path

def main():
    print("Starting download test...")
    
    # Configuration
    url = "https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip"
    output_dir = Path(__file__).parent / "gtfs_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "gtfs_test.zip"
    
    print(f"Downloading {url} to {output_file}")
    
    try:
        # Download with timeout
        urllib.request.urlretrieve(url, output_file, timeout=30)
        print(f"Successfully downloaded {output_file}")
        print(f"File size: {output_file.stat().st_size / (1024*1024):.2f} MB")
        return 0
    except Exception as e:
        print(f"Error downloading file: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
