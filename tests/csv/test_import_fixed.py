#!/usr/bin/env python3

import requests
import sys
import os

def test_import():
    url = "http://localhost:8000/api/tickets/tech/import"
    csv_file = "manual_test_import.csv"
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file {csv_file} not found")
        return
    
    print(f"Testing fixed import function with {csv_file}...")
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
            
            print("Sending request...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result}")
                print(f"Imported count: {result.get('imported_count', 0)}")
                print(f"Errors: {result.get('errors', [])}")
            else:
                print(f"Error response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Is the server running?")
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_import()
