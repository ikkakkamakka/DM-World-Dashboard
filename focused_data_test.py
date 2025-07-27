#!/usr/bin/env python3
"""
Focused Data Loading Test for Review Request
Tests specific data loading issues after data separation implementation
"""

import asyncio
import aiohttp
import json
import sys

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

print(f"🔗 Testing backend at: {API_BASE}")

class FocusedDataLoadingTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = {}
        self.errors = []

    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def test_admin_login(self):
        """Test admin login to get JWT token"""
        print("\n🔐 Testing Admin Login...")
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                print(f"   Login response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    if 'access_token' in result:
                        self.admin_token = result['access_token']
                        user_info = result.get('user', {})
                        print(f"✅ Admin login successful")
                        print(f"   User: {user_info.get('username', 'Unknown')}")
                        print(f"   User ID: {user_info.get('id', 'Unknown')}")
                        return True
                    else:
                        self.errors.append("Login response missing access_token")
                        return False
                        
                else:
                    error_text = await response.text()
                    self.errors.append(f"Admin login failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Admin login error: {str(e)}")
            return False

    async def test_kingdom_data_loading(self):
        """Test GET /api/multi-kingdoms endpoint for authenticated users"""
        print("\n🏰 Testing Kingdom Data Loading...")
        try:
            if not self.admin_token:
                self.errors.append("No admin token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                print(f"   Multi-kingdoms response status: {response.status}")
                
                if response.status == 200:
                    kingdoms = await response.json()
                    print(f"✅ Kingdom data loading successful")
                    print(f"   Found {len(kingdoms)} kingdoms")
                    
                    if kingdoms:
                        kingdom = kingdoms[0]
                        print(f"   Sample kingdom: {kingdom.get('name', 'Unknown')}")
                        print(f"   Owner ID: {kingdom.get('owner_id', 'Missing!')}")
                        print(f"   Cities: {len(kingdom.get('cities', []))}")
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Kingdom data loading failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Kingdom data loading error: {str(e)}")
            return False

    async def test_city_data_access(self):
        """Test city data access with proper owner_id filtering"""
        print("\n🏘️ Testing City Data Access...")
        try:
            if not self.admin_token:
                self.errors.append("No admin token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # First get kingdoms to find cities
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status != 200:
                    self.errors.append("Cannot get kingdoms for city test")
                    return False
                
                kingdoms = await response.json()
                
                if not kingdoms:
                    print("   ⚠️ No kingdoms found")
                    return True
                
                # Find a city to test
                test_city = None
                for kingdom in kingdoms:
                    cities = kingdom.get('cities', [])
                    if cities:
                        test_city = cities[0]
                        break
                
                if not test_city:
                    print("   ⚠️ No cities found")
                    return True
                
                city_id = test_city['id']
                
                # Test city data access
                async with self.session.get(f"{API_BASE}/city/{city_id}", headers=headers) as city_response:
                    print(f"   City data response status: {city_response.status}")
                    
                    if city_response.status == 200:
                        city_data = await city_response.json()
                        print(f"✅ City data access successful")
                        print(f"   City: {city_data.get('name', 'Unknown')}")
                        print(f"   Population: {city_data.get('population', 0)}")
                        print(f"   Citizens: {len(city_data.get('citizens', []))}")
                        return True
                        
                    else:
                        error_text = await city_response.text()
                        self.errors.append(f"City data access failed: HTTP {city_response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.errors.append(f"City data access error: {str(e)}")
            return False

    async def test_government_hierarchy(self):
        """Test GET /api/cities/{city_id}/government endpoint"""
        print("\n🏛️ Testing Government Hierarchy...")
        try:
            if not self.admin_token:
                self.errors.append("No admin token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get a city ID
            city_id = await self.get_test_city_id(headers)
            if not city_id:
                print("   ⚠️ No cities available for government test")
                return True
            
            # Test government hierarchy endpoint
            async with self.session.get(f"{API_BASE}/cities/{city_id}/government", headers=headers) as response:
                print(f"   Government hierarchy response status: {response.status}")
                
                if response.status == 200:
                    gov_data = await response.json()
                    print(f"✅ Government hierarchy access successful")
                    
                    officials = gov_data.get('officials', [])
                    positions = gov_data.get('positions', [])
                    
                    print(f"   Available positions: {len(positions)}")
                    print(f"   Current officials: {len(officials)}")
                    
                    return True
                    
                elif response.status == 404:
                    print("   ⚠️ Government hierarchy endpoint not found")
                    return False
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Government hierarchy failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Government hierarchy error: {str(e)}")
            return False

    async def test_registry_data_access(self):
        """Test registry data access (citizens, slaves, livestock)"""
        print("\n📋 Testing Registry Data Access...")
        try:
            if not self.admin_token:
                self.errors.append("No admin token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get city data to check registries
            city_data = await self.get_test_city_data(headers)
            if not city_data:
                print("   ⚠️ No city data available for registry test")
                return True
            
            city_name = city_data.get('name', 'Unknown')
            
            # Check each registry type
            registries = {
                'citizens': city_data.get('citizens', []),
                'slaves': city_data.get('slaves', []),
                'livestock': city_data.get('livestock', [])
            }
            
            print(f"✅ Registry data access successful for city: {city_name}")
            
            for registry_name, items in registries.items():
                print(f"   {registry_name.title()}: {len(items)} items")
                if items:
                    sample = items[0]
                    name = sample.get('name', 'Unknown')
                    if registry_name == 'citizens':
                        occupation = sample.get('occupation', 'Unknown')
                        print(f"     Sample: {name} ({occupation})")
                    elif registry_name == 'livestock':
                        animal_type = sample.get('type', 'Unknown')
                        print(f"     Sample: {name} ({animal_type})")
                    else:
                        print(f"     Sample: {name}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Registry data access error: {str(e)}")
            return False

    async def test_authentication_flow(self):
        """Test JWT authentication flow"""
        print("\n🔐 Testing Authentication Flow...")
        try:
            # Test unauthenticated access (should fail)
            async with self.session.get(f"{API_BASE}/multi-kingdoms") as response:
                if response.status == 401:
                    print("   ✅ Unauthenticated access properly denied")
                else:
                    print(f"   ⚠️ Unauthenticated access returned {response.status} (expected 401)")
            
            # Test with valid token (should succeed)
            if self.admin_token:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                    if response.status == 200:
                        print("   ✅ Authenticated access successful")
                        return True
                    else:
                        self.errors.append(f"Authenticated access failed: {response.status}")
                        return False
            else:
                self.errors.append("No token available for authentication test")
                return False
                
        except Exception as e:
            self.errors.append(f"Authentication flow error: {str(e)}")
            return False

    async def get_test_city_id(self, headers):
        """Get a city ID for testing"""
        try:
            async with self.session.get(f"{API_BASE}/multi-kingdoms", headers=headers) as response:
                if response.status == 200:
                    kingdoms = await response.json()
                    for kingdom in kingdoms:
                        cities = kingdom.get('cities', [])
                        if cities:
                            return cities[0]['id']
                return None
        except:
            return None

    async def get_test_city_data(self, headers):
        """Get city data for testing"""
        try:
            city_id = await self.get_test_city_id(headers)
            if not city_id:
                return None
            
            async with self.session.get(f"{API_BASE}/city/{city_id}", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except:
            return None

    async def run_tests(self):
        """Run all focused tests"""
        print("🧪 Starting Focused Data Loading Tests...")
        print("=" * 60)
        
        await self.setup()
        
        try:
            tests = [
                ("Admin Login", self.test_admin_login),
                ("Kingdom Data Loading", self.test_kingdom_data_loading),
                ("City Data Access", self.test_city_data_access),
                ("Government Hierarchy", self.test_government_hierarchy),
                ("Registry Data Access", self.test_registry_data_access),
                ("Authentication Flow", self.test_authentication_flow)
            ]
            
            results = {}
            
            for test_name, test_func in tests:
                print(f"\n{'='*20} {test_name} {'='*20}")
                success = await test_func()
                results[test_name] = success
                
                if success:
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            
            # Print summary
            print("\n" + "="*60)
            print("📊 FOCUSED TEST RESULTS SUMMARY")
            print("="*60)
            
            passed = sum(results.values())
            total = len(results)
            
            print(f"\n✅ PASSED: {passed}/{total} tests")
            
            for test_name, result in results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {status} {test_name}")
            
            if self.errors:
                print(f"\n🚨 ERRORS ({len(self.errors)}):")
                for i, error in enumerate(self.errors, 1):
                    print(f"   {i}. {error}")
            
            print("\n" + "="*60)
            
            return passed == total
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = FocusedDataLoadingTester()
    success = await tester.run_tests()
    
    if success:
        print("🎉 All focused tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())