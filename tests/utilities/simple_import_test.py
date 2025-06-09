#!/usr/bin/env python3

import requests

def test_csv_import():
    """Test CSV import functionality"""
    
    print("Testing CSV import with debug file...")
    
    try:
        with open('debug_import_test.csv', 'rb') as f:
            files = {'file': ('debug_import_test.csv', f, 'text/csv')}
            data = {'operation': 'append'}
            
            response = requests.post("http://localhost:8000/api/tickets/tech/import", 
                                   files=files, data=data)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("Import successful!")
                
                # Check the most recent tickets
                print("\nChecking most recent tickets...")
                response = requests.get("http://localhost:8000/api/tickets/tech")
                if response.status_code == 200:
                    tickets = response.json()
                    recent_tickets = tickets[:2]
                    
                    for i, ticket in enumerate(recent_tickets):
                        print(f"\nTicket {i+1}:")
                        print(f"  Title: '{ticket.get('title')}'")
                        print(f"  Description: '{ticket.get('description')}'")
                        print(f"  School: '{ticket.get('school')}'")
                        print(f"  Room: '{ticket.get('room')}'")
                        print(f"  Issue Type: '{ticket.get('issue_type')}'")
                        print(f"  Tag: '{ticket.get('tag')}'")
                        print(f"  Status: '{ticket.get('status')}'")
                        print(f"  Created By: '{ticket.get('created_by')}'")
            else:
                print("Import failed!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_csv_import()
