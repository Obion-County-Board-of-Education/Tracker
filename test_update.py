#!/usr/bin/env python3
"""
Test script to verify tech ticket comprehensive update functionality
"""
import requests
import json

def test_ticket_update():
    # Test comprehensive update (status + message)
    print("Testing comprehensive ticket update (status + message)...")
    
    update_data = {
        "status": "closed",
        "update_message": "Issue has been closed after testing the new configuration",
        "updated_by": "Test User"
    }
    
    try:
        response = requests.put(
            "http://localhost:8000/api/tickets/tech/1",
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Comprehensive update successful!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Update failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during update: {e}")

    # Get ticket updates to verify
    print("\nChecking ticket update history...")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech/1/updates", timeout=10)
        if response.status_code == 200:
            updates = response.json()
            print(f"✅ Found {len(updates)} updates")
            for update in updates[-3:]:  # Show last 3 updates
                print(f"  - {update.get('created_at', 'Unknown time')}: {update.get('status_from', '?')} → {update.get('status_to', '?')}")
                if update.get('update_message'):
                    print(f"    Message: {update['update_message']}")
        else:
            print(f"❌ Failed to get updates: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting updates: {e}")

if __name__ == "__main__":
    test_ticket_update()
