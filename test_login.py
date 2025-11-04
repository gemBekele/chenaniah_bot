#!/usr/bin/env python3
"""
Test script to verify login functionality
"""
import requests
import json
import sys

def test_login(base_url, username, password):
    """Test login endpoint"""
    url = f"{base_url}/api/auth/login"
    
    print(f"Testing login at: {url}")
    print(f"Username: {username}")
    print("-" * 50)
    
    try:
        # Test OPTIONS (CORS preflight)
        print("1. Testing OPTIONS (CORS preflight)...")
        options_response = requests.options(
            url,
            headers={
                'Origin': 'https://chenaniah.org',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=5
        )
        print(f"   Status: {options_response.status_code}")
        print(f"   CORS Headers:")
        for header in ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers']:
            value = options_response.headers.get(header, 'NOT SET')
            print(f"     {header}: {value}")
        
        if options_response.status_code != 200:
            print(f"   ⚠️  WARNING: OPTIONS request failed with {options_response.status_code}")
        
        # Test POST (actual login)
        print("\n2. Testing POST (login)...")
        post_response = requests.post(
            url,
            json={'username': username, 'password': password},
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://chenaniah.org'
            },
            timeout=5
        )
        print(f"   Status: {post_response.status_code}")
        print(f"   CORS Headers:")
        cors_origin = post_response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
        print(f"     Access-Control-Allow-Origin: {cors_origin}")
        
        if post_response.status_code == 200:
            data = post_response.json()
            if data.get('success') and data.get('token'):
                print(f"   ✅ Login successful!")
                print(f"   Token: {data['token'][:50]}...")
                print(f"   Username: {data.get('username', 'N/A')}")
                return True
            else:
                print(f"   ❌ Login failed: {data}")
                return False
        else:
            print(f"   ❌ Login failed with status {post_response.status_code}")
            print(f"   Response: {post_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ ERROR: Cannot connect to {base_url}")
        print("   Make sure the API server is running!")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    # Test local server
    print("=" * 50)
    print("Testing LOCAL API Server")
    print("=" * 50)
    local_success = test_login("http://localhost:5000", "admin", "admin123")
    
    print("\n" + "=" * 50)
    print("Testing PRODUCTION API Server")
    print("=" * 50)
    prod_success = test_login("https://chenaniah.com", "admin", "admin123")
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Local API:   {'✅ Working' if local_success else '❌ Not working'}")
    print(f"Production:  {'✅ Working' if prod_success else '❌ Not working'}")
    
    sys.exit(0 if (local_success or prod_success) else 1)

