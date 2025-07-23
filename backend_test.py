#!/usr/bin/env python3
"""
Backend Testing Suite for Fantasy Kingdom Management System
Tests all API endpoints, WebSocket connections, database operations, and simulation engine
"""

import asyncio
import aiohttp
import websockets
import json
import time
from datetime import datetime
import sys
import os

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
WS_URL = f"{BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws"

print(f"🔗 Testing backend at: {API_BASE}")
print(f"🔗 WebSocket URL: {WS_URL}")

class BackendTester:
    def __init__(self):
        self.session = None
        self.test_results = {
            'kingdom_api': False,
            'city_api': False,
            'events_api': False,
            'websocket_connection': False,
            'database_initialization': False,
            'simulation_engine': False,
            'auto_generate_citizens': False,
            'auto_generate_slaves': False,
            'auto_generate_livestock': False,
            'auto_generate_garrison': False,
            'auto_generate_crimes': False,
            'auto_generate_tribute': False
        }
        self.errors = []

    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def test_kingdom_api(self):
        """Test /api/kingdom endpoint"""
        print("\n🏰 Testing Kingdom API endpoint...")
        try:
            async with self.session.get(f"{API_BASE}/kingdom") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify kingdom structure
                    required_fields = ['name', 'ruler', 'total_population', 'royal_treasury', 'cities']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.errors.append(f"Kingdom API missing fields: {missing_fields}")
                        return False
                    
                    # Check if it's Cartborne Kingdom
                    if data['name'] != 'Cartborne Kingdom':
                        self.errors.append(f"Expected 'Cartborne Kingdom', got '{data['name']}'")
                        return False
                    
                    # Check if cities exist
                    if len(data['cities']) < 2:
                        self.errors.append(f"Expected at least 2 cities, got {len(data['cities'])}")
                        return False
                    
                    # Check for Emberfalls and Stormhaven
                    city_names = [city['name'] for city in data['cities']]
                    expected_cities = ['Emberfalls', 'Stormhaven']
                    missing_cities = [city for city in expected_cities if city not in city_names]
                    
                    if missing_cities:
                        self.errors.append(f"Missing expected cities: {missing_cities}")
                        return False
                    
                    print(f"✅ Kingdom API working - Found {data['name']} with {len(data['cities'])} cities")
                    print(f"   Cities: {', '.join(city_names)}")
                    print(f"   Total Population: {data['total_population']}")
                    print(f"   Royal Treasury: {data['royal_treasury']}")
                    
                    self.test_results['kingdom_api'] = True
                    return True
                else:
                    self.errors.append(f"Kingdom API returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Kingdom API error: {str(e)}")
            return False

    async def test_city_api(self):
        """Test /api/city/{city_id} endpoint"""
        print("\n🏘️ Testing City API endpoint...")
        try:
            # First get kingdom to find city IDs
            async with self.session.get(f"{API_BASE}/kingdom") as response:
                if response.status != 200:
                    self.errors.append("Cannot test City API - Kingdom API failed")
                    return False
                
                kingdom_data = await response.json()
                cities = kingdom_data.get('cities', [])
                
                if not cities:
                    self.errors.append("No cities found in kingdom data")
                    return False
                
                # Test first city
                test_city = cities[0]
                city_id = test_city['id']
                
                async with self.session.get(f"{API_BASE}/city/{city_id}") as city_response:
                    if city_response.status == 200:
                        city_data = await city_response.json()
                        
                        # Verify city structure
                        required_fields = ['id', 'name', 'governor', 'population', 'treasury', 'citizens']
                        missing_fields = [field for field in required_fields if field not in city_data]
                        
                        if missing_fields:
                            self.errors.append(f"City API missing fields: {missing_fields}")
                            return False
                        
                        # Check if citizens exist
                        citizens = city_data.get('citizens', [])
                        if not citizens:
                            self.errors.append("City has no citizens")
                            return False
                        
                        # Check citizen structure
                        citizen = citizens[0]
                        citizen_fields = ['id', 'name', 'age', 'occupation', 'city_id']
                        missing_citizen_fields = [field for field in citizen_fields if field not in citizen]
                        
                        if missing_citizen_fields:
                            self.errors.append(f"Citizen data missing fields: {missing_citizen_fields}")
                            return False
                        
                        print(f"✅ City API working - Found {city_data['name']}")
                        print(f"   Governor: {city_data['governor']}")
                        print(f"   Population: {city_data['population']}")
                        print(f"   Citizens: {len(citizens)}")
                        print(f"   Sample citizen: {citizen['name']} ({citizen['occupation']})")
                        
                        self.test_results['city_api'] = True
                        return True
                    else:
                        self.errors.append(f"City API returned status {city_response.status}")
                        return False
                        
        except Exception as e:
            self.errors.append(f"City API error: {str(e)}")
            return False

    async def test_events_api(self):
        """Test /api/events endpoint"""
        print("\n📜 Testing Events API endpoint...")
        try:
            async with self.session.get(f"{API_BASE}/events") as response:
                if response.status == 200:
                    events = await response.json()
                    
                    if not isinstance(events, list):
                        self.errors.append("Events API should return a list")
                        return False
                    
                    print(f"✅ Events API working - Found {len(events)} events")
                    
                    if events:
                        # Check event structure
                        event = events[0]
                        required_fields = ['id', 'description', 'city_name', 'kingdom_name', 'timestamp']
                        missing_fields = [field for field in required_fields if field not in event]
                        
                        if missing_fields:
                            self.errors.append(f"Event data missing fields: {missing_fields}")
                            return False
                        
                        print(f"   Latest event: {event['description']}")
                        print(f"   City: {event['city_name']}")
                        print(f"   Kingdom: {event['kingdom_name']}")
                    else:
                        print("   No events found yet (simulation may still be starting)")
                    
                    self.test_results['events_api'] = True
                    return True
                else:
                    self.errors.append(f"Events API returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Events API error: {str(e)}")
            return False

    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        print("\n🔌 Testing WebSocket connection...")
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Send a test message
                test_message = "Hello from test client"
                await websocket.send(test_message)
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                if "Message received" in response:
                    print("✅ WebSocket connection working - Echo response received")
                    self.test_results['websocket_connection'] = True
                    return True
                else:
                    self.errors.append(f"Unexpected WebSocket response: {response}")
                    return False
                    
        except asyncio.TimeoutError:
            self.errors.append("WebSocket connection timeout")
            return False
        except Exception as e:
            self.errors.append(f"WebSocket error: {str(e)}")
            return False

    async def test_database_initialization(self):
        """Test if database is properly initialized with kingdom data"""
        print("\n🗄️ Testing Database Initialization...")
        try:
            # Test kingdom data exists
            async with self.session.get(f"{API_BASE}/kingdom") as response:
                if response.status != 200:
                    self.errors.append("Database initialization failed - no kingdom data")
                    return False
                
                kingdom_data = await response.json()
                
                # Check for pre-populated data
                expected_citizens = ["Thorin Emberthane", "Elena Brightwater", "Gareth Stormwind", "Aria Moonwhisper"]
                found_citizens = []
                
                for city in kingdom_data.get('cities', []):
                    for citizen in city.get('citizens', []):
                        found_citizens.append(citizen['name'])
                
                missing_citizens = [name for name in expected_citizens if name not in found_citizens]
                
                if len(missing_citizens) > 2:  # Allow some flexibility
                    self.errors.append(f"Database missing expected citizens: {missing_citizens}")
                    return False
                
                print("✅ Database initialization working")
                print(f"   Found citizens: {', '.join(found_citizens[:5])}...")
                print(f"   Total citizens across all cities: {len(found_citizens)}")
                
                self.test_results['database_initialization'] = True
                return True
                
        except Exception as e:
            self.errors.append(f"Database initialization test error: {str(e)}")
            return False

    async def test_auto_generate_functionality(self):
        """Test auto-generate functionality for all registry types"""
        print("\n🎲 Testing Auto-Generate Functionality...")
        
        # First get kingdom data to find city IDs
        try:
            async with self.session.get(f"{API_BASE}/kingdom") as response:
                if response.status != 200:
                    self.errors.append("Cannot test auto-generate - Kingdom API failed")
                    return False
                
                kingdom_data = await response.json()
                cities = kingdom_data.get('cities', [])
                
                if not cities:
                    self.errors.append("No cities found for auto-generate testing")
                    return False
                
                test_city = cities[0]  # Use first city for testing
                city_id = test_city['id']
                city_name = test_city['name']
                
                print(f"   Testing with city: {city_name} (ID: {city_id})")
                
                # Test each registry type
                registry_types = ["citizens", "slaves", "livestock", "garrison", "crimes", "tribute"]
                results = {}
                
                for registry_type in registry_types:
                    print(f"\n   🔄 Testing auto-generate for {registry_type}...")
                    success = await self.test_single_registry_autogenerate(city_id, city_name, registry_type)
                    results[f'auto_generate_{registry_type}'] = success
                    self.test_results[f'auto_generate_{registry_type}'] = success
                
                # Summary for auto-generate tests
                passed_auto_tests = sum(results.values())
                total_auto_tests = len(results)
                
                print(f"\n   📊 Auto-Generate Summary: {passed_auto_tests}/{total_auto_tests} registry types working")
                
                return passed_auto_tests == total_auto_tests
                
        except Exception as e:
            self.errors.append(f"Auto-generate test setup error: {str(e)}")
            return False

    async def test_single_registry_autogenerate(self, city_id, city_name, registry_type):
        """Test auto-generate for a single registry type"""
        try:
            # Get initial count of items in this registry
            initial_count = await self.get_registry_count(city_id, registry_type)
            
            # Make auto-generate request
            payload = {
                "registry_type": registry_type,
                "city_id": city_id,
                "count": 2  # Generate 2 items
            }
            
            async with self.session.post(f"{API_BASE}/auto-generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Check response structure
                    if 'generated_items' not in result or 'count' not in result:
                        self.errors.append(f"Auto-generate {registry_type}: Invalid response structure")
                        return False
                    
                    generated_items = result['generated_items']
                    generated_count = result['count']
                    
                    if generated_count != 2:
                        self.errors.append(f"Auto-generate {registry_type}: Expected 2 items, got {generated_count}")
                        return False
                    
                    if len(generated_items) != 2:
                        self.errors.append(f"Auto-generate {registry_type}: Generated items count mismatch")
                        return False
                    
                    # Verify items have proper structure
                    for item in generated_items:
                        if not self.validate_generated_item(item, registry_type, city_id):
                            self.errors.append(f"Auto-generate {registry_type}: Invalid item structure")
                            return False
                    
                    # Wait a moment for database to update
                    await asyncio.sleep(1)
                    
                    # Verify items were stored in database
                    new_count = await self.get_registry_count(city_id, registry_type)
                    expected_new_count = initial_count + 2
                    
                    if new_count != expected_new_count:
                        self.errors.append(f"Auto-generate {registry_type}: Database not updated. Expected {expected_new_count}, got {new_count}")
                        return False
                    
                    # Check if event was generated
                    event_generated = await self.check_recent_event_for_registry(registry_type, city_name)
                    if not event_generated:
                        print(f"      ⚠️ Warning: No recent event found for {registry_type} auto-generation")
                    
                    print(f"      ✅ {registry_type}: Generated 2 items, database updated, count: {initial_count} → {new_count}")
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Auto-generate {registry_type}: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Auto-generate {registry_type} error: {str(e)}")
            return False

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

    def validate_generated_item(self, item, registry_type, city_id):
        """Validate structure of generated item"""
        try:
            # Common fields all items should have
            if 'id' not in item:
                return False
            
            # Registry-specific validation
            if registry_type == "citizens":
                required_fields = ['name', 'age', 'occupation', 'city_id', 'health']
                return all(field in item for field in required_fields) and item['city_id'] == city_id
                
            elif registry_type == "slaves":
                required_fields = ['name', 'age', 'origin', 'occupation', 'owner', 'city_id']
                return all(field in item for field in required_fields) and item['city_id'] == city_id
                
            elif registry_type == "livestock":
                required_fields = ['name', 'type', 'age', 'health', 'weight', 'value', 'city_id']
                return all(field in item for field in required_fields) and item['city_id'] == city_id
                
            elif registry_type == "garrison":
                required_fields = ['name', 'rank', 'age', 'years_of_service', 'city_id']
                return all(field in item for field in required_fields) and item['city_id'] == city_id
                
            elif registry_type == "crimes":
                required_fields = ['criminal_name', 'crime_type', 'description', 'city_id', 'punishment']
                return all(field in item for field in required_fields) and item['city_id'] == city_id
                
            elif registry_type == "tribute":
                required_fields = ['from_city', 'to_city', 'amount', 'type', 'purpose']
                return all(field in item for field in required_fields)
                
            return False
            
        except:
            return False

    async def check_recent_event_for_registry(self, registry_type, city_name):
        """Check if a recent event was generated for the registry type"""
        try:
            async with self.session.get(f"{API_BASE}/events?limit=10") as response:
                if response.status == 200:
                    events = await response.json()
                    
                    # Look for recent events (within last 30 seconds) related to this registry
                    current_time = datetime.utcnow()
                    
                    for event in events:
                        event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                        time_diff = (current_time - event_time.replace(tzinfo=None)).total_seconds()
                        
                        if time_diff <= 30:  # Within last 30 seconds
                            description = event['description'].lower()
                            city_match = city_name.lower() in description
                            
                            # Check for registry-specific keywords
                            registry_keywords = {
                                "citizens": ["citizen", "joins", "registers"],
                                "slaves": ["slave", "enslaved", "acquired"],
                                "livestock": ["livestock", "cattle", "horse", "herds"],
                                "garrison": ["soldier", "recruit", "garrison", "military"],
                                "crimes": ["crime", "accused", "authorities"],
                                "tribute": ["tribute", "payment", "owes"]
                            }
                            
                            keywords = registry_keywords.get(registry_type, [])
                            keyword_match = any(keyword in description for keyword in keywords)
                            
                            if city_match and keyword_match:
                                return True
                    
                    return False
                else:
                    return False
        except:
            return False

    async def test_simulation_engine(self):
        """Test if simulation engine is generating events"""
        print("\n⚙️ Testing Real-time Simulation Engine...")
        try:
            # Get initial event count
            async with self.session.get(f"{API_BASE}/events") as response:
                if response.status != 200:
                    self.errors.append("Cannot test simulation engine - Events API failed")
                    return False
                
                initial_events = await response.json()
                initial_count = len(initial_events)
                
                print(f"   Initial event count: {initial_count}")
                print("   Waiting 35 seconds for new events to be generated...")
                
                # Wait for simulation to generate new events (simulation runs every 10-30 seconds)
                await asyncio.sleep(35)
                
                # Check for new events
                async with self.session.get(f"{API_BASE}/events") as response2:
                    if response2.status != 200:
                        self.errors.append("Events API failed during simulation test")
                        return False
                    
                    new_events = await response2.json()
                    new_count = len(new_events)
                    
                    if new_count > initial_count:
                        print(f"✅ Simulation engine working - Generated {new_count - initial_count} new events")
                        
                        # Check if events have fantasy content
                        latest_event = new_events[0] if new_events else None
                        if latest_event:
                            description = latest_event['description']
                            print(f"   Latest event: {description}")
                            
                            # Check for fantasy names and content
                            fantasy_indicators = ['Thorin', 'Elena', 'Gareth', 'Emberfalls', 'Stormhaven', 'citizen', 'kingdom']
                            has_fantasy_content = any(indicator in description for indicator in fantasy_indicators)
                            
                            if has_fantasy_content:
                                print("   ✅ Events contain fantasy content as expected")
                            else:
                                print("   ⚠️ Events may not contain expected fantasy content")
                        
                        self.test_results['simulation_engine'] = True
                        return True
                    else:
                        self.errors.append(f"Simulation engine not generating events - count remained {initial_count}")
                        return False
                        
        except Exception as e:
            self.errors.append(f"Simulation engine test error: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Fantasy Kingdom Backend Tests")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Test in order of dependency
            await self.test_kingdom_api()
            await self.test_city_api()
            await self.test_events_api()
            await self.test_websocket_connection()
            await self.test_database_initialization()
            await self.test_auto_generate_functionality()  # Test auto-generate functionality
            await self.test_simulation_engine()
            
        finally:
            await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(self.test_results.values())
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if self.errors:
            print("\n🚨 ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")
        
        return passed == total

async def main():
    """Main test runner"""
    tester = BackendTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All backend tests passed!")
        return 0
    else:
        print("\n💥 Some backend tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)