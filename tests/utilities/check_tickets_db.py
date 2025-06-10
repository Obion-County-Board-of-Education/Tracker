#!/usr/bin/env python3
import requests

try:
    response = requests.get('http://localhost:8000/api/tickets/tech')
    if response.status_code == 200:
        tickets = response.json()
        print(f'Found {len(tickets)} tickets in database:')
        for ticket in tickets:
            print(f'- ID: {ticket["id"]}, Title: {ticket["title"]}, Status: {ticket["status"]}, School: {ticket.get("school", "N/A")}')
    else:
        print(f'API Error: {response.status_code}')
        print(response.text)
except Exception as e:
    print(f'Error: {e}')
