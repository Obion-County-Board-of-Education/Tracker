#!/usr/bin/env python3
print("Python is working!")
import requests
print("Requests library is available")
print("Starting API test...")

try:
    response = requests.get("http://localhost:8000/api/tickets/tech", timeout=5)
    print(f"API response status: {response.status_code}")
except Exception as e:
    print(f"API connection error: {e}")
