import requests
import json

# Test the import endpoint with a simple CSV
print("Testing CSV import...")

try:
    # First check if we can read the file
    with open('simple_test.csv', 'r') as f:
        content = f.read()
        print(f"CSV content: {content}")
    
    # Now try the import
    with open('simple_test.csv', 'rb') as f:
        files = {'file': ('simple_test.csv', f, 'text/csv')}
        data = {'operation': 'append'}
        
        response = requests.post("http://localhost:8000/api/tickets/tech/import", 
                               files=files, data=data)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Imported count: {result.get('imported_count')}")
            print(f"Errors: {result.get('errors')}")

except Exception as e:
    print(f"Error: {e}")

# Check tickets after import
print("\nChecking tickets after import...")
try:
    response = requests.get("http://localhost:8000/api/tickets/tech")
    if response.status_code == 200:
        tickets = response.json()
        print(f"Total tickets: {len(tickets)}")
        for ticket in tickets:
            print(f"  - {ticket.get('title')} (ID: {ticket.get('id')})")
    else:
        print(f"Error getting tickets: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
