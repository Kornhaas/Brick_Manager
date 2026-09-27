#!/usr/bin/env python3
"""Test script for the location editing feature."""

import json

import requests

BASE_URL = "http://127.0.0.1:5001"


def test_update_part_location():
    """Test the update_part_location endpoint."""

    # Test data
    test_data = {
        "part_num": "3001",  # A common LEGO brick
        "location": "A",
        "level": "1",
        "box": "5",
    }

    print("Testing location update endpoint...")
    print(f"Sending data: {json.dumps(test_data, indent=2)}")

    response = requests.post(
        f"{BASE_URL}/update_part_location",
        json=test_data,
        headers={"Content-Type": "application/json"},
    )

    print(f"\nResponse status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response data: {json.dumps(data, indent=2)}")

        if data.get("success"):
            print("✅ Location updated successfully!")
            print(f"New location: {data.get('location')}")
        else:
            print("❌ Update failed:", data.get("message"))
    else:
        print(f"❌ Request failed with status {response.status_code}")
        print(f"Response: {response.text}")


if __name__ == "__main__":
    test_update_part_location()
