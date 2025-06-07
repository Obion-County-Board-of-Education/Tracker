#!/usr/bin/env python3
"""
Test script to verify maintenance ticket comprehensive update functionality
"""
import requests
import json

def test_maintenance_ticket_workflow():
    print("Testing maintenance ticket complete workflow...")
    
    # First, create a maintenance ticket
    print("\n1. Creating a maintenance ticket...")
    create_data = {
        "title": "Test HVAC Issue",
        "description": "Air conditioning not working in classroom",
        "issue_type": "hvac",
        "building_name": "Main Building",
        "room_name": "Room 101",
        "created_by": "Test User"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/tickets/maintenance",
            json=create_data,
            timeout=10
        )
        
        if response.status_code == 200:
            ticket = response.json()
            ticket_id = ticket['id']
            print(f"✅ Maintenance ticket created successfully! ID: {ticket_id}")
            print(f"   Status: {ticket['status']}")
            
            # Now update the ticket to closed status
            print(f"\n2. Updating ticket {ticket_id} to closed status...")
            update_data = {
                "status": "closed",
                "update_message": "HVAC unit repaired and tested successfully",
                "updated_by": "Maintenance Staff"
            }
            
            response = requests.put(
                f"http://localhost:8000/api/tickets/maintenance/{ticket_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Maintenance ticket update successful!")
                print(f"Response: {response.json()}")
                
                # Check the update history
                print(f"\n3. Checking update history for ticket {ticket_id}...")
                response = requests.get(
                    f"http://localhost:8000/api/tickets/maintenance/{ticket_id}/updates",
                    timeout=10
                )
                
                if response.status_code == 200:
                    updates = response.json()
                    print(f"✅ Found {len(updates)} updates")
                    for update in updates:
                        print(f"  - {update.get('created_at', 'Unknown time')}: {update.get('status_from', '?')} → {update.get('status_to', '?')}")
                        if update.get('update_message'):
                            print(f"    Message: {update['update_message']}")
                            print(f"    Updated by: {update['updated_by']}")
                else:
                    print(f"❌ Failed to get updates: {response.status_code}")
                    
                # Test the closed tickets filter
                print(f"\n4. Testing closed tickets filter...")
                response = requests.get(
                    "http://localhost:8000/api/tickets/maintenance?status_filter=closed",
                    timeout=10
                )
                
                if response.status_code == 200:
                    closed_tickets = response.json()
                    print(f"✅ Found {len(closed_tickets)} closed maintenance tickets")
                    for ticket in closed_tickets:
                        print(f"  - Ticket #{ticket['id']}: {ticket['title']} - Status: {ticket['status']}")
                else:
                    print(f"❌ Failed to get closed tickets: {response.status_code}")
                    
            else:
                print(f"❌ Update failed with status {response.status_code}")
                print(f"Response: {response.text}")
        else:
            print(f"❌ Failed to create ticket: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_maintenance_ticket_workflow()
