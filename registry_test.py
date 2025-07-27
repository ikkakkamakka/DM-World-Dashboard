#!/usr/bin/env python3
"""
Focused test for Registry Creation Endpoints
Tests the recently fixed city management registry endpoints
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

print(f"🔗 Testing registry endpoints at: {API_BASE}")

class RegistryTester:
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

    async def get_registry_count(self, city_id, registry_type):
        """Get current count of items in a registry"""
        try:
            async with self.session.get(f"{API_BASE}/city/{city_id}") as response:
                if response.status == 200:
                    city_data = await response.json()
                    
                    registry_map = {
                        "citizens": "citizens",
                        "slaves": "slaves", 
                        "livestock": "livestock",
                        "garrison": "garrison",
                        "crimes": "crime_records",
                        "tribute": "tribute_records"
                    }
                    
                    registry_key = registry_map.get(registry_type, registry_type)
                    items = city_data.get(registry_key, [])
                    return len(items)
                else:
                    return 0
        except:
            return 0

    async def test_create_citizen(self, city_id, city_name):
        """Test POST /api/citizens endpoint"""
        print("\n🧑 Testing Citizen Creation...")
        try:
            initial_count = await self.get_registry_count(city_id, "citizens")
            
            citizen_data = {
                "name": "Test Citizen Aldric",
                "age": 35,
                "occupation": "Test Blacksmith",
                "city_id": city_id,
                "health": "Healthy",
                "notes": "Created by automated test"
            }
            
            async with self.session.post(f"{API_BASE}/citizens", json=citizen_data) as response:
                if response.status == 200:
                    created_citizen = await response.json()
                    
                    # Verify response structure
                    required_fields = ['id', 'name', 'age', 'occupation', 'city_id', 'health']
                    missing_fields = [field for field in required_fields if field not in created_citizen]
                    
                    if missing_fields:
                        self.errors.append(f"Created citizen missing fields: {missing_fields}")
                        return False
                    
                    # Verify data matches
                    if created_citizen['name'] != citizen_data['name']:
                        self.errors.append("Created citizen name doesn't match input")
                        return False
                    
                    if created_citizen['city_id'] != city_id:
                        self.errors.append("Created citizen city_id doesn't match")
                        return False
                    
                    # Wait for database update
                    await asyncio.sleep(2)
                    
                    # Verify database was updated
                    new_count = await self.get_registry_count(city_id, "citizens")
                    if new_count != initial_count + 1:
                        self.errors.append(f"Citizen database not updated: {initial_count} -> {new_count}")
                        return False
                    
                    print(f"   ✅ Citizen created: {created_citizen['name']} in {city_name}")
                    print(f"   Database updated: {initial_count} -> {new_count} citizens")
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Citizen creation failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Citizen creation test error: {str(e)}")
            return False

    async def test_create_slave(self, city_id, city_name):
        """Test POST /api/slaves endpoint"""
        print("\n⛓️ Testing Slave Creation...")
        try:
            initial_count = await self.get_registry_count(city_id, "slaves")
            
            slave_data = {
                "name": "Test Slave Keth",
                "age": 28,
                "origin": "Test Captured",
                "occupation": "Test Laborer",
                "owner": "Test City",
                "purchase_price": 75,
                "city_id": city_id,
                "health": "Healthy",
                "notes": "Created by automated test"
            }
            
            async with self.session.post(f"{API_BASE}/slaves", json=slave_data) as response:
                if response.status == 200:
                    created_slave = await response.json()
                    
                    required_fields = ['id', 'name', 'age', 'origin', 'occupation', 'owner', 'city_id']
                    missing_fields = [field for field in required_fields if field not in created_slave]
                    
                    if missing_fields:
                        self.errors.append(f"Created slave missing fields: {missing_fields}")
                        return False
                    
                    if created_slave['city_id'] != city_id:
                        self.errors.append("Created slave city_id doesn't match")
                        return False
                    
                    await asyncio.sleep(2)
                    
                    new_count = await self.get_registry_count(city_id, "slaves")
                    if new_count != initial_count + 1:
                        self.errors.append(f"Slave database not updated: {initial_count} -> {new_count}")
                        return False
                    
                    print(f"   ✅ Slave created: {created_slave['name']} in {city_name}")
                    print(f"   Database updated: {initial_count} -> {new_count} slaves")
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Slave creation failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Slave creation test error: {str(e)}")
            return False

    async def test_create_livestock(self, city_id, city_name):
        """Test POST /api/livestock endpoint"""
        print("\n🐄 Testing Livestock Creation...")
        try:
            initial_count = await self.get_registry_count(city_id, "livestock")
            
            livestock_data = {
                "name": "Test Thunder",
                "type": "Horse",
                "age": 4,
                "health": "Healthy",
                "weight": 1100,
                "value": 280,
                "city_id": city_id,
                "owner": "Test City",
                "notes": "Created by automated test"
            }
            
            async with self.session.post(f"{API_BASE}/livestock", json=livestock_data) as response:
                if response.status == 200:
                    created_livestock = await response.json()
                    
                    required_fields = ['id', 'name', 'type', 'age', 'health', 'weight', 'value', 'city_id']
                    missing_fields = [field for field in required_fields if field not in created_livestock]
                    
                    if missing_fields:
                        self.errors.append(f"Created livestock missing fields: {missing_fields}")
                        return False
                    
                    if created_livestock['city_id'] != city_id:
                        self.errors.append("Created livestock city_id doesn't match")
                        return False
                    
                    await asyncio.sleep(2)
                    
                    new_count = await self.get_registry_count(city_id, "livestock")
                    if new_count != initial_count + 1:
                        self.errors.append(f"Livestock database not updated: {initial_count} -> {new_count}")
                        return False
                    
                    print(f"   ✅ Livestock created: {created_livestock['name']} ({created_livestock['type']}) in {city_name}")
                    print(f"   Database updated: {initial_count} -> {new_count} livestock")
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Livestock creation failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Livestock creation test error: {str(e)}")
            return False

    async def test_create_soldier(self, city_id, city_name):
        """Test POST /api/soldiers endpoint"""
        print("\n⚔️ Testing Soldier Creation...")
        try:
            initial_count = await self.get_registry_count(city_id, "garrison")
            
            soldier_data = {
                "name": "Test Captain Steel",
                "rank": "Captain",
                "age": 32,
                "years_of_service": 8,
                "equipment": ["Sword", "Shield", "Chain Mail"],
                "status": "Active",
                "city_id": city_id,
                "notes": "Created by automated test"
            }
            
            async with self.session.post(f"{API_BASE}/soldiers", json=soldier_data) as response:
                if response.status == 200:
                    created_soldier = await response.json()
                    
                    required_fields = ['id', 'name', 'rank', 'age', 'years_of_service', 'equipment', 'city_id']
                    missing_fields = [field for field in required_fields if field not in created_soldier]
                    
                    if missing_fields:
                        self.errors.append(f"Created soldier missing fields: {missing_fields}")
                        return False
                    
                    if created_soldier['city_id'] != city_id:
                        self.errors.append("Created soldier city_id doesn't match")
                        return False
                    
                    await asyncio.sleep(2)
                    
                    new_count = await self.get_registry_count(city_id, "garrison")
                    if new_count != initial_count + 1:
                        self.errors.append(f"Soldier database not updated: {initial_count} -> {new_count}")
                        return False
                    
                    print(f"   ✅ Soldier created: {created_soldier['rank']} {created_soldier['name']} in {city_name}")
                    print(f"   Database updated: {initial_count} -> {new_count} soldiers")
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Soldier creation failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Soldier creation test error: {str(e)}")
            return False

    async def test_create_tribute(self, city_id, city_name):
        """Test POST /api/tribute endpoint"""
        print("\n💰 Testing Tribute Creation...")
        try:
            initial_count = await self.get_registry_count(city_id, "tribute")
            
            tribute_data = {
                "from_city": city_name,
                "to_city": "Royal Treasury",
                "amount": 150,
                "type": "Gold",
                "purpose": "Test Annual Tribute",
                "due_date": "2025-02-01T00:00:00Z",
                "notes": "Created by automated test"
            }
            
            async with self.session.post(f"{API_BASE}/tribute", json=tribute_data) as response:
                if response.status == 200:
                    created_tribute = await response.json()
                    
                    required_fields = ['id', 'from_city', 'to_city', 'amount', 'type', 'purpose']
                    missing_fields = [field for field in required_fields if field not in created_tribute]
                    
                    if missing_fields:
                        self.errors.append(f"Created tribute missing fields: {missing_fields}")
                        return False
                    
                    if created_tribute['from_city'] != city_name:
                        self.errors.append("Created tribute from_city doesn't match")
                        return False
                    
                    await asyncio.sleep(2)
                    
                    new_count = await self.get_registry_count(city_id, "tribute")
                    if new_count != initial_count + 1:
                        self.errors.append(f"Tribute database not updated: {initial_count} -> {new_count}")
                        return False
                    
                    print(f"   ✅ Tribute created: {created_tribute['amount']} GP from {created_tribute['from_city']}")
                    print(f"   Database updated: {initial_count} -> {new_count} tribute records")
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Tribute creation failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Tribute creation test error: {str(e)}")
            return False

    async def test_create_crime(self, city_id, city_name):
        """Test POST /api/crimes endpoint"""
        print("\n🚨 Testing Crime Creation...")
        try:
            initial_count = await self.get_registry_count(city_id, "crimes")
            
            crime_data = {
                "criminal_name": "Test Criminal Bob",
                "crime_type": "Petty Theft",
                "description": "Accused of stealing bread from the market",
                "city_id": city_id,
                "punishment": "3 days in stocks",
                "fine_amount": 5,
                "date_occurred": "2025-01-15T10:00:00Z",
                "notes": "Created by automated test"
            }
            
            async with self.session.post(f"{API_BASE}/crimes", json=crime_data) as response:
                if response.status == 200:
                    created_crime = await response.json()
                    
                    required_fields = ['id', 'criminal_name', 'crime_type', 'description', 'city_id', 'punishment']
                    missing_fields = [field for field in required_fields if field not in created_crime]
                    
                    if missing_fields:
                        self.errors.append(f"Created crime missing fields: {missing_fields}")
                        return False
                    
                    if created_crime['city_id'] != city_id:
                        self.errors.append("Created crime city_id doesn't match")
                        return False
                    
                    await asyncio.sleep(2)
                    
                    new_count = await self.get_registry_count(city_id, "crimes")
                    if new_count != initial_count + 1:
                        self.errors.append(f"Crime database not updated: {initial_count} -> {new_count}")
                        return False
                    
                    print(f"   ✅ Crime created: {created_crime['criminal_name']} - {created_crime['crime_type']} in {city_name}")
                    print(f"   Database updated: {initial_count} -> {new_count} crime records")
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Crime creation failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Crime creation test error: {str(e)}")
            return False

    async def test_error_handling(self, city_id):
        """Test error handling for invalid requests"""
        print("\n⚠️ Testing Error Handling...")
        try:
            # Test with invalid city_id
            invalid_citizen_data = {
                "name": "Invalid Test",
                "age": 30,
                "occupation": "Test",
                "city_id": "invalid-city-id-12345",
                "health": "Healthy"
            }
            
            async with self.session.post(f"{API_BASE}/citizens", json=invalid_citizen_data) as response:
                if response.status == 404:
                    print(f"   ✅ Invalid city_id properly rejected with 404")
                else:
                    self.errors.append(f"Invalid city_id should return 404, got {response.status}")
                    return False
            
            # Test with missing required fields
            incomplete_citizen_data = {
                "name": "Incomplete Test"
                # Missing required fields
            }
            
            async with self.session.post(f"{API_BASE}/citizens", json=incomplete_citizen_data) as response:
                if response.status in [400, 422]:  # Bad request or validation error
                    print(f"   ✅ Missing required fields properly rejected with {response.status}")
                    return True
                else:
                    self.errors.append(f"Missing fields should return 400/422, got {response.status}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Error handling test error: {str(e)}")
            return False

    async def test_government_endpoints(self, city_id, city_name):
        """Test government hierarchy endpoints"""
        print("\n🏛️ Testing Government Hierarchy...")
        
        # Test get government positions
        try:
            async with self.session.get(f"{API_BASE}/government-positions") as response:
                if response.status == 200:
                    positions_data = await response.json()
                    positions = positions_data.get('positions', [])
                    print(f"   ✅ Retrieved {len(positions)} government positions")
                else:
                    self.errors.append(f"Government positions failed: {response.status}")
                    return False
        except Exception as e:
            self.errors.append(f"Government positions error: {str(e)}")
            return False
        
        # Test get city government
        try:
            async with self.session.get(f"{API_BASE}/cities/{city_id}/government") as response:
                if response.status == 200:
                    government_data = await response.json()
                    officials = government_data.get('government_officials', [])
                    print(f"   ✅ Retrieved government data for {city_name} ({len(officials)} officials)")
                    return True
                else:
                    self.errors.append(f"City government failed: {response.status}")
                    return False
        except Exception as e:
            self.errors.append(f"City government error: {str(e)}")
            return False

    async def run_tests(self):
        """Run all registry tests"""
        print("🚀 Starting Registry Creation Endpoint Tests")
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
            
            # Test all registry creation endpoints
            tests = [
                ("Citizens", self.test_create_citizen),
                ("Slaves", self.test_create_slave),
                ("Livestock", self.test_create_livestock),
                ("Soldiers", self.test_create_soldier),
                ("Tribute", self.test_create_tribute),
                ("Crimes", self.test_create_crime),
            ]
            
            results = {}
            for test_name, test_func in tests:
                success = await test_func(city_id, city_name)
                results[test_name] = success
                self.test_results[test_name] = success
            
            # Test error handling
            error_handling_success = await self.test_error_handling(city_id)
            results["Error Handling"] = error_handling_success
            self.test_results["Error Handling"] = error_handling_success
            
            # Test government endpoints
            government_success = await self.test_government_endpoints(city_id, city_name)
            results["Government Hierarchy"] = government_success
            self.test_results["Government Hierarchy"] = government_success
            
        finally:
            await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 REGISTRY TEST SUMMARY")
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
    tester = RegistryTester()
    success = await tester.run_tests()
    
    if success:
        print("\n🎉 All registry tests passed!")
        return 0
    else:
        print("\n💥 Some registry tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)