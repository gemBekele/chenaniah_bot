#!/usr/bin/env python3
"""
Test script for the Chenaniah API server
"""

import requests
import json
import sys

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Chenaniah API Server...")
    print("=" * 50)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test login endpoint
    print("\n2. Testing login endpoint...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{base_url}/api/auth/login", 
                               json=login_data, timeout=5)
        if response.status_code == 200:
            print("✅ Login successful")
            token = response.json().get('token')
            print(f"   Token received: {token[:20]}...")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False
    
    # Test protected endpoint with token
    print("\n3. Testing protected endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/submissions", 
                              headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ Protected endpoint accessible")
            data = response.json()
            print(f"   Submissions count: {data.get('count', 0)}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Protected endpoint failed: {e}")
        return False
    
    # Test stats endpoint
    print("\n4. Testing stats endpoint...")
    try:
        response = requests.get(f"{base_url}/api/stats", 
                              headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ Stats endpoint working")
            stats = response.json().get('stats', {})
            print(f"   Stats: {stats}")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats endpoint failed: {e}")
        return False
    
    print("\n🎉 All API tests passed!")
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
