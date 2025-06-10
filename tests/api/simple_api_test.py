import requests

print("Testing API connection...")
try:
    response = requests.get('http://localhost:8000/api/tickets/tech?status_filter=open', timeout=5)
    print(f'API Response: {response.status_code}')
    if response.status_code == 200:
        tickets = response.json()
        print(f'Found {len(tickets)} tech tickets in open filter')
    else:
        print(f'API Error: {response.text}')
except Exception as e:
    print(f'Connection error: {e}')
