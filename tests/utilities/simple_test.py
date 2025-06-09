import requests

print("Testing connection...")
response = requests.get('http://localhost:5002/api/tickets/tech/export?exclude_ids=true')
print(f'Status: {response.status_code}')
if response.status_code == 200:
    first_line = response.text.split('\n')[0] if response.text else "No content"
    print(f'First line (headers): {first_line}')
    print(f'Contains id: {"id" in first_line.lower()}')
    print(f'Contains created_at: {"created_at" in first_line.lower()}')
    print(f'Contains updated_at: {"updated_at" in first_line.lower()}')
else:
    print(f'Error response: {response.text}')
