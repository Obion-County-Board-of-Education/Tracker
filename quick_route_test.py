import requests

try:
    print("Testing simple route...")
    response = requests.get("http://localhost:8000/api/test/simple", timeout=5)
    print(f"Simple route status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    
    print("\nTesting export_for_import route...")
    response = requests.get("http://localhost:8000/api/tickets/tech/export_for_import", timeout=5)
    print(f"Export for import status: {response.status_code}")
    
    print("\nTesting regular export route...")
    response = requests.get("http://localhost:8000/api/tickets/tech/export", timeout=5)
    print(f"Regular export status: {response.status_code}")
    
except Exception as e:
    print(f"Error: {e}")
