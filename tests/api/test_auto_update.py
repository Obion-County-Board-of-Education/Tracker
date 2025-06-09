#!/usr/bin/env python3
"""
Test script to verify the auto-update functionality by temporarily modifying
a ticket's creation date to be older than 48 hours, then testing the auto-update.
"""

import requests
import json
from datetime import datetime, timedelta
import psycopg2
import os

def test_auto_update():
    """Test the auto-update functionality"""
    
    print("=== AUTO-UPDATE FUNCTIONALITY TEST ===")
    
    # Database connection
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host="localhost",
            port="5433",
            database="ocs_tickets",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        
        print("✅ Connected to database")
        
        # Find a ticket with 'new' status
        cur.execute("SELECT id, title, created_at, status FROM tech_tickets WHERE status = 'new' LIMIT 1")
        result = cur.fetchone()
        
        if not result:
            print("❌ No 'new' tech tickets found for testing")
            return
            
        ticket_id, title, original_created_at, status = result
        print(f"📋 Found test ticket: ID {ticket_id} - {title} (Status: {status})")
        print(f"   Original creation time: {original_created_at}")
        
        # Calculate a time that's definitely older than 48 hours
        old_time = datetime.now() - timedelta(hours=49)
        
        print(f"⏰ Setting creation time to 49 hours ago: {old_time}")
        
        # Temporarily update the creation time
        cur.execute(
            "UPDATE tech_tickets SET created_at = %s WHERE id = %s",
            (old_time, ticket_id)
        )
        conn.commit()
        
        print("✅ Temporarily updated ticket creation time")
        
        # Test the auto-update status endpoint
        print("\n📊 Checking auto-update status...")
        response = requests.get("http://localhost:8000/api/tickets/auto-update/status")
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"   Tech tickets to update: {status_data['tech_tickets_to_update']}")
            print(f"   Total tickets to update: {status_data['total_tickets_to_update']}")
            
            if status_data['tech_tickets_to_update'] > 0:
                print("✅ Auto-update system correctly identified tickets for update")
                
                # Trigger the auto-update
                print("\n🔄 Triggering auto-update...")
                response = requests.post("http://localhost:8000/api/tickets/auto-update/trigger")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Auto-update triggered: {result['message']}")
                    
                    # Check if the ticket was updated
                    response = requests.get(f"http://localhost:8000/api/tickets/tech/{ticket_id}")
                    if response.status_code == 200:
                        ticket_data = response.json()
                        new_status = ticket_data['status']
                        print(f"📋 Ticket status after update: {new_status}")
                        
                        if new_status == 'open':
                            print("✅ SUCCESS: Ticket was automatically updated from 'new' to 'open'!")
                            
                            # Check update history
                            response = requests.get(f"http://localhost:8000/api/tickets/tech/{ticket_id}/updates")
                            if response.status_code == 200:
                                updates = response.json()
                                print(f"📝 Found {len(updates)} update entries")
                                for update in updates:
                                    if update.get('updated_by') == 'System':
                                        print(f"   ✅ System update: {update['status_from']} → {update['status_to']}")
                                        print(f"      Message: {update['update_message']}")
                        else:
                            print(f"❌ FAILED: Ticket status is still '{new_status}', expected 'open'")
                    else:
                        print(f"❌ Failed to fetch updated ticket: {response.status_code}")
                else:
                    print(f"❌ Failed to trigger auto-update: {response.status_code}")
            else:
                print("❌ Auto-update system did not identify any tickets for update")
        else:
            print(f"❌ Failed to get auto-update status: {response.status_code}")
        
        # Restore the original creation time
        print(f"\n🔄 Restoring original creation time...")
        cur.execute(
            "UPDATE tech_tickets SET created_at = %s WHERE id = %s",
            (original_created_at, ticket_id)
        )
        conn.commit()
        print("✅ Original creation time restored")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_auto_update()
