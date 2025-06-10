#!/usr/bin/env python3
"""
Debug the import cycle issue
"""
import requests
import json

def clear_existing_tickets():
    """Clear existing tickets for clean test"""
    print("=== Clearing existing tickets ===")
    try:
        response = requests.delete("http://localhost:8000/api/tickets/tech/clear")
        print(f"Clear response: {response.status_code}")
    except Exception as e:
        print(f"Clear error: {e}")

def check_tickets():
    """Check current tickets"""
    print("\n=== Checking current tickets ===")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets = response.json()
            print(f"Found {len(tickets)} tickets")
            for i, ticket in enumerate(tickets[:3]):
                print(f"\nTicket {i+1}:")
                print(f"  ID: {ticket.get('id')}")
                print(f"  Title: '{ticket.get('title')}'")
                print(f"  Description: '{ticket.get('description')}'")
                print(f"  Issue Type: '{ticket.get('issue_type')}'")
                print(f"  School: '{ticket.get('school')}'")
                print(f"  Room: '{ticket.get('room')}'")
                print(f"  Tag: '{ticket.get('tag')}'")
                print(f"  Status: '{ticket.get('status')}'")
                print(f"  Created By: '{ticket.get('created_by')}'")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def test_export_import_ready():
    """Test the import-ready export"""
    print("\n=== Testing import-ready export ===")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech/export?import_ready=true")
        if response.status_code == 200:
            print("Export successful!")
            content = response.text
            print("CSV Content:")
            print(content[:500])
            
            # Save to file for import test
            with open('debug_export_import_ready.csv', 'w') as f:
                f.write(content)
            print("Saved to debug_export_import_ready.csv")
        else:
            print(f"Export failed: {response.status_code}")
    except Exception as e:
        print(f"Export error: {e}")

def test_import_via_api():
    """Test importing directly via API"""
    print("\n=== Testing import via API ===")
    try:
        with open('test_import_cycle.csv', 'rb') as f:
            files = {'file': ('test_import_cycle.csv', f, 'text/csv')}
            data = {'operation': 'append'}
            
            response = requests.post("http://localhost:8000/api/tickets/tech/import", 
                                   files=files, data=data)
            
            print(f"Import Status: {response.status_code}")
            result = response.json()
            print(f"Import Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Import error: {e}")

def main():
    print("🔍 DEBUG IMPORT CYCLE ISSUE")
    print("=" * 50)
    
    # First check current state
    check_tickets()
    
    # Test export functionality
    test_export_import_ready()
    
    # Clear and test import
    clear_existing_tickets()
    test_import_via_api()
    
    # Check results
    check_tickets()

if __name__ == "__main__":
    main()
