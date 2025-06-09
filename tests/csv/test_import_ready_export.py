#!/usr/bin/env python3

import requests
import sys

def test_import_ready_export():
    """Test the import-ready export functionality"""
    
    # Test with import_ready=true
    print("Testing import-ready export...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech/export?import_ready=true")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Save to file
            with open("test_import_ready.csv", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # Show first few lines
            lines = response.text.split('\n')[:5]
            print("First 5 lines of CSV:")
            for i, line in enumerate(lines):
                print(f"{i+1}: {line}")
                
            # Check headers
            if lines:
                headers = lines[0].split(',')
                print(f"\nHeaders found: {headers}")
                if 'id' in headers:
                    print("❌ ERROR: 'id' found in headers - import_ready parameter not working!")
                else:
                    print("✅ SUCCESS: 'id' not found in headers - import_ready working!")
        else:
            print(f"❌ ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_import_ready_export()
