#!/usr/bin/env python3
"""
Script to identify stations missing coordinates.
"""
import os
import sys
from data_loader import data_loader

def find_stations_without_coords():
    """Find and print stations that are missing coordinates."""
    # Load all stations
    stations = data_loader.load_stations()
    
    # Find stations without coordinates
    missing_coords = [s for s in stations if s.lat is None or s.lng is None]
    
    # Group by type
    by_type = {}
    for station in missing_coords:
        by_type.setdefault(station.type, []).append(station)
    
    # Print summary
    print(f"Found {len(missing_coords)} stations without coordinates out of {len(stations)} total stations")
    print("\nBreakdown by type:")
    for stype, stns in by_type.items():
        print(f"- {stype}: {len(stns)} stations")
    
    # Print details
    print("\nStations without coordinates:")
    for stype, stns in by_type.items():
        print(f"\n{stype}:")
        for station in stns:
            print(f"  - {station.name} (RBL: {station.rbl or 'N/A'})")

if __name__ == "__main__":
    find_stations_without_coords()
