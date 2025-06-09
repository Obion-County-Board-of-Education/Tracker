#!/usr/bin/env python3

import requests
import sys
import os

def test_cycle_import():
    url = "http://localhost:8000/api/tickets/tech/import"
    csv_file = "cycle_test_final.csv"
    
    print(f"Testing complete export-import cycle with {csv_file}...")
    print(f"API endpoint: {url}")
    
    try:
        # Open the CSV file
        with open(csv_file, "rb") as f:
            files = {
                "file": (csv_file, f, "text/csv")
            }
            data = {
                "operation": "append"
            }
            
            print("Sending import request...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result}")
                print(f"Imported count: {result.get('imported_count', 0)}")
                print(f"Errors: {result.get('errors', [])}")
                
                # Show any errors
                if result.get('errors'):
                    print("Errors encountered:")
                    for error in result.get('errors', []):
                        print(f"  - {error}")
            else:
                print(f"Error response: {response.text}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cycle_import()
