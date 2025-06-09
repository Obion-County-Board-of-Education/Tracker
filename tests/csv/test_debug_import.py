#!/usr/bin/env python3

import requests
import json

def test_csv_import():
    """Test CSV import functionality with our debug file"""
    
    # First, check current tickets count
    print("=== Checking tickets before import ===")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets_before = response.json()
            print(f"Tickets before import: {len(tickets_before)}")
        else:
            print(f"Error fetching tickets: {response.status_code}")
            return
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Import the CSV file
    print("\n=== Testing CSV Import ===")
    try:
        with open('debug_import_test.csv', 'rb') as f:
            files = {'file': ('debug_import_test.csv', f, 'text/csv')}
            data = {'operation': 'append'}  # Use append to avoid clearing existing tickets
            
            response = requests.post("http://localhost:8000/api/tickets/tech/import", 
                                   files=files, data=data)
            
            print(f"Import response status: {response.status_code}")
            print(f"Import response: {response.text}")
            
    except Exception as e:
        print(f"Import error: {e}")
        return
    
    # Check tickets after import
    print("\n=== Checking tickets after import ===")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets_after = response.json()
            print(f"Tickets after import: {len(tickets_after)}")
            
            # Show the most recent tickets (our imported ones should be at the top)
            recent_tickets = tickets_after[:2]
            for i, ticket in enumerate(recent_tickets):
                print(f"\nRecent Ticket {i+1}:")
                print(f"  ID: {ticket.get('id')}")
                print(f"  Title: '{ticket.get('title')}'")
                print(f"  Description: '{ticket.get('description')}'")
                print(f"  School: '{ticket.get('school')}'")
                print(f"  Room: '{ticket.get('room')}'")
                print(f"  Status: '{ticket.get('status')}'")
                print(f"  Issue Type: '{ticket.get('issue_type')}'")
                print(f"  Tag: '{ticket.get('tag')}'")
                print(f"  Created By: '{ticket.get('created_by')}'")
        else:
            print(f"Error fetching tickets after import: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_csv_import()
