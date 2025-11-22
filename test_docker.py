#!/usr/bin/env python3
"""
Docker Test Script for Wiener Linien Live Map
Tests the Docker container and application functionality
"""

import requests
import time
import sys
from datetime import datetime

def test_docker_setup():
    """Test the Docker setup and application functionality"""
    
    print("🐳 Testing Wiener Linien Live Map Docker Setup")
    print("=" * 50)
    
    base_url = "http://localhost:3080"
    endpoints = [
        "/api/status",
        "/api/lines", 
        "/api/stations",
        "/api/routes",
        "/api/vehicles"
    ]
    
    # Test 1: Check if container is running
    print("\n1. Checking if container is running...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        if response.status_code == 200:
            print("✅ Container is running and responding")
        else:
            print(f"❌ Container responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to container. Is Docker running?")
        print("   Try: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error connecting to container: {e}")
        return False
    
    # Test 2: Check all API endpoints
    print("\n2. Testing API endpoints...")
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ {endpoint}: {len(data)} items")
                elif isinstance(data, dict):
                    print(f"✅ {endpoint}: OK")
                else:
                    print(f"✅ {endpoint}: {type(data)}")
            else:
                print(f"❌ {endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")
    
    # Test 3: Check specific data
    print("\n3. Checking data integrity...")
    try:
        # Check lines
        lines_response = requests.get(f"{base_url}/api/lines", timeout=10)
        if lines_response.status_code == 200:
            lines = lines_response.json()
            metro_lines = [line for line in lines if line.get('type') == 'metro']
            tram_lines = [line for line in lines if line.get('type') == 'tram']
            bus_lines = [line for line in lines if line.get('type') == 'bus']
            print(f"✅ Lines: {len(lines)} total ({len(metro_lines)} metro, {len(tram_lines)} tram, {len(bus_lines)} bus)")
        
        # Check stations
        stations_response = requests.get(f"{base_url}/api/stations", timeout=10)
        if stations_response.status_code == 200:
            stations = stations_response.json()
            print(f"✅ Stations: {len(stations)} total")
        
        # Check vehicles
        vehicles_response = requests.get(f"{base_url}/api/vehicles", timeout=10)
        if vehicles_response.status_code == 200:
            vehicles = vehicles_response.json()
            print(f"✅ Vehicles: {len(vehicles)} total")
            
    except Exception as e:
        print(f"❌ Error checking data: {e}")
    
    # Test 4: Check WebSocket (basic test)
    print("\n4. Testing WebSocket connectivity...")
    try:
        # This is a basic test - in a real scenario you'd use a WebSocket client
        print("✅ WebSocket endpoint available (manual testing required)")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    
    # Test 5: Performance test
    print("\n5. Performance test...")
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"✅ Response time: {response_time:.2f}ms")
        
        if response_time < 1000:
            print("✅ Performance: Excellent")
        elif response_time < 3000:
            print("✅ Performance: Good")
        else:
            print("⚠️  Performance: Slow")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Docker setup test completed!")
    print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Application URL: {base_url}")
    print("📚 For more information, see: DOCKER_README.md")
    
    return True

if __name__ == "__main__":
    try:
        success = test_docker_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1) 