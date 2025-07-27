#!/usr/bin/env python3
"""
Test script to verify admin user login works
"""

import requests
import json

BACKEND_URL = "http://localhost:8001"

def test_admin_login():
    print("🧪 Testing admin user login...")
    
    # Test login
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"Token: {result.get('access_token', 'N/A')[:50]}...")
            print(f"User info: {result.get('user_info', {})}")
            
            # Test fetching kingdoms with the token
            token = result.get('access_token')
            if token:
                headers = {'Authorization': f'Bearer {token}'}
                kingdoms_response = requests.get(f"{BACKEND_URL}/api/multi-kingdoms", headers=headers)
                print(f"Kingdoms fetch status: {kingdoms_response.status_code}")
                
                if kingdoms_response.status_code == 200:
                    kingdoms = kingdoms_response.json()
                    print(f"✅ Found {len(kingdoms)} kingdoms")
                    for kingdom in kingdoms:
                        print(f"  - {kingdom.get('name', 'Unknown')} (ID: {kingdom.get('id', 'N/A')[:8]}...)")
                else:
                    print(f"❌ Failed to fetch kingdoms: {kingdoms_response.text}")
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_admin_login()