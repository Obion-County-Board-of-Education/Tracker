#!/usr/bin/env python3
"""
Test script to reproduce and verify the fix for the "open" status disappearing issue.
"""

import requests
import json

def test_open_status_issue():
    """Test the open status filtering issue"""
    print("🧪 Testing the 'Open' status disappearing issue...")
    
    base_url = "http://localhost:8000"
    
    # Step 1: Create a test ticket
    print("\n1. Creating a test tech ticket...")
    create_data = {
        "title": "Test Open Status Issue",
        "description": "Testing why tickets disappear when set to 'open' status",
        "issue_type": "Testing",
        "building_name": "Test Building",
        "room_name": "Test Room",
        "created_by": "Test User"
    }
    
    try:
        response = requests.post(f"{base_url}/api/tickets/tech", json=create_data, timeout=10)
        if response.status_code == 200:
            ticket = response.json()
            ticket_id = ticket['id']
            print(f"✅ Created tech ticket #{ticket_id} with status: {ticket['status']}")
        else:
            print(f"❌ Failed to create ticket: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error creating ticket: {e}")
        return False
    
    # Step 2: Update ticket status to "open"
    print(f"\n2. Updating ticket #{ticket_id} status to 'open'...")
    try:
        update_data = {"status": "open"}
        response = requests.put(f"{base_url}/api/tickets/tech/{ticket_id}/status", 
                               data=update_data, timeout=10)
        if response.status_code == 200:
            print("✅ Status updated to 'open'")
        else:
            print(f"❌ Failed to update status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error updating status: {e}")
        return False
    
    # Step 3: Check if ticket shows up in "open" filter
    print("\n3. Checking if ticket appears in 'open' filter...")
    try:
        response = requests.get(f"{base_url}/api/tickets/tech?status_filter=open", timeout=10)
        if response.status_code == 200:
            tickets = response.json()
            found_ticket = None
            for ticket in tickets:
                if ticket['id'] == ticket_id:
                    found_ticket = ticket
                    break
            
            if found_ticket:
                print(f"✅ SUCCESS: Ticket #{ticket_id} found in open filter with status: {found_ticket['status']}")
                return True
            else:
                print(f"❌ ISSUE CONFIRMED: Ticket #{ticket_id} NOT found in open filter")
                print(f"   Found {len(tickets)} open tickets, but our ticket is missing")
                
                # Let's check all tickets to see where our ticket went
                print("\n4. Checking all tickets to find our test ticket...")
                response = requests.get(f"{base_url}/api/tickets/tech", timeout=10)
                if response.status_code == 200:
                    all_tickets = response.json()
                    for ticket in all_tickets:
                        if ticket['id'] == ticket_id:
                            print(f"   Found ticket #{ticket_id} with status: '{ticket['status']}'")
                            print(f"   This explains why it doesn't appear in 'open' filter!")
                            break
                return False
        else:
            print(f"❌ Failed to get open tickets: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking open filter: {e}")
        return False

if __name__ == "__main__":
    success = test_open_status_issue()
    if success:
        print("\n🎉 Test passed - no issue found!")
    else:
        print("\n❌ Test confirmed the issue exists - tickets with 'open' status don't appear in 'open' filter")
        print("\nThe fix needed: Update API filtering logic to include 'open' in the open filter list")
