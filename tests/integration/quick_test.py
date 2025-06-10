#!/usr/bin/env python3
import requests
import sys

def test_routes():
    base_url = "http://localhost:8003"
    routes = ["/users", "/users/list", "/buildings", "/buildings/list"]
    
    for route in routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            print(f"{route}: {response.status_code}")
            if response.status_code in [302]:
                print(f"  -> Redirects to: {response.headers.get('location', 'unknown')}")
        except Exception as e:
            print(f"{route}: ERROR - {e}")

if __name__ == "__main__":
    test_routes()
