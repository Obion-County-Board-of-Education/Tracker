#!/usr/bin/env python3

import requests
import json

# Test script to check what data is actually in the imported tickets
def check_imported_tickets():
    """Check what data was imported for tech tickets"""
    
    print("=== Checking Tech Tickets ===")
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets = response.json()
            print(f"Found {len(tickets)} tech tickets")
            
            for i, ticket in enumerate(tickets[:3]):  # Show first 3 tickets
                print(f"\nTicket {i+1}:")
                print(f"  ID: {ticket.get('id')}")
                print(f"  Title: '{ticket.get('title')}'")
                print(f"  Description: '{ticket.get('description')}'")
                print(f"  School: '{ticket.get('school')}'")
                print(f"  Room: '{ticket.get('room')}'")
                print(f"  Status: '{ticket.get('status')}'")
                print(f"  Issue Type: '{ticket.get('issue_type')}'")
                print(f"  Created By: '{ticket.get('created_by')}'")
                print(f"  Tag: '{ticket.get('tag')}'")
        else:
            print(f"Error fetching tech tickets: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Checking Maintenance Tickets ===")
    try:
        response = requests.get("http://localhost:8000/api/tickets/maintenance")
        if response.status_code == 200:
            tickets = response.json()
            print(f"Found {len(tickets)} maintenance tickets")
            
            for i, ticket in enumerate(tickets[:3]):  # Show first 3 tickets
                print(f"\nTicket {i+1}:")
                print(f"  ID: {ticket.get('id')}")
                print(f"  Title: '{ticket.get('title')}'")
                print(f"  Description: '{ticket.get('description')}'")
                print(f"  School: '{ticket.get('school')}'")
                print(f"  Room: '{ticket.get('room')}'")
                print(f"  Status: '{ticket.get('status')}'")
                print(f"  Issue Type: '{ticket.get('issue_type')}'")
                print(f"  Created By: '{ticket.get('created_by')}'")
                print(f"  Tag: '{ticket.get('tag')}'")
        else:
            print(f"Error fetching maintenance tickets: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_imported_tickets()
