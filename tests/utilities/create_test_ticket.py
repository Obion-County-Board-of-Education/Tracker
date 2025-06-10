#!/usr/bin/env python3
import requests
import json

# Create a test ticket with real data
ticket_data = {
    "title": "Test Ticket for Export",
    "description": "This is a test ticket with real data to verify export-import cycle",
    "issue_type": "Hardware",
    "building_name": "Elementary School", 
    "room_name": "Computer Lab",
    "created_by": "TestUser",
    "tag": "HW001"
}

try:
    response = requests.post("http://localhost:8000/api/tickets/tech", json=ticket_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        ticket = response.json()
        print(f"Created ticket: {ticket['title']} (ID: {ticket['id']})")
        print(f"School: {ticket['school']}, Room: {ticket['room']}")
        print(f"Issue Type: {ticket['issue_type']}, Tag: {ticket['tag']}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")
