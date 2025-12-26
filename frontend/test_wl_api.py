"""Manual utility for inspecting the Wiener Linien realtime API.

This module is intentionally excluded from the automated test suite; run it
directly to debug the public API:

    python -m frontend.test_wl_api
"""

from __future__ import annotations

import json

import requests

API_URL = "https://www.wienerlinien.at/ogd_realtime/monitor"


def main() -> None:
    rbl = "3043"
    params = {"rbl": rbl}

    print(f"Testing Wiener Linien API with RBL: {rbl}")
    print("=" * 60)
    print(f"Requesting: {API_URL} with params {params}")

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        print(f"Status code: {response.status_code}")
    except requests.RequestException as exc:  # pragma: no cover - manual tool
        print(f"Request failed: {exc}")
        return

    if response.status_code != 200:
        print(f"HTTP Error: {response.status_code}")
        print("Response text (first 500 chars):")
        print(response.text[:500])
        return

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:  # pragma: no cover - manual tool
        print(f"Error parsing JSON: {exc}")
        print("Response text (first 500 chars):")
        print(response.text[:500])
        return

    print(f"Response keys: {list(payload.keys())}")
    monitors = payload.get("data", {}).get("monitors", [])
    print(f"Found {len(monitors)} monitors")

    for i, monitor in enumerate(monitors):
        location = monitor.get("locationStop", {})
        title = location.get("properties", {}).get("title", "Unknown")
        coords = location.get("geometry", {}).get("coordinates", [])
        print(f"\n--- Monitor {i + 1} ---")
        print(f"Stop: {title}")
        print(f"Coordinates: {coords}")

        for j, line in enumerate(monitor.get("lines", [])):
            print(
                f"\n  Line {j + 1}: {line.get('name', 'N/A')} towards {line.get('towards', 'N/A')}"
            )
            print(f"  Type: {line.get('type', 'unknown')}")

            departures = line.get("departures", {}).get("departure", [])
            print(f"  Departures: {len(departures)}")
            for k, departure in enumerate(departures):
                dep_time = departure.get("departureTime", {})
                print(f"\n    Departure {k + 1}:")
                print(f"      Planned: {dep_time.get('timePlanned', 'N/A')}")
                print(f"      Real: {dep_time.get('timeReal', 'N/A')}")
                print(f"      Countdown: {dep_time.get('countdown', 'N/A')}")

                vehicle = departure.get("vehicle", {})
                if vehicle:
                    print(f"      Vehicle: {vehicle.get('name', 'N/A')}")
                    print(f"      Towards: {vehicle.get('towards', 'N/A')}")
                    print(f"      Direction: {vehicle.get('direction', 'N/A')}")
                    print(f"      Type: {vehicle.get('type', 'N/A')}")

    print("\n" + "=" * 60)
    print("Testing complete!")


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
