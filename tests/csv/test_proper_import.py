#!/usr/bin/env python3

import requests
import json

def test_proper_import():
    """Test importing a properly formatted CSV"""
    
    print("=== Testing Proper CSV Import ===")
    
    # Clear existing tickets first
    print("1. Clearing existing tickets...")
    try:
        response = requests.delete("http://localhost:8000/api/tickets/tech/clear")
        print(f"Clear response: {response.status_code}")
    except Exception as e:
        print(f"Clear error: {e}")
    
    # Import the properly formatted CSV
    print("\n2. Importing properly formatted CSV...")
    try:
        with open('proper_import_test.csv', 'rb') as f:
            files = {'file': ('proper_import_test.csv', f, 'text/csv')}
            data = {'operation': 'overwrite'}
            
            response = requests.post("http://localhost:8000/api/tickets/tech/import", 
                                   files=files, data=data)
            
            print(f"Import Status: {response.status_code}")
            result = response.json()
            print(f"Import Result: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print(f"✅ Successfully imported {result.get('imported_count')} tickets")
                if result.get('errors'):
                    print(f"⚠️ Errors: {result.get('errors')}")
            else:
                print("❌ Import failed")
                return
                
    except Exception as e:
        print(f"❌ Import error: {e}")
        return
    
    # Check the imported tickets
    print("\n3. Checking imported tickets...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets = response.json()
            print(f"Total tickets: {len(tickets)}")
            
            for i, ticket in enumerate(tickets):
                print(f"\nTicket {i+1} (ID: {ticket.get('id')}):")
                print(f"  Title: '{ticket.get('title')}'")
                print(f"  Description: '{ticket.get('description')}'")
                print(f"  School: '{ticket.get('school')}'")
                print(f"  Room: '{ticket.get('room')}'")
                print(f"  Issue Type: '{ticket.get('issue_type')}'")
                print(f"  Tag: '{ticket.get('tag')}'")
                print(f"  Status: '{ticket.get('status')}'")
                print(f"  Created By: '{ticket.get('created_by')}'")
        else:
            print(f"❌ Failed to get tickets: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting tickets: {e}")

if __name__ == "__main__":
    test_proper_import()
