import socket
import time

def check_port(host, port):
    """Check if a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except:
        return False
    finally:
        sock.close()

def main():
    print("Checking OCS services...")
    
    services = [
        ("PostgreSQL", "localhost", 5433),
        ("Tickets API", "localhost", 8000),
        ("Inventory API", "localhost", 8001),  
        ("Requisition API", "localhost", 8002),
        ("Portal", "localhost", 8003),
        ("Manage API", "localhost", 8004)
    ]
    
    for name, host, port in services:
        if check_port(host, port):
            print(f"✅ {name} ({port}) - Running")
        else:
            print(f"❌ {name} ({port}) - Not responding")
    
    # Test specific routes if portal is running
    if check_port("localhost", 8003):
        import requests
        try:
            print("\nTesting portal routes...")
            routes = ["/", "/users", "/users/list", "/buildings", "/buildings/list"]
            for route in routes:
                try:
                    r = requests.get(f"http://localhost:8003{route}", timeout=5)
                    print(f"  {route}: {r.status_code}")
                except Exception as e:
                    print(f"  {route}: ERROR - {str(e)[:50]}")
        except ImportError:
            print("Requests library not available for route testing")

if __name__ == "__main__":
    main()
