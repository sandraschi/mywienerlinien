"""
Test script to verify that routes are loaded correctly from all route files.
"""
import os
import sys
import logging
from data_loader import DataLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Test loading routes from all route files."""
    # Initialize the data loader
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    data_loader = DataLoader(data_dir=data_dir)
    
    # Clear any cached data
    data_loader.clear_cache()
    
    # Load all routes
    print("Loading routes...")
    routes = data_loader.load_routes()
    
    # Print summary
    print(f"\nTotal routes loaded: {len(routes)}")
    
    # Group routes by type
    routes_by_type = {}
    for route in routes:
        if route.type not in routes_by_type:
            routes_by_type[route.type] = []
        routes_by_type[route.type].append(route)
    
    # Print routes by type
    for route_type, type_routes in routes_by_type.items():
        print(f"\n{route_type} routes ({len(type_routes)}):")
        for route in sorted(type_routes, key=lambda r: r.line):
            print(f"  - {route.line}: {route.description}")
    
    # Print cache status
    print("\nCache status:")
    for key, value in data_loader.get_cache_status().items():
        if key != 'last_loaded':
            print(f"  - {key}: {value}")

if __name__ == "__main__":
    main()
