#!/usr/bin/env python3

import requests

def test_export_then_import():
    """Test exporting tickets and then re-importing them"""
    
    print("=== Testing Export -> Import Cycle ===")
    
    # First, clear existing tickets to start fresh
    print("1. Clearing existing tickets...")
    try:
        response = requests.delete("http://localhost:8000/api/tickets/tech/clear")
        if response.status_code == 200:
            print("✅ Tickets cleared successfully")
        else:
            print(f"❌ Failed to clear tickets: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error clearing tickets: {e}")
        return
    
    # Create some test tickets manually
    print("\n2. Creating test tickets...")
    test_tickets = [
        {
            "title": "Test Issue 1", 
            "description": "First test issue for export/import",
            "issue_type": "hardware",
            "building_name": "Test School 1",
            "room_name": "Room A1",
            "created_by": "Test User 1",
            "tag": "TEST001"
        },
        {
            "title": "Test Issue 2", 
            "description": "Second test issue for export/import",
            "issue_type": "software", 
            "building_name": "Test School 2",
            "room_name": "Room B2",
            "created_by": "Test User 2",
            "tag": "TEST002"
        }
    ]
    
    for i, ticket_data in enumerate(test_tickets):
        try:
            response = requests.post("http://localhost:8000/api/tickets/tech", json=ticket_data)
            if response.status_code == 200:
                print(f"✅ Created test ticket {i+1}")
            else:
                print(f"❌ Failed to create ticket {i+1}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating ticket {i+1}: {e}")
    
    # Export the tickets
    print("\n3. Exporting tickets to CSV...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech/export")
        if response.status_code == 200:
            print("✅ Export successful")
            
            # Save the exported data
            with open('test_export_reimport.csv', 'wb') as f:
                f.write(response.content)
                
            # Look at the exported CSV content
            print("\n--- Exported CSV Content ---")
            with open('test_export_reimport.csv', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:4]):  # Show first 4 lines
                    print(f"Line {i+1}: {line.strip()}")
                    
        else:
            print(f"❌ Export failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Export error: {e}")
        return
    
    # Try to re-import the exported CSV
    print("\n4. Re-importing the exported CSV...")
    try:
        with open('test_export_reimport.csv', 'rb') as f:
            files = {'file': ('test_export_reimport.csv', f, 'text/csv')}
            data = {'operation': 'append'}
            
            response = requests.post("http://localhost:8000/api/tickets/tech/import", 
                                   files=files, data=data)
            
            print(f"Import status: {response.status_code}")
            print(f"Import response: {response.text}")
            
    except Exception as e:
        print(f"❌ Import error: {e}")
        return
    
    # Check the final state
    print("\n5. Checking final ticket state...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets = response.json()
            print(f"Total tickets after import: {len(tickets)}")
            
            # Show first few tickets
            for i, ticket in enumerate(tickets[:3]):
                print(f"\nTicket {i+1}:")
                print(f"  ID: {ticket.get('id')}")
                print(f"  Title: '{ticket.get('title')}'")
                print(f"  Description: '{ticket.get('description')}'")
                print(f"  School: '{ticket.get('school')}'")
                print(f"  Room: '{ticket.get('room')}'")
                print(f"  Issue Type: '{ticket.get('issue_type')}'")
                print(f"  Tag: '{ticket.get('tag')}'")
                
        else:
            print(f"❌ Failed to get tickets: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting tickets: {e}")

if __name__ == "__main__":
    test_export_then_import()
