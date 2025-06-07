#!/usr/bin/env python3
"""
Simple test script to check route accessibility
"""

import requests
import sys

def test_route(url, description):
    """Test a single route and print result"""
    try:
        print(f"Testing {description}: {url}")
        response = requests.get(url, timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 404:
            print(f"  ❌ Route not found")
        elif response.status_code == 200:
            print(f"  ✅ Route accessible")
        elif response.status_code == 500:
            print(f"  ⚠️ Server error")
        else:
            print(f"  ? Unexpected status: {response.status_code}")
        print()
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed: {e}")
        print()
        return 0

def main():
    """Test key routes"""
    base_url = "http://localhost:8003"
    
    routes_to_test = [
        ("/", "Home page"),
        ("/users/list", "Users list"),
        ("/buildings/list", "Buildings list"),
        ("/api/buildings", "API Buildings"),
        ("/tickets/tech/new", "Tech tickets"),
    ]
    
    print("🔍 Testing route accessibility...")
    print("=" * 50)
    
    for route, description in routes_to_test:
        url = f"{base_url}{route}"
        test_route(url, description)

if __name__ == "__main__":
    main()
