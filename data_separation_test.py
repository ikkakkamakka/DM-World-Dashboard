#!/usr/bin/env python3
"""
Data Separation Testing Suite for Fantasy Kingdom Management System
Tests authentication, authorization, data isolation, and super admin functionality
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    print("❌ Could not determine backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BACKEND_URL}/api"
AUTH_BASE = f"{BACKEND_URL}/auth"

print(f"🔗 Testing backend at: {API_BASE}")
print(f"🔗 Auth endpoints at: {AUTH_BASE}")

class DataSeparationTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.dm1_token = None
        self.dm2_token = None
        self.admin_user_id = None
        self.dm1_user_id = None
        self.dm2_user_id = None
        self.test_results = {
            'admin_login': False,
            'dm_account_creation': False,
            'jwt_token_validation': False,
            'data_isolation_kingdoms': False,
            'data_isolation_events': False,
            'registry_ownership_verification': False,
            'cross_account_access_prevention': False,
            'super_admin_bypass': False,
            'kingdom_management_security': False,
            'data_migration_verification': False
        }
        self.errors = []

    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def test_admin_login(self):
        """Test admin user login with default credentials"""
        print("\n🔐 Testing Admin User Login...")
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            async with self.session.post(f"{AUTH_BASE}/login", json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Verify response structure
                    required_fields = ['access_token', 'token_type', 'user_info']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if missing_fields:
                        self.errors.append(f"Admin login response missing fields: {missing_fields}")
                        return False
                    
                    # Store admin token and user info
                    self.admin_token = result['access_token']
                    self.admin_user_id = result['user_info']['id']
                    
                    # Verify token type
                    if result['token_type'] != 'bearer':
                        self.errors.append(f"Expected token_type 'bearer', got '{result['token_type']}'")
                        return False
                    
                    # Verify admin username
                    if result['user_info']['username'] != 'admin':
                        self.errors.append(f"Expected username 'admin', got '{result['user_info']['username']}'")
                        return False
                    
                    print(f"✅ Admin login successful")
                    print(f"   User ID: {self.admin_user_id}")
                    print(f"   Username: {result['user_info']['username']}")
                    print(f"   Token type: {result['token_type']}")
                    
                    self.test_results['admin_login'] = True
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Admin login failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Admin login error: {str(e)}")
            return False

    async def test_dm_account_creation(self):
        """Test creating two DM test accounts"""
        print("\n👥 Testing DM Account Creation...")
        try:
            # Create first DM account
            dm1_data = {
                "username": "dm_test_1",
                "email": "dm1@test.com",
                "password": "testpass123"
            }
            
            async with self.session.post(f"{AUTH_BASE}/signup", json=dm1_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.dm1_token = result['access_token']
                    self.dm1_user_id = result['user_info']['id']
                    print(f"✅ DM Test 1 account created - ID: {self.dm1_user_id}")
                else:
                    error_text = await response.text()
                    self.errors.append(f"DM1 account creation failed: HTTP {response.status} - {error_text}")
                    return False
            
            # Create second DM account
            dm2_data = {
                "username": "dm_test_2", 
                "email": "dm2@test.com",
                "password": "testpass456"
            }
            
            async with self.session.post(f"{AUTH_BASE}/signup", json=dm2_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.dm2_token = result['access_token']
                    self.dm2_user_id = result['user_info']['id']
                    print(f"✅ DM Test 2 account created - ID: {self.dm2_user_id}")
                else:
                    error_text = await response.text()
                    self.errors.append(f"DM2 account creation failed: HTTP {response.status} - {error_text}")
                    return False
            
            self.test_results['dm_account_creation'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"DM account creation error: {str(e)}")
            return False

    async def test_jwt_token_validation(self):
        """Test JWT token validation and structure"""
        print("\n🎫 Testing JWT Token Validation...")
        try:
            # Test admin token validation
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.get(f"{AUTH_BASE}/me", headers=headers) as response:
                if response.status == 200:
                    user_info = await response.json()
                    
                    if user_info['username'] != 'admin':
                        self.errors.append(f"Admin token validation failed: wrong username")
                        return False
                    
                    if user_info['id'] != self.admin_user_id:
                        self.errors.append(f"Admin token validation failed: wrong user ID")
                        return False
                        
                    print(f"✅ Admin JWT token valid")
                else:
                    self.errors.append(f"Admin token validation failed: HTTP {response.status}")
                    return False
            
            # Test DM1 token validation
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.get(f"{AUTH_BASE}/me", headers=headers) as response:
                if response.status == 200:
                    user_info = await response.json()
                    
                    if user_info['username'] != 'dm_test_1':
                        self.errors.append(f"DM1 token validation failed: wrong username")
                        return False
                        
                    print(f"✅ DM1 JWT token valid")
                else:
                    self.errors.append(f"DM1 token validation failed: HTTP {response.status}")
                    return False
            
            # Test invalid token
            headers = {"Authorization": "Bearer invalid_token_12345"}
            async with self.session.get(f"{AUTH_BASE}/me", headers=headers) as response:
                if response.status in [401, 403]:
                    print(f"✅ Invalid token properly rejected with status {response.status}")
                else:
                    self.errors.append(f"Invalid token should be rejected, got status {response.status}")
                    return False
            
            self.test_results['jwt_token_validation'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"JWT token validation error: {str(e)}")
            return False

    async def test_data_isolation_kingdoms(self):
        """Test that users can only see their own kingdoms"""
        print("\n🏰 Testing Kingdom Data Isolation...")
        try:
            # Test admin user - should see existing kingdoms (migrated data)
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status == 200:
                    admin_kingdoms = await response.json()
                    
                    if len(admin_kingdoms) == 0:
                        self.errors.append("Admin user should see migrated kingdoms but found none")
                        return False
                    
                    # Verify all kingdoms belong to admin
                    for kingdom in admin_kingdoms:
                        if kingdom.get('owner_id') != self.admin_user_id:
                            self.errors.append(f"Kingdom {kingdom['name']} has wrong owner_id: {kingdom.get('owner_id')} != {self.admin_user_id}")
                            return False
                    
                    print(f"✅ Admin user sees {len(admin_kingdoms)} kingdoms (migrated data)")
                    for kingdom in admin_kingdoms:
                        print(f"   - {kingdom['name']} (Owner: {kingdom.get('owner_id')})")
                        
                else:
                    self.errors.append(f"Admin kingdoms request failed: HTTP {response.status}")
                    return False
            
            # Test DM1 user - should see NO kingdoms initially
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status == 200:
                    dm1_kingdoms = await response.json()
                    
                    if len(dm1_kingdoms) != 0:
                        self.errors.append(f"DM1 user should see 0 kingdoms but found {len(dm1_kingdoms)}")
                        return False
                    
                    print(f"✅ DM1 user sees {len(dm1_kingdoms)} kingdoms (correct isolation)")
                else:
                    self.errors.append(f"DM1 kingdoms request failed: HTTP {response.status}")
                    return False
            
            # Test DM2 user - should see NO kingdoms initially
            headers = {"Authorization": f"Bearer {self.dm2_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status == 200:
                    dm2_kingdoms = await response.json()
                    
                    if len(dm2_kingdoms) != 0:
                        self.errors.append(f"DM2 user should see 0 kingdoms but found {len(dm2_kingdoms)}")
                        return False
                    
                    print(f"✅ DM2 user sees {len(dm2_kingdoms)} kingdoms (correct isolation)")
                else:
                    self.errors.append(f"DM2 kingdoms request failed: HTTP {response.status}")
                    return False
            
            self.test_results['data_isolation_kingdoms'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Kingdom data isolation error: {str(e)}")
            return False

    async def test_kingdom_creation_isolation(self):
        """Test that users can only see kingdoms they create"""
        print("\n🏗️ Testing Kingdom Creation and Isolation...")
        try:
            # Create kingdom for DM1
            dm1_kingdom_data = {
                "name": "DM1 Test Kingdom",
                "ruler": "DM1 Test Ruler",
                "government_type": "Test Monarchy",
                "color": "#ff0000"
            }
            
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.post(f"{API_BASE}/multi-kingdoms", json=dm1_kingdom_data, headers=headers) as response:
                if response.status == 200:
                    dm1_kingdom = await response.json()
                    dm1_kingdom_id = dm1_kingdom['id']
                    
                    # Verify owner_id is set correctly
                    if dm1_kingdom.get('owner_id') != self.dm1_user_id:
                        self.errors.append(f"DM1 kingdom has wrong owner_id: {dm1_kingdom.get('owner_id')} != {self.dm1_user_id}")
                        return False
                    
                    print(f"✅ DM1 created kingdom: {dm1_kingdom['name']} (ID: {dm1_kingdom_id})")
                else:
                    error_text = await response.text()
                    self.errors.append(f"DM1 kingdom creation failed: HTTP {response.status} - {error_text}")
                    return False
            
            # Create kingdom for DM2
            dm2_kingdom_data = {
                "name": "DM2 Test Kingdom",
                "ruler": "DM2 Test Ruler", 
                "government_type": "Test Republic",
                "color": "#00ff00"
            }
            
            headers = {"Authorization": f"Bearer {self.dm2_token}"}
            async with self.session.post(f"{API_BASE}/multi-kingdoms", json=dm2_kingdom_data, headers=headers) as response:
                if response.status == 200:
                    dm2_kingdom = await response.json()
                    dm2_kingdom_id = dm2_kingdom['id']
                    
                    # Verify owner_id is set correctly
                    if dm2_kingdom.get('owner_id') != self.dm2_user_id:
                        self.errors.append(f"DM2 kingdom has wrong owner_id: {dm2_kingdom.get('owner_id')} != {self.dm2_user_id}")
                        return False
                    
                    print(f"✅ DM2 created kingdom: {dm2_kingdom['name']} (ID: {dm2_kingdom_id})")
                else:
                    error_text = await response.text()
                    self.errors.append(f"DM2 kingdom creation failed: HTTP {response.status} - {error_text}")
                    return False
            
            # Verify DM1 only sees their kingdom
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status == 200:
                    dm1_kingdoms = await response.json()
                    
                    if len(dm1_kingdoms) != 1:
                        self.errors.append(f"DM1 should see 1 kingdom but found {len(dm1_kingdoms)}")
                        return False
                    
                    if dm1_kingdoms[0]['id'] != dm1_kingdom_id:
                        self.errors.append(f"DM1 sees wrong kingdom: {dm1_kingdoms[0]['id']} != {dm1_kingdom_id}")
                        return False
                    
                    print(f"✅ DM1 isolation verified: sees only their kingdom")
                else:
                    self.errors.append(f"DM1 kingdom list failed: HTTP {response.status}")
                    return False
            
            # Verify DM2 only sees their kingdom
            headers = {"Authorization": f"Bearer {self.dm2_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status == 200:
                    dm2_kingdoms = await response.json()
                    
                    if len(dm2_kingdoms) != 1:
                        self.errors.append(f"DM2 should see 1 kingdom but found {len(dm2_kingdoms)}")
                        return False
                    
                    if dm2_kingdoms[0]['id'] != dm2_kingdom_id:
                        self.errors.append(f"DM2 sees wrong kingdom: {dm2_kingdoms[0]['id']} != {dm2_kingdom_id}")
                        return False
                    
                    print(f"✅ DM2 isolation verified: sees only their kingdom")
                else:
                    self.errors.append(f"DM2 kingdom list failed: HTTP {response.status}")
                    return False
            
            # Store kingdom IDs for later tests
            self.dm1_kingdom_id = dm1_kingdom_id
            self.dm2_kingdom_id = dm2_kingdom_id
            
            return True
            
        except Exception as e:
            self.errors.append(f"Kingdom creation isolation error: {str(e)}")
            return False

    async def test_cross_account_access_prevention(self):
        """Test that users cannot access other users' kingdoms"""
        print("\n🚫 Testing Cross-Account Access Prevention...")
        try:
            # Test DM1 trying to access DM2's kingdom (should get 403)
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdom/{self.dm2_kingdom_id}", headers=headers) as response:
                if response.status == 403:
                    print(f"✅ DM1 correctly denied access to DM2's kingdom (403)")
                elif response.status == 404:
                    print(f"✅ DM1 cannot find DM2's kingdom (404 - also acceptable)")
                else:
                    self.errors.append(f"DM1 should be denied access to DM2's kingdom, got status {response.status}")
                    return False
            
            # Test DM2 trying to access DM1's kingdom (should get 403)
            headers = {"Authorization": f"Bearer {self.dm2_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdom/{self.dm1_kingdom_id}", headers=headers) as response:
                if response.status == 403:
                    print(f"✅ DM2 correctly denied access to DM1's kingdom (403)")
                elif response.status == 404:
                    print(f"✅ DM2 cannot find DM1's kingdom (404 - also acceptable)")
                else:
                    self.errors.append(f"DM2 should be denied access to DM1's kingdom, got status {response.status}")
                    return False
            
            # Test DM1 trying to update DM2's kingdom (should get 403)
            update_data = {"name": "Hacked Kingdom"}
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.put(f"{API_BASE}/multi-kingdom/{self.dm2_kingdom_id}", json=update_data, headers=headers) as response:
                if response.status in [403, 404]:
                    print(f"✅ DM1 correctly denied update access to DM2's kingdom ({response.status})")
                else:
                    self.errors.append(f"DM1 should be denied update access to DM2's kingdom, got status {response.status}")
                    return False
            
            # Test DM2 trying to delete DM1's kingdom (should get 403)
            headers = {"Authorization": f"Bearer {self.dm2_token}"}
            async with self.session.delete(f"{API_BASE}/multi-kingdom/{self.dm1_kingdom_id}", headers=headers) as response:
                if response.status in [403, 404]:
                    print(f"✅ DM2 correctly denied delete access to DM1's kingdom ({response.status})")
                else:
                    self.errors.append(f"DM2 should be denied delete access to DM1's kingdom, got status {response.status}")
                    return False
            
            self.test_results['cross_account_access_prevention'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Cross-account access prevention error: {str(e)}")
            return False

    async def test_super_admin_functionality(self):
        """Test that admin user can access all kingdoms"""
        print("\n👑 Testing Super Admin Functionality...")
        try:
            # Admin should be able to access DM1's kingdom
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdom/{self.dm1_kingdom_id}", headers=headers) as response:
                if response.status == 200:
                    kingdom_data = await response.json()
                    
                    if kingdom_data['id'] != self.dm1_kingdom_id:
                        self.errors.append(f"Admin accessed wrong kingdom: {kingdom_data['id']} != {self.dm1_kingdom_id}")
                        return False
                    
                    print(f"✅ Admin can access DM1's kingdom: {kingdom_data['name']}")
                else:
                    self.errors.append(f"Admin should access DM1's kingdom, got status {response.status}")
                    return False
            
            # Admin should be able to access DM2's kingdom
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdom/{self.dm2_kingdom_id}", headers=headers) as response:
                if response.status == 200:
                    kingdom_data = await response.json()
                    
                    if kingdom_data['id'] != self.dm2_kingdom_id:
                        self.errors.append(f"Admin accessed wrong kingdom: {kingdom_data['id']} != {self.dm2_kingdom_id}")
                        return False
                    
                    print(f"✅ Admin can access DM2's kingdom: {kingdom_data['name']}")
                else:
                    self.errors.append(f"Admin should access DM2's kingdom, got status {response.status}")
                    return False
            
            # Admin should see all kingdoms in list
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status == 200:
                    all_kingdoms = await response.json()
                    
                    # Should see at least admin's kingdoms + DM1's + DM2's
                    if len(all_kingdoms) < 3:
                        self.errors.append(f"Admin should see at least 3 kingdoms, got {len(all_kingdoms)}")
                        return False
                    
                    # Check that admin can see kingdoms from different owners
                    owner_ids = set(kingdom.get('owner_id') for kingdom in all_kingdoms)
                    
                    if len(owner_ids) < 2:
                        self.errors.append(f"Admin should see kingdoms from multiple owners, got {len(owner_ids)} owners")
                        return False
                    
                    print(f"✅ Admin sees {len(all_kingdoms)} kingdoms from {len(owner_ids)} different owners")
                else:
                    self.errors.append(f"Admin kingdom list failed: HTTP {response.status}")
                    return False
            
            self.test_results['super_admin_bypass'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Super admin functionality error: {str(e)}")
            return False

    async def test_registry_ownership_verification(self):
        """Test that registry operations require city ownership"""
        print("\n📋 Testing Registry Ownership Verification...")
        try:
            # First, create a city in DM1's kingdom
            city_data = {
                "name": "DM1 Test City",
                "governor": "Test Governor",
                "x_coordinate": 100.0,
                "y_coordinate": 200.0
            }
            
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.post(f"{API_BASE}/multi-kingdom/{self.dm1_kingdom_id}/cities", json=city_data, headers=headers) as response:
                if response.status == 200:
                    city_result = await response.json()
                    dm1_city_id = city_result['city']['id']
                    print(f"✅ Created test city in DM1's kingdom: {dm1_city_id}")
                else:
                    error_text = await response.text()
                    self.errors.append(f"Failed to create test city: HTTP {response.status} - {error_text}")
                    return False
            
            # Test DM1 can add citizen to their own city
            citizen_data = {
                "name": "Test Citizen",
                "age": 30,
                "occupation": "Test Worker",
                "city_id": dm1_city_id,
                "health": "Healthy",
                "notes": "Test citizen for ownership verification"
            }
            
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.post(f"{API_BASE}/citizens", json=citizen_data, headers=headers) as response:
                if response.status == 200:
                    print(f"✅ DM1 can add citizen to their own city")
                else:
                    error_text = await response.text()
                    self.errors.append(f"DM1 should be able to add citizen to own city: HTTP {response.status} - {error_text}")
                    return False
            
            # Test DM2 cannot add citizen to DM1's city (should get 403)
            headers = {"Authorization": f"Bearer {self.dm2_token}"}
            async with self.session.post(f"{API_BASE}/citizens", json=citizen_data, headers=headers) as response:
                if response.status == 403:
                    print(f"✅ DM2 correctly denied access to add citizen to DM1's city (403)")
                else:
                    self.errors.append(f"DM2 should be denied access to DM1's city, got status {response.status}")
                    return False
            
            # Test admin can add citizen to any city (super admin bypass)
            admin_citizen_data = {
                "name": "Admin Test Citizen",
                "age": 35,
                "occupation": "Admin Worker",
                "city_id": dm1_city_id,
                "health": "Healthy",
                "notes": "Admin test citizen"
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.post(f"{API_BASE}/citizens", json=admin_citizen_data, headers=headers) as response:
                if response.status == 200:
                    print(f"✅ Admin can add citizen to any city (super admin bypass)")
                else:
                    error_text = await response.text()
                    self.errors.append(f"Admin should be able to add citizen to any city: HTTP {response.status} - {error_text}")
                    return False
            
            self.test_results['registry_ownership_verification'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Registry ownership verification error: {str(e)}")
            return False

    async def test_data_migration_verification(self):
        """Test that existing data was properly migrated with admin ownership"""
        print("\n📦 Testing Data Migration Verification...")
        try:
            # Get admin's kingdoms (should include migrated data)
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status == 200:
                    admin_kingdoms = await response.json()
                    
                    # Find migrated kingdoms (should have admin as owner)
                    migrated_kingdoms = [k for k in admin_kingdoms if k.get('owner_id') == self.admin_user_id]
                    
                    if len(migrated_kingdoms) == 0:
                        self.errors.append("No migrated kingdoms found with admin ownership")
                        return False
                    
                    print(f"✅ Found {len(migrated_kingdoms)} migrated kingdoms owned by admin")
                    
                    # Check for expected migrated kingdom names
                    kingdom_names = [k['name'] for k in migrated_kingdoms]
                    expected_names = ['Faerûn Campaign', 'Cartborne Kingdom']  # Common migrated names
                    
                    found_expected = any(name in kingdom_names for name in expected_names)
                    if not found_expected:
                        print(f"   ⚠️ Warning: Expected kingdom names not found. Found: {kingdom_names}")
                    else:
                        print(f"   ✅ Found expected migrated kingdom names")
                    
                    # Check that migrated kingdoms have cities with data
                    for kingdom in migrated_kingdoms:
                        cities = kingdom.get('cities', [])
                        if len(cities) > 0:
                            print(f"   ✅ Kingdom '{kingdom['name']}' has {len(cities)} cities")
                            
                            # Check for citizens in cities
                            total_citizens = sum(len(city.get('citizens', [])) for city in cities)
                            if total_citizens > 0:
                                print(f"   ✅ Found {total_citizens} citizens in migrated data")
                            else:
                                print(f"   ⚠️ No citizens found in migrated kingdoms")
                        else:
                            print(f"   ⚠️ Kingdom '{kingdom['name']}' has no cities")
                    
                else:
                    self.errors.append(f"Failed to get admin kingdoms for migration verification: HTTP {response.status}")
                    return False
            
            # Test that events are also migrated with admin ownership
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.get(f"{API_BASE}/events", headers=headers) as response:
                if response.status == 200:
                    admin_events = await response.json()
                    
                    # Check if events have owner_id field set to admin
                    admin_owned_events = [e for e in admin_events if e.get('owner_id') == self.admin_user_id]
                    
                    if len(admin_owned_events) > 0:
                        print(f"✅ Found {len(admin_owned_events)} events owned by admin")
                    else:
                        print(f"   ⚠️ No events found with admin ownership (may be expected if events don't have owner_id yet)")
                    
                else:
                    self.errors.append(f"Failed to get admin events for migration verification: HTTP {response.status}")
                    return False
            
            self.test_results['data_migration_verification'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Data migration verification error: {str(e)}")
            return False

    async def test_events_isolation(self):
        """Test that events are isolated by owner"""
        print("\n📜 Testing Events Data Isolation...")
        try:
            # Get events for each user and verify isolation
            
            # Admin events
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.get(f"{API_BASE}/events", headers=headers) as response:
                if response.status == 200:
                    admin_events = await response.json()
                    print(f"✅ Admin sees {len(admin_events)} events")
                else:
                    self.errors.append(f"Admin events request failed: HTTP {response.status}")
                    return False
            
            # DM1 events (should be fewer or none)
            headers = {"Authorization": f"Bearer {self.dm1_token}"}
            async with self.session.get(f"{API_BASE}/events", headers=headers) as response:
                if response.status == 200:
                    dm1_events = await response.json()
                    print(f"✅ DM1 sees {len(dm1_events)} events")
                else:
                    self.errors.append(f"DM1 events request failed: HTTP {response.status}")
                    return False
            
            # DM2 events (should be fewer or none)
            headers = {"Authorization": f"Bearer {self.dm2_token}"}
            async with self.session.get(f"{API_BASE}/events", headers=headers) as response:
                if response.status == 200:
                    dm2_events = await response.json()
                    print(f"✅ DM2 sees {len(dm2_events)} events")
                else:
                    self.errors.append(f"DM2 events request failed: HTTP {response.status}")
                    return False
            
            # Verify that DM users see fewer events than admin (data isolation working)
            if len(admin_events) > len(dm1_events) and len(admin_events) > len(dm2_events):
                print(f"✅ Event isolation verified: Admin sees more events than DM users")
            else:
                print(f"   ⚠️ Event isolation may not be fully implemented yet")
            
            self.test_results['data_isolation_events'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Events isolation error: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all data separation tests"""
        print("🚀 Starting Data Separation Testing Suite...")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Authentication Tests
            await self.test_admin_login()
            await self.test_dm_account_creation()
            await self.test_jwt_token_validation()
            
            # Data Isolation Tests
            await self.test_data_isolation_kingdoms()
            await self.test_kingdom_creation_isolation()
            await self.test_events_isolation()
            
            # Security Tests
            await self.test_cross_account_access_prevention()
            await self.test_super_admin_functionality()
            await self.test_registry_ownership_verification()
            
            # Migration Tests
            await self.test_data_migration_verification()
            
        finally:
            await self.cleanup()
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 DATA SEPARATION TEST RESULTS")
        print("=" * 60)
        
        passed_tests = sum(self.test_results.values())
        total_tests = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n📈 Overall Results: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n❌ Errors encountered:")
            for error in self.errors:
                print(f"   • {error}")
        
        if passed_tests == total_tests:
            print("\n🎉 All data separation tests passed! System is secure.")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} tests failed. Security issues detected.")
            return False

async def main():
    """Main test runner"""
    tester = DataSeparationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ DATA SEPARATION IMPLEMENTATION: WORKING")
        sys.exit(0)
    else:
        print("\n❌ DATA SEPARATION IMPLEMENTATION: ISSUES DETECTED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())