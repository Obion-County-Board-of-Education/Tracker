#!/usr/bin/env python3
"""
Test to check which routes are actually registered
"""

import requests
import sys

def test_routes():
    """Test various routes to see which ones exist"""
    base_url = "http://localhost:8000"
    
    routes_to_test = [
        "/",
        "/users",
        "/users/list", 
        "/buildings",
        "/buildings/list",
        "/users/add",
        "/buildings/add"
    ]
    
    print("🧪 Testing route availability:")
    print("=" * 40)
    
    for route in routes_to_test:
        url = f"{base_url}{route}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                status = "✅ 200 OK"
            elif response.status_code == 302:
                redirect_location = response.headers.get('Location', 'unknown')
                status = f"🔄 302 Redirect to {redirect_location}"
            elif response.status_code == 404:
                status = "❌ 404 Not Found"
            else:
                status = f"⚠️  {response.status_code}"
            
            print(f"{route:20} -> {status}")
            
        except requests.exceptions.RequestException as e:
            print(f"{route:20} -> ❌ Connection Error: {e}")

if __name__ == "__main__":
    test_routes()
