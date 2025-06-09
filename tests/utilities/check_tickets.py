import sqlite3
import os

# Check if database exists and query tickets
db_path = '/app/instance/tracker.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all closed tickets
    cursor.execute('SELECT id, title, status, description, school, room, issue_type FROM maintenance_tickets WHERE status = ?', ('closed',))
    closed_tickets = cursor.fetchall()
    
    print('=== CLOSED TICKETS ===')
    for ticket in closed_tickets:
        print(f'ID: {ticket[0]}, Title: "{ticket[1]}", Status: {ticket[2]}')
        print(f'Description length: {len(ticket[3]) if ticket[3] else 0} chars')
        print(f'School: {ticket[4]}, Room: {ticket[5]}, Type: {ticket[6]}')
        print('-' * 60)
    
    # Get all open tickets for comparison
    cursor.execute('SELECT id, title, status, description, school, room, issue_type FROM maintenance_tickets WHERE status != ?', ('closed',))
    open_tickets = cursor.fetchall()
    
    print('\n=== OPEN TICKETS ===')
    for ticket in open_tickets:
        print(f'ID: {ticket[0]}, Title: "{ticket[1]}", Status: {ticket[2]}')
        print(f'Description length: {len(ticket[3]) if ticket[3] else 0} chars')
        print(f'School: {ticket[4]}, Room: {ticket[5]}, Type: {ticket[6]}')
        print('-' * 60)
    
    conn.close()
else:
    print('Database not found at:', db_path)
