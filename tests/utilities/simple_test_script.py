import requests

print("Starting test...")

try:
    response = requests.get("http://localhost:8000/api/tickets/tech/export?import_ready=true")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        lines = response.text.split('\n')
        if lines:
            headers = lines[0]
            print(f"First line (headers): {headers}")
            
            if 'id' in headers:
                print("❌ ID found in headers - parameter not working")
            else:
                print("✅ ID not found - parameter working")
        
        with open("simple_test.csv", "w") as f:
            f.write(response.text)
        print("Saved to simple_test.csv")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Exception: {e}")

print("Test completed")
