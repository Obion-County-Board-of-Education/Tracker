import requests
import time

def test_user_building_routes():
    """Test if user and building routes are working"""
    base_url = "http://localhost:8003"
    
    routes_to_test = [
        "/users",
        "/users/list", 
        "/buildings",
        "/buildings/list"
    ]
    
    results = []
    
    for route in routes_to_test:
        try:
            print(f"Testing {route}...")
            response = requests.get(f"{base_url}{route}", timeout=10)
            status = response.status_code
            
            if status == 200:
                result = f"✅ {route} - OK (200)"
            elif status == 302:
                redirect_location = response.headers.get('location', 'unknown')
                result = f"↗️  {route} - Redirect (302) to {redirect_location}"
            else:
                result = f"❌ {route} - Error ({status})"
                
            results.append(result)
            print(result)
            
        except requests.exceptions.RequestException as e:
            result = f"❌ {route} - Connection Error: {e}"
            results.append(result)
            print(result)
        
        time.sleep(1)  # Brief pause between requests
    
    # Write results to file
    with open("route_test_results.txt", "w", encoding="utf-8") as f:
        f.write("=== User and Building Routes Test Results ===\n")
        f.write(f"Test run at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for result in results:
            f.write(f"{result}\n")
    
    print(f"\nResults written to route_test_results.txt")
    return results

if __name__ == "__main__":
    test_user_building_routes()
