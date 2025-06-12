#!/usr/bin/env python3
"""
Test script to verify the complete clear tickets functionality
"""
import requests
import time

def test_clear_tickets():
    print("🧪 Testing Clear All Tickets functionality...")
    
    # Step 1: Create a test tech ticket
    print("\n1. Creating a test tech ticket...")
    tech_ticket_data = {
        "title": "Test Tech Issue for Clear Function",
        "description": "This ticket will be used to test the clear functionality",
        "issue_type": "software",
        "building_name": "Main Building",
        "room_name": "Room 101",
        "created_by": "Test User"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/tickets/tech",
            json=tech_ticket_data,
            timeout=10
        )
        
        if response.status_code == 200:
            tech_ticket = response.json()
            print(f"✅ Tech ticket created! ID: {tech_ticket['id']}")
        else:
            print(f"❌ Failed to create tech ticket: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error creating tech ticket: {e}")
        return
    
    # Step 2: Create a test maintenance ticket
    print("\n2. Creating a test maintenance ticket...")
    maintenance_ticket_data = {
        "title": "Test Maintenance Issue for Clear Function",
        "description": "This ticket will be used to test the clear functionality",
        "issue_type": "hvac",
        "building_name": "Main Building",
        "room_name": "Room 102",
        "created_by": "Test User"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/tickets/maintenance",
            json=maintenance_ticket_data,
            timeout=10
        )
        
        if response.status_code == 200:
            maintenance_ticket = response.json()
            print(f"✅ Maintenance ticket created! ID: {maintenance_ticket['id']}")
        else:
            print(f"❌ Failed to create maintenance ticket: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error creating maintenance ticket: {e}")
        return
    
    # Step 3: Verify tickets exist
    print("\n3. Verifying tickets exist before clearing...")
    
    # Check tech tickets
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech", timeout=10)
        if response.status_code == 200:
            tech_tickets = response.json()
            print(f"📊 Found {len(tech_tickets)} tech tickets before clearing")
        else:
            print(f"❌ Failed to get tech tickets: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting tech tickets: {e}")
    
    # Check maintenance tickets
    try:
        response = requests.get("http://localhost:8000/api/tickets/maintenance", timeout=10)
        if response.status_code == 200:
            maintenance_tickets = response.json()
            print(f"📊 Found {len(maintenance_tickets)} maintenance tickets before clearing")
        else:
            print(f"❌ Failed to get maintenance tickets: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting maintenance tickets: {e}")
    
    # Step 4: Test clear tech tickets via API
    print("\n4. Testing clear tech tickets via API...")
    try:
        response = requests.delete("http://localhost:8000/api/tickets/tech/clear", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tech tickets cleared successfully!")
            print(f"   Response: {result}")
        else:
            print(f"❌ Failed to clear tech tickets: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error clearing tech tickets: {e}")
    
    # Step 5: Test clear maintenance tickets via API
    print("\n5. Testing clear maintenance tickets via API...")
    try:
        response = requests.delete("http://localhost:8000/api/tickets/maintenance/clear", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Maintenance tickets cleared successfully!")
            print(f"   Response: {result}")
        else:
            print(f"❌ Failed to clear maintenance tickets: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error clearing maintenance tickets: {e}")
    
    # Step 6: Verify tickets are cleared
    print("\n6. Verifying tickets are cleared...")
    
    # Check tech tickets
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech", timeout=10)
        if response.status_code == 200:
            tech_tickets = response.json()
            print(f"📊 Found {len(tech_tickets)} tech tickets after clearing")
            if len(tech_tickets) == 0:
                print("✅ Tech tickets successfully cleared!")
            else:
                print("❌ Tech tickets still exist after clearing")
        else:
            print(f"❌ Failed to get tech tickets: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting tech tickets: {e}")
    
    # Check maintenance tickets
    try:
        response = requests.get("http://localhost:8000/api/tickets/maintenance", timeout=10)
        if response.status_code == 200:
            maintenance_tickets = response.json()
            print(f"📊 Found {len(maintenance_tickets)} maintenance tickets after clearing")
            if len(maintenance_tickets) == 0:
                print("✅ Maintenance tickets successfully cleared!")
            else:
                print("❌ Maintenance tickets still exist after clearing")
        else:
            print(f"❌ Failed to get maintenance tickets: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting maintenance tickets: {e}")
    
    print("\n🎯 Clear tickets functionality test completed!")

if __name__ == "__main__":
    test_clear_tickets()
