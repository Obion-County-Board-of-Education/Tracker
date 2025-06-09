#!/usr/bin/env python3
import requests

def test_import_with_debug():
    print("🧪 TESTING CSV IMPORT WITH DEBUG")
    print("=" * 40)
    
    # Create CSV content
    csv_content = """title,description,issue_type,school,room,tag,status,created_by
Network Issue,Internet connection dropping frequently,Network,Middle School,Computer Lab,NET002,new,TechSupport
Broken Printer,Main printer in office not working,Hardware,Elementary School,Main Office,PRINT001,new,TestUser"""

    print("📄 CSV Content to import:")
    print(csv_content)
    print()
    
    # Save to file
    with open('python_test_import.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    # Import using requests
    try:
        with open('python_test_import.csv', 'rb') as f:
            files = {'file': ('python_test_import.csv', f, 'text/csv')}
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
    
    # Check results
    print("\n🔍 Checking imported tickets...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets = response.json()
            print(f"Found {len(tickets)} tickets")
            for ticket in tickets:
                print(f"  - {ticket['title']} ({ticket['id']})")
        else:
            print(f"Failed to get tickets: {response.status_code}")
    except Exception as e:
        print(f"Error getting tickets: {e}")

if __name__ == "__main__":
    test_import_with_debug()
