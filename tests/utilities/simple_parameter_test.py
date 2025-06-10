#!/usr/bin/env python3
"""
Simple test to check if import_ready parameter works
"""
import requests

def test_parameter():
    base_url = "http://localhost:8000"
    
    print("Testing regular export (should include id, created_at, updated_at):")
    response = requests.get(f"{base_url}/api/tickets/tech/export")
    if response.status_code == 200:
        lines = response.text.strip().split('\n')
        headers = lines[0]
        print(f"Headers: {headers}")
        print(f"Has 'id': {'id' in headers}")
        print(f"Has 'created_at': {'created_at' in headers}")
        print(f"Has 'updated_at': {'updated_at' in headers}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    print("\nTesting import-ready export (should exclude id, created_at, updated_at):")
    response = requests.get(f"{base_url}/api/tickets/tech/export?import_ready=true")
    if response.status_code == 200:
        lines = response.text.strip().split('\n')
        headers = lines[0]
        print(f"Headers: {headers}")
        print(f"Has 'id': {'id' in headers}")
        print(f"Has 'created_at': {'created_at' in headers}")
        print(f"Has 'updated_at': {'updated_at' in headers}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_parameter()
