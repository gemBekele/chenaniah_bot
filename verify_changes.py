import requests
import json
import sys

# Configuration
API_URL = "http://localhost:5000/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Default password from api_server.py

def get_token():
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        response.raise_for_status()
        return response.json()["token"]
    except Exception as e:
        print(f"Failed to login: {e}")
        sys.exit(1)

def test_stats(token):
    print("\nTesting /api/schedule/stats...")
    try:
        response = requests.get(f"{API_URL}/schedule/stats", headers={
            "Authorization": f"Bearer {token}"
        })
        response.raise_for_status()
        stats = response.json()["stats"]
        print(f"Stats received: {json.dumps(stats, indent=2)}")
        
        required_keys = ["total_appointments", "scheduled", "accepted", "rejected", "cancelled"]
        missing_keys = [key for key in required_keys if key not in stats]
        
        if missing_keys:
            print(f"❌ Missing keys in stats: {missing_keys}")
        else:
            print("✅ Stats structure is correct")
            
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")

def test_search(token):
    print("\nTesting /api/schedule/appointments with search...")
    try:
        # First get all appointments to find a name to search for
        response = requests.get(f"{API_URL}/schedule/appointments", headers={
            "Authorization": f"Bearer {token}"
        })
        response.raise_for_status()
        appointments = response.json()["appointments"]
        
        if not appointments:
            print("⚠️ No appointments found to test search")
            return

        target_name = appointments[0]["applicant_name"]
        print(f"Searching for: {target_name}")
        
        # Search for the name
        response = requests.get(f"{API_URL}/schedule/appointments", params={"search": target_name}, headers={
            "Authorization": f"Bearer {token}"
        })
        response.raise_for_status()
        search_results = response.json()["appointments"]
        
        print(f"Found {len(search_results)} results")
        
        matched = any(apt["applicant_name"] == target_name for apt in search_results)
        if matched:
            print("✅ Search returned the expected applicant")
        else:
            print("❌ Search did not return the expected applicant")
            
    except Exception as e:
        print(f"❌ Failed to search appointments: {e}")

if __name__ == "__main__":
    print("Starting verification...")
    token = get_token()
    test_stats(token)
    test_search(token)
