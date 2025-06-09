#!/usr/bin/env python3
"""
Quick test to verify the 'open' status fix is working.
"""

import requests
import json

def test_fix():
    print("🧪 Testing the 'Open' Status Fix...")
    
    # Step 1: Create a test ticket
    print("\n1. Creating a test ticket...")
    create_data = {
        "title": "Fix Verification Test",
        "description": "Testing that tickets with 'open' status appear in open filter",
        "issue_type": "Testing",
        "building_name": "Test Building", 
        "room_name": "Test Room",
        "created_by": "Fix Test"
    }
    
    response = requests.post("http://localhost:8000/api/tickets/tech", json=create_data)
    if response.status_code == 200:
        ticket = response.json()
        ticket_id = ticket['id']
        print(f"✅ Created ticket #{ticket_id} with initial status: {ticket['status']}")
    else:
        print(f"❌ Failed to create ticket: {response.status_code}")
        return False
    
    # Step 2: Update to 'open' status
    print(f"\n2. Updating ticket #{ticket_id} to 'open' status...")
    update_data = {"status": "open"}
    response = requests.put(f"http://localhost:8000/api/tickets/tech/{ticket_id}/status", data=update_data)
    if response.status_code == 200:
        print("✅ Successfully updated to 'open' status")
    else:
        print(f"❌ Failed to update: {response.status_code}")
        return False
    
    # Step 3: Check if it appears in open filter
    print("\n3. Checking open filter...")
    response = requests.get("http://localhost:8000/api/tickets/tech?status_filter=open")
    if response.status_code == 200:
        tickets = response.json()
        found = False
        for ticket in tickets:
            if ticket['id'] == ticket_id:
                print(f"✅ SUCCESS: Ticket #{ticket_id} found in open filter with status: '{ticket['status']}'")
                found = True
                break
        
        if not found:
            print(f"❌ FAILED: Ticket #{ticket_id} not found in open filter")
            return False
    else:
        print(f"❌ Failed to get open tickets: {response.status_code}")
        return False
    
    print("\n🎉 Fix verification successful! Tickets with 'open' status now appear in open filter.")
    return True

if __name__ == "__main__":
    test_fix()
