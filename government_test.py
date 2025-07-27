#!/usr/bin/env python3
"""
Focused test for Government Hierarchy System
Tests the government CRUD operations
"""

import asyncio
import aiohttp
import json
import sys
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

print(f"🔗 Testing government endpoints at: {API_BASE}")

class GovernmentTester:
    def __init__(self):
        self.session = None
        self.errors = []
        self.test_results = {}

    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def get_test_kingdom_and_city(self):
        """Get test kingdom and city data"""
        try:
            # Get kingdoms
            async with self.session.get(f"{API_BASE}/multi-kingdoms") as response:
                if response.status != 200:
                    self.errors.append("Failed to get kingdoms")
                    return None, None, None
                
                kingdoms = await response.json()
                if not kingdoms:
                    self.errors.append("No kingdoms found")
                    return None, None, None
                
                kingdom = kingdoms[0]
                kingdom_id = kingdom['id']
                
                # Get kingdom details
                async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom_id}") as response:
                    if response.status != 200:
                        self.errors.append("Failed to get kingdom details")
                        return None, None, None
                    
                    kingdom_data = await response.json()
                    cities = kingdom_data.get('cities', [])
                    
                    if not cities:
                        self.errors.append("No cities found in kingdom")
                        return None, None, None
                    
                    city = cities[0]
                    return kingdom_id, city['id'], city['name']
                    
        except Exception as e:
            self.errors.append(f"Error getting test data: {str(e)}")
            return None, None, None

    async def test_get_government_positions(self):
        """Test GET /api/government-positions endpoint"""
        print("\n📋 Testing Government Positions Retrieval...")
        try:
            async with self.session.get(f"{API_BASE}/government-positions") as response:
                if response.status == 200:
                    positions_data = await response.json()
                    
                    if 'positions' not in positions_data:
                        self.errors.append("Government positions response missing 'positions' field")
                        return False
                    
                    positions = positions_data['positions']
                    if not isinstance(positions, list):
                        self.errors.append("Government positions should be a list")
                        return False
                    
                    if len(positions) == 0:
                        self.errors.append("No government positions available")
                        return False
                    
                    # Check for expected positions
                    expected_positions = ["Captain of the Guard", "Master of Coin", "High Scribe", "Court Wizard", "Head Cleric"]
                    missing_positions = [pos for pos in expected_positions if pos not in positions]
                    
                    if missing_positions:
                        self.errors.append(f"Missing expected government positions: {missing_positions}")
                        return False
                    
                    print(f"   ✅ Retrieved {len(positions)} government positions")
                    print(f"   Sample positions: {', '.join(positions[:5])}")
                    return True
                    
                else:
                    self.errors.append(f"Government positions GET failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Government positions test error: {str(e)}")
            return False

    async def test_get_city_government(self, city_id, city_name):
        """Test GET /api/cities/{city_id}/government endpoint"""
        print(f"\n🏛️ Testing City Government Retrieval for {city_name}...")
        try:
            async with self.session.get(f"{API_BASE}/cities/{city_id}/government") as response:
                if response.status == 200:
                    government_data = await response.json()
                    
                    required_fields = ['city_id', 'city_name', 'government_officials']
                    missing_fields = [field for field in required_fields if field not in government_data]
                    
                    if missing_fields:
                        self.errors.append(f"City government response missing fields: {missing_fields}")
                        return False
                    
                    if government_data['city_id'] != city_id:
                        self.errors.append("City government response city_id mismatch")
                        return False
                    
                    officials = government_data['government_officials']
                    if not isinstance(officials, list):
                        self.errors.append("Government officials should be a list")
                        return False
                    
                    print(f"   ✅ Retrieved government data for {city_name}")
                    print(f"   Current officials: {len(officials)}")
                    
                    # Display current officials
                    if officials:
                        print("   Current government officials:")
                        for official in officials[:5]:  # Show first 5
                            print(f"     - {official['name']} ({official['position']})")
                        if len(officials) > 5:
                            print(f"     ... and {len(officials) - 5} more")
                    
                    # Store for later tests
                    self.test_city_government_data = government_data
                    return True
                    
                else:
                    self.errors.append(f"City government GET failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"City government test error: {str(e)}")
            return False

    async def test_appoint_citizen_to_government(self, city_id, city_name):
        """Test POST /api/cities/{city_id}/government/appoint endpoint"""
        print(f"\n👑 Testing Citizen Appointment to Government in {city_name}...")
        try:
            # First, get a citizen to appoint
            async with self.session.get(f"{API_BASE}/city/{city_id}") as response:
                if response.status != 200:
                    self.errors.append("Failed to get city data for appointment test")
                    return False
                
                city_data = await response.json()
                citizens = city_data.get('citizens', [])
                
                if not citizens:
                    self.errors.append("No citizens available for appointment test")
                    return False
                
                # Find a citizen without a government position
                available_citizen = None
                for citizen in citizens:
                    if not citizen.get('government_position'):
                        available_citizen = citizen
                        break
                
                if not available_citizen:
                    # Use the first citizen anyway
                    available_citizen = citizens[0]
                
                citizen_id = available_citizen['id']
                citizen_name = available_citizen['name']
            
            # Get initial official count
            async with self.session.get(f"{API_BASE}/cities/{city_id}/government") as response:
                if response.status == 200:
                    initial_data = await response.json()
                    initial_count = len(initial_data['government_officials'])
                else:
                    self.errors.append("Failed to get initial official count")
                    return False
            
            # Appoint citizen to a government position
            appointment_data = {
                "citizen_id": citizen_id,
                "position": "Tax Collector"
            }
            
            async with self.session.post(f"{API_BASE}/cities/{city_id}/government/appoint", json=appointment_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if 'message' not in result:
                        self.errors.append("Appointment response missing message")
                        return False
                    
                    print(f"   ✅ Appointment request successful: {result['message']}")
                    
                    # Verify the appointment was successful
                    await asyncio.sleep(2)
                    
                    async with self.session.get(f"{API_BASE}/cities/{city_id}/government") as verify_response:
                        if verify_response.status == 200:
                            government_data = await verify_response.json()
                            officials = government_data['government_officials']
                            new_count = len(officials)
                            
                            # Check if citizen was appointed
                            appointed_official = None
                            for official in officials:
                                if official.get('citizen_id') == citizen_id:
                                    appointed_official = official
                                    break
                            
                            if not appointed_official:
                                self.errors.append("Citizen not found in government officials after appointment")
                                return False
                            
                            if appointed_official['position'] != "Tax Collector":
                                self.errors.append("Appointed citizen has wrong position")
                                return False
                            
                            print(f"   ✅ {citizen_name} successfully appointed as Tax Collector")
                            print(f"   Government officials count: {initial_count} -> {new_count}")
                            
                            # Store for removal test
                            self.test_appointed_official_id = appointed_official['id']
                            self.test_appointed_citizen_id = citizen_id
                            return True
                        else:
                            self.errors.append("Failed to verify appointment")
                            return False
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Citizen appointment failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Citizen appointment test error: {str(e)}")
            return False

    async def test_remove_government_official(self, city_id, city_name):
        """Test DELETE /api/cities/{city_id}/government/{official_id} endpoint"""
        print(f"\n❌ Testing Government Official Removal in {city_name}...")
        try:
            if not hasattr(self, 'test_appointed_official_id'):
                self.errors.append("No appointed official ID available for removal test")
                return False
            
            official_id = self.test_appointed_official_id
            
            # Get initial official count
            async with self.session.get(f"{API_BASE}/cities/{city_id}/government") as response:
                if response.status == 200:
                    initial_data = await response.json()
                    initial_count = len(initial_data['government_officials'])
                    
                    # Find the official to remove
                    official_to_remove = None
                    for official in initial_data['government_officials']:
                        if official['id'] == official_id:
                            official_to_remove = official
                            break
                    
                    if not official_to_remove:
                        self.errors.append("Official to remove not found")
                        return False
                    
                    print(f"   Removing: {official_to_remove['name']} ({official_to_remove['position']})")
                    
                else:
                    self.errors.append("Failed to get initial official count")
                    return False
            
            # Remove the official
            async with self.session.delete(f"{API_BASE}/cities/{city_id}/government/{official_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if 'message' not in result:
                        self.errors.append("Removal response missing message")
                        return False
                    
                    print(f"   ✅ Removal request successful: {result['message']}")
                    
                    # Verify the removal was successful
                    await asyncio.sleep(2)
                    
                    async with self.session.get(f"{API_BASE}/cities/{city_id}/government") as verify_response:
                        if verify_response.status == 200:
                            government_data = await verify_response.json()
                            officials = government_data['government_officials']
                            new_count = len(officials)
                            
                            if new_count != initial_count - 1:
                                self.errors.append(f"Official count not updated after removal: {initial_count} -> {new_count}")
                                return False
                            
                            # Check that specific official is gone
                            removed_official = None
                            for official in officials:
                                if official['id'] == official_id:
                                    removed_official = official
                                    break
                            
                            if removed_official:
                                self.errors.append("Removed official still exists in government")
                                return False
                            
                            print(f"   ✅ Government official removed successfully")
                            print(f"   Government officials count: {initial_count} -> {new_count}")
                            
                            # Verify citizen's government position was cleared
                            if hasattr(self, 'test_appointed_citizen_id'):
                                async with self.session.get(f"{API_BASE}/city/{city_id}") as city_response:
                                    if city_response.status == 200:
                                        city_data = await city_response.json()
                                        citizens = city_data.get('citizens', [])
                                        
                                        for citizen in citizens:
                                            if citizen['id'] == self.test_appointed_citizen_id:
                                                if citizen.get('government_position'):
                                                    print(f"   ⚠️ Warning: Citizen still has government position: {citizen['government_position']}")
                                                else:
                                                    print(f"   ✅ Citizen's government position cleared correctly")
                                                break
                            
                            return True
                        else:
                            self.errors.append("Failed to verify official removal")
                            return False
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Official removal failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Official removal test error: {str(e)}")
            return False

    async def test_government_error_handling(self, city_id):
        """Test error handling for government endpoints"""
        print("\n⚠️ Testing Government Error Handling...")
        try:
            # Test appointment with invalid citizen_id
            invalid_appointment = {
                "citizen_id": "invalid-citizen-id-12345",
                "position": "Tax Collector"
            }
            
            async with self.session.post(f"{API_BASE}/cities/{city_id}/government/appoint", json=invalid_appointment) as response:
                if response.status == 404:
                    print(f"   ✅ Invalid citizen_id properly rejected with 404")
                else:
                    self.errors.append(f"Invalid citizen_id should return 404, got {response.status}")
                    return False
            
            # Test appointment with invalid position
            async with self.session.get(f"{API_BASE}/city/{city_id}") as response:
                if response.status == 200:
                    city_data = await response.json()
                    citizens = city_data.get('citizens', [])
                    if citizens:
                        invalid_position_appointment = {
                            "citizen_id": citizens[0]['id'],
                            "position": "Invalid Position That Does Not Exist"
                        }
                        
                        async with self.session.post(f"{API_BASE}/cities/{city_id}/government/appoint", json=invalid_position_appointment) as response:
                            if response.status in [400, 422]:
                                print(f"   ✅ Invalid position properly rejected with {response.status}")
                            else:
                                print(f"   ⚠️ Invalid position returned {response.status} (may be allowed)")
            
            # Test removal with invalid official_id
            async with self.session.delete(f"{API_BASE}/cities/{city_id}/government/invalid-official-id") as response:
                if response.status == 404:
                    print(f"   ✅ Invalid official_id properly rejected with 404")
                    return True
                else:
                    self.errors.append(f"Invalid official_id should return 404, got {response.status}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Government error handling test error: {str(e)}")
            return False

    async def test_government_data_persistence(self, city_id, kingdom_id):
        """Test that government data persists correctly in multi_kingdoms collection"""
        print("\n💾 Testing Government Data Persistence...")
        try:
            # Get current government data
            async with self.session.get(f"{API_BASE}/cities/{city_id}/government") as response:
                if response.status != 200:
                    self.errors.append("Failed to get government data for persistence test")
                    return False
                
                government_data = await response.json()
                officials_count = len(government_data['government_officials'])
            
            # Verify it exists in the multi_kingdoms collection
            async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom_id}") as response:
                if response.status == 200:
                    kingdom_data = await response.json()
                    
                    # Find the city and check government officials
                    target_city = None
                    for city in kingdom_data.get('cities', []):
                        if city['id'] == city_id:
                            target_city = city
                            break
                    
                    if not target_city:
                        self.errors.append("Target city not found in kingdom data")
                        return False
                    
                    # Check government officials count matches
                    kingdom_officials_count = len(target_city.get('government_officials', []))
                    
                    if kingdom_officials_count != officials_count:
                        self.errors.append(f"Government officials count mismatch: API={officials_count}, Kingdom={kingdom_officials_count}")
                        return False
                    
                    print(f"   ✅ Government data persisted correctly in multi_kingdoms collection")
                    print(f"   Officials count matches: {officials_count}")
                    return True
                    
                else:
                    self.errors.append("Failed to retrieve kingdom data for persistence test")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Government persistence test error: {str(e)}")
            return False

    async def run_tests(self):
        """Run all government tests"""
        print("🚀 Starting Government Hierarchy System Tests")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Get test data
            kingdom_id, city_id, city_name = await self.get_test_kingdom_and_city()
            if not kingdom_id:
                print("❌ Failed to get test data")
                return False
            
            print(f"📍 Testing with Kingdom ID: {kingdom_id}")
            print(f"📍 Testing with City: {city_name} (ID: {city_id})")
            
            # Test all government endpoints
            tests = [
                ("Get Government Positions", self.test_get_government_positions, []),
                ("Get City Government", self.test_get_city_government, [city_id, city_name]),
                ("Appoint Citizen", self.test_appoint_citizen_to_government, [city_id, city_name]),
                ("Remove Official", self.test_remove_government_official, [city_id, city_name]),
                ("Error Handling", self.test_government_error_handling, [city_id]),
                ("Data Persistence", self.test_government_data_persistence, [city_id, kingdom_id]),
            ]
            
            results = {}
            for test_name, test_func, args in tests:
                success = await test_func(*args)
                results[test_name] = success
                self.test_results[test_name] = success
            
        finally:
            await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 GOVERNMENT HIERARCHY TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if self.errors:
            print("\n🚨 ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")
        
        return passed == total

async def main():
    """Main test runner"""
    tester = GovernmentTester()
    success = await tester.run_tests()
    
    if success:
        print("\n🎉 All government hierarchy tests passed!")
        return 0
    else:
        print("\n💥 Some government hierarchy tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)