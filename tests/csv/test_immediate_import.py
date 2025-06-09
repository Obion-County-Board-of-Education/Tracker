import requests
import time

print("Testing import immediately after clear...")

# First, verify database is empty
response = requests.get("http://localhost:8000/api/tickets/tech")
print(f"Tickets before import: {len(response.json()) if response.status_code == 200 else 'Error'}")

# Test import
try:
    with open('simple_test.csv', 'rb') as f:
        files = {'file': ('simple_test.csv', f, 'text/csv')}
        data = {'operation': 'append'}
        
        response = requests.post("http://localhost:8000/api/tickets/tech/import", 
                               files=files, data=data)
        
        print(f"Import status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Import result: {result}")
        else:
            print(f"Import error: {response.text}")

except Exception as e:
    print(f"Import error: {e}")

# Check tickets immediately after import
time.sleep(1)  # Small delay to ensure commit
response = requests.get("http://localhost:8000/api/tickets/tech")
if response.status_code == 200:
    tickets = response.json()
    print(f"Tickets after import: {len(tickets)}")
    for ticket in tickets:
        print(f"  - Title: '{ticket.get('title')}', ID: {ticket.get('id')}")
else:
    print(f"Error getting tickets: {response.status_code}")
