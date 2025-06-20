import requests
import json

API_URL = "https://www.wienerlinien.at/ogd_realtime/monitor"

# Test with RBL 3043 which returned data
rbl = '3043'
params = {'rbl': rbl}

print(f"Testing Wiener Linien API with RBL: {rbl}")
print("=" * 60)

print(f"Requesting: {API_URL} with params {params}")
try:
    response = requests.get(API_URL, params=params, timeout=10)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'data' in data and 'monitors' in data['data']:
                monitors = data['data']['monitors']
                print(f"Found {len(monitors)} monitors")
                
                for i, monitor in enumerate(monitors):
                    print(f"\n--- Monitor {i+1} ---")
                    print(f"Stop: {monitor['locationStop']['properties']['title']}")
                    print(f"Coordinates: {monitor['locationStop']['geometry']['coordinates']}")
                    
                    if 'lines' in monitor:
                        print(f"Lines: {len(monitor['lines'])}")
                        for j, line in enumerate(monitor['lines']):
                            print(f"\n  Line {j+1}: {line['name']} towards {line['towards']}")
                            print(f"  Type: {line.get('type', 'unknown')}")
                            
                            if 'departures' in line and 'departure' in line['departures']:
                                departures = line['departures']['departure']
                                print(f"  Departures: {len(departures)}")
                                
                                for k, departure in enumerate(departures):
                                    print(f"\n    Departure {k+1}:")
                                    print(f"      Planned: {departure['departureTime']['timePlanned']}")
                                    print(f"      Real: {departure['departureTime']['timeReal']}")
                                    print(f"      Countdown: {departure['departureTime']['countdown']}")
                                    
                                    if 'vehicle' in departure:
                                        vehicle = departure['vehicle']
                                        print(f"      Vehicle: {vehicle.get('name', 'N/A')}")
                                        print(f"      Towards: {vehicle.get('towards', 'N/A')}")
                                        print(f"      Direction: {vehicle.get('direction', 'N/A')}")
                                        print(f"      Type: {vehicle.get('type', 'N/A')}")
                                        print(f"      ID: {vehicle.get('id', 'N/A')}")
                                        print(f"      Latitude: {vehicle.get('latitude', 'N/A')}")
                                        print(f"      Longitude: {vehicle.get('longitude', 'N/A')}")
                                        print(f"      Heading: {vehicle.get('direction', 'N/A')}")
                            else:
                                print("  No departures data")
                    else:
                        print("  No lines data")
            else:
                print("No 'monitors' key in data")
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("Response text (first 500 chars):")
            print(response.text[:500])
    else:
        print(f"HTTP Error: {response.status_code}")
        print("Response text (first 500 chars):")
        print(response.text[:500])
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")

print("\n" + "=" * 60)
print("Testing complete!")
