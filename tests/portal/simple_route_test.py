import requests

print("Testing routes:")
routes = ["/users", "/users/list", "/buildings", "/buildings/list"]

for route in routes:
    try:
        r = requests.get(f"http://localhost:8000{route}")
        print(f"{route}: {r.status_code}")
    except Exception as e:
        print(f"{route}: ERROR - {e}")
