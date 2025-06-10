#!/usr/bin/env python3
import requests
import io

def debug_import_issue():
    print("🔍 DEBUGGING IMPORT ISSUE")
    print("=" * 40)
    
    # Step 1: Create a simple test CSV with known data
    test_csv_content = """title,description,issue_type,school,room,tag,status,created_by
Test Import Ticket,This is a test description,Hardware,Test School,Test Room,T001,new,TestImporter"""
    
    print("📄 Test CSV Content:")
    print(test_csv_content)
    print()
    
    # Save CSV to file for import
    with open('debug_import_test.csv', 'w', encoding='utf-8') as f:
        f.write(test_csv_content)
    
    # Step 2: Try to import this CSV
    print("📥 Attempting import...")
    try:
        with open('debug_import_test.csv', 'rb') as f:
            files = {'file': ('debug_import_test.csv', f, 'text/csv')}
            data = {'operation': 'append'}
            
            response = requests.post("http://localhost:8000/api/tickets/tech/import",
                                   files=files, data=data)
            
            print(f"Import response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Import result: {result}")
            else:
                print(f"Import error: {response.text}")
                
    except Exception as e:
        print(f"Import exception: {e}")
    
    # Step 3: Check what was actually created
    print("\n🔍 Checking created tickets...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets = response.json()
            print(f"Found {len(tickets)} tickets:")
            for ticket in tickets:
                print(f"  ID: {ticket['id']}")
                print(f"  Title: '{ticket['title']}'")
                print(f"  Description: '{ticket['description']}'")
                print(f"  Issue Type: '{ticket['issue_type']}'")
                print(f"  School: '{ticket['school']}'")
                print(f"  Room: '{ticket['room']}'")
                print(f"  Tag: '{ticket['tag']}'")
                print(f"  Status: '{ticket['status']}'")
                print(f"  Created By: '{ticket['created_by']}'")
                print("  ---")
        else:
            print(f"Failed to get tickets: {response.status_code}")
            
    except Exception as e:
        print(f"Error getting tickets: {e}")

if __name__ == "__main__":
    debug_import_issue()
