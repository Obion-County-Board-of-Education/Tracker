import requests
import time

def test_import_buttons():
    print("Testing import button visibility...")
    
    # Wait a moment for service to start
    time.sleep(2)
    
    try:
        response = requests.get("http://localhost:8003/tickets/tech/open", timeout=10)
        if response.status_code == 200:
            content = response.text
            if "Import CSV" in content:
                print("✅ Import CSV button found in tech tickets page!")
            else:
                print("❌ Import CSV button NOT found in tech tickets page")
                
            if "action-buttons" in content:
                print("✅ Action buttons section found")
            else:
                print("❌ Action buttons section NOT found")
                
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_import_buttons()
