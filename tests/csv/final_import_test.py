import requests

print("🔍 FINAL IMPORT TEST")
print("=" * 50)

# Test importing the exported CSV
try:
    with open('test_export_for_import.csv', 'rb') as f:
        files = {'file': ('test_export_for_import.csv', f, 'text/csv')}
        data = {'operation': 'append'}
        
        print("Importing test_export_for_import.csv...")
        response = requests.post("http://localhost:8000/api/tickets/tech/import", 
                               files=files, data=data)
        
        print(f"Import status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Import successful!")
            print(f"   Success: {result.get('success')}")
            print(f"   Imported count: {result.get('imported_count')}")
            print(f"   Errors: {result.get('errors')}")
            print(f"   Operation: {result.get('operation')}")
        else:
            print(f"❌ Import failed: {response.text}")
            exit(1)

except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Check if tickets are in database
print("\nChecking database...")
try:
    response = requests.get("http://localhost:8000/api/tickets/tech")
    if response.status_code == 200:
        tickets = response.json()
        print(f"✅ Found {len(tickets)} tickets in database")
        
        if len(tickets) > 0:
            ticket = tickets[0]
            print(f"   First ticket:")
            print(f"     Title: '{ticket.get('title')}'")
            print(f"     Description: '{ticket.get('description')}'")
            print(f"     Issue Type: '{ticket.get('issue_type')}'")
            print(f"     School: '{ticket.get('school')}'")
            print(f"     Room: '{ticket.get('room')}'")
            print(f"     Tag: '{ticket.get('tag')}'")
            print(f"     Status: '{ticket.get('status')}'")
            print(f"     Created By: '{ticket.get('created_by')}'")
            
            print("\n🎉 SUCCESS! The export-import cycle is working!")
        else:
            print("❌ No tickets found after import")
    else:
        print(f"❌ Error getting tickets: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error checking database: {e}")
