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
            'auto_generate_tribute': False,
            # Enhanced Boundary System Tests
            'multi_kingdoms_api': False,
            'kingdom_boundaries_create': False,
            'kingdom_boundaries_get': False,
            'kingdom_boundaries_update': False,
            'kingdom_boundaries_delete': False,
            'kingdom_boundaries_clear_all': False,
            'multi_kingdom_boundary_isolation': False,
            'database_consistency_check': False,
            # City Management with Multi-Kingdom Support Tests
            'city_creation_multi_kingdom': False,
            'city_update_multi_kingdom': False,
            'city_deletion_multi_kingdom': False,
            'city_retrieval_cross_kingdom': False,
            'city_multi_kingdom_isolation': False
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

    async def test_enhanced_boundary_management(self):
        """Test the enhanced boundary management system with new features"""
        print("\n🗺️ Testing Enhanced Boundary Management System...")
        
        # Test multi-kingdoms API first
        multi_kingdoms_success = await self.test_multi_kingdoms_api()
        self.test_results['multi_kingdoms_api'] = multi_kingdoms_success
        
        if not multi_kingdoms_success:
            print("   ❌ Multi-kingdoms API failed, skipping boundary tests")
            return False
        
        # Get kingdom IDs for testing
        kingdom_ids = await self.get_test_kingdom_ids()
        if len(kingdom_ids) < 2:
            print("   ⚠️ Creating additional test kingdom for isolation testing...")
            kingdom_ids = await self.ensure_multiple_kingdoms()
        
        # Test boundary creation
        boundary_create_success = await self.test_kingdom_boundaries_create(kingdom_ids[0])
        self.test_results['kingdom_boundaries_create'] = boundary_create_success
        
        # Test boundary retrieval
        boundary_get_success = await self.test_kingdom_boundaries_get(kingdom_ids[0])
        self.test_results['kingdom_boundaries_get'] = boundary_get_success
        
        # Test boundary update
        boundary_update_success = await self.test_kingdom_boundaries_update(kingdom_ids[0])
        self.test_results['kingdom_boundaries_update'] = boundary_update_success
        
        # Test boundary deletion
        boundary_delete_success = await self.test_kingdom_boundaries_delete(kingdom_ids[0])
        self.test_results['kingdom_boundaries_delete'] = boundary_delete_success
        
        # Test clear all boundaries (NEW FEATURE)
        boundary_clear_success = await self.test_kingdom_boundaries_clear_all(kingdom_ids[0])
        self.test_results['kingdom_boundaries_clear_all'] = boundary_clear_success
        
        # Test multi-kingdom boundary isolation
        isolation_success = await self.test_multi_kingdom_boundary_isolation(kingdom_ids)
        self.test_results['multi_kingdom_boundary_isolation'] = isolation_success
        
        # Test database consistency
        consistency_success = await self.test_database_consistency(kingdom_ids[0])
        self.test_results['database_consistency_check'] = consistency_success
        
        # Summary
        boundary_tests = [
            boundary_create_success, boundary_get_success, boundary_update_success,
            boundary_delete_success, boundary_clear_success, isolation_success, consistency_success
        ]
        
        passed_boundary_tests = sum(boundary_tests)
        total_boundary_tests = len(boundary_tests)
        
        print(f"\n   📊 Boundary Management Summary: {passed_boundary_tests}/{total_boundary_tests} tests passed")
        
        return passed_boundary_tests == total_boundary_tests

    async def test_multi_kingdoms_api(self):
        """Test multi-kingdoms API endpoints"""
        print("\n   🏰 Testing Multi-Kingdoms API...")
        try:
            # Test GET /api/multi-kingdoms
            async with self.session.get(f"{API_BASE}/multi-kingdoms") as response:
                if response.status == 200:
                    kingdoms = await response.json()
                    
                    if not isinstance(kingdoms, list):
                        self.errors.append("Multi-kingdoms API should return a list")
                        return False
                    
                    if len(kingdoms) == 0:
                        self.errors.append("No kingdoms found in multi-kingdoms API")
                        return False
                    
                    # Check kingdom structure
                    kingdom = kingdoms[0]
                    required_fields = ['id', 'name', 'ruler', 'color', 'cities', 'boundaries']
                    missing_fields = [field for field in required_fields if field not in kingdom]
                    
                    if missing_fields:
                        self.errors.append(f"Multi-kingdom missing fields: {missing_fields}")
                        return False
                    
                    print(f"      ✅ Found {len(kingdoms)} kingdoms")
                    print(f"      Sample kingdom: {kingdom['name']} (Ruler: {kingdom['ruler']})")
                    
                    return True
                else:
                    self.errors.append(f"Multi-kingdoms API returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Multi-kingdoms API error: {str(e)}")
            return False

    async def get_test_kingdom_ids(self):
        """Get kingdom IDs for testing"""
        try:
            async with self.session.get(f"{API_BASE}/multi-kingdoms") as response:
                if response.status == 200:
                    kingdoms = await response.json()
                    return [kingdom['id'] for kingdom in kingdoms]
                return []
        except:
            return []

    async def ensure_multiple_kingdoms(self):
        """Ensure we have multiple kingdoms for isolation testing"""
        try:
            # Create a test kingdom
            test_kingdom_data = {
                "name": "Test Kingdom for Boundaries",
                "ruler": "Test Ruler",
                "government_type": "Test Monarchy",
                "color": "#ff0000"
            }
            
            async with self.session.post(f"{API_BASE}/multi-kingdoms", json=test_kingdom_data) as response:
                if response.status == 200:
                    new_kingdom = await response.json()
                    print(f"      ✅ Created test kingdom: {new_kingdom['name']}")
                    
                    # Return updated kingdom list
                    return await self.get_test_kingdom_ids()
                else:
                    print(f"      ❌ Failed to create test kingdom: {response.status}")
                    return await self.get_test_kingdom_ids()
                    
        except Exception as e:
            print(f"      ❌ Error creating test kingdom: {e}")
            return await self.get_test_kingdom_ids()

    async def test_kingdom_boundaries_create(self, kingdom_id):
        """Test creating kingdom boundaries"""
        print("\n   📍 Testing Boundary Creation...")
        try:
            # Create test boundary data
            boundary_data = {
                "kingdom_id": kingdom_id,
                "boundary_points": [
                    {"x": 100, "y": 100},
                    {"x": 200, "y": 100},
                    {"x": 200, "y": 200},
                    {"x": 100, "y": 200}
                ],
                "color": "#1e3a8a"
            }
            
            async with self.session.post(f"{API_BASE}/kingdom-boundaries", json=boundary_data) as response:
                if response.status == 200:
                    boundary = await response.json()
                    
                    # Verify boundary structure
                    required_fields = ['id', 'kingdom_id', 'boundary_points', 'color']
                    missing_fields = [field for field in required_fields if field not in boundary]
                    
                    if missing_fields:
                        self.errors.append(f"Created boundary missing fields: {missing_fields}")
                        return False
                    
                    if boundary['kingdom_id'] != kingdom_id:
                        self.errors.append(f"Boundary kingdom_id mismatch: expected {kingdom_id}, got {boundary['kingdom_id']}")
                        return False
                    
                    if len(boundary['boundary_points']) != 4:
                        self.errors.append(f"Boundary points count mismatch: expected 4, got {len(boundary['boundary_points'])}")
                        return False
                    
                    print(f"      ✅ Created boundary with {len(boundary['boundary_points'])} points")
                    print(f"      Boundary ID: {boundary['id']}")
                    
                    # Store boundary ID for later tests
                    self.test_boundary_id = boundary['id']
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Boundary creation failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Boundary creation error: {str(e)}")
            return False

    async def test_kingdom_boundaries_get(self, kingdom_id):
        """Test retrieving kingdom boundaries"""
        print("\n   📋 Testing Boundary Retrieval...")
        try:
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as response:
                if response.status == 200:
                    boundaries = await response.json()
                    
                    if not isinstance(boundaries, list):
                        self.errors.append("Kingdom boundaries should return a list")
                        return False
                    
                    if len(boundaries) == 0:
                        self.errors.append("No boundaries found for kingdom")
                        return False
                    
                    # Check boundary structure
                    boundary = boundaries[0]
                    required_fields = ['id', 'kingdom_id', 'boundary_points', 'color']
                    missing_fields = [field for field in required_fields if field not in boundary]
                    
                    if missing_fields:
                        self.errors.append(f"Retrieved boundary missing fields: {missing_fields}")
                        return False
                    
                    print(f"      ✅ Retrieved {len(boundaries)} boundaries for kingdom")
                    print(f"      First boundary has {len(boundary['boundary_points'])} points")
                    
                    return True
                    
                else:
                    self.errors.append(f"Boundary retrieval failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Boundary retrieval error: {str(e)}")
            return False

    async def test_kingdom_boundaries_update(self, kingdom_id):
        """Test updating kingdom boundaries"""
        print("\n   ✏️ Testing Boundary Update...")
        try:
            if not hasattr(self, 'test_boundary_id'):
                self.errors.append("No boundary ID available for update test")
                return False
            
            # Update boundary with new points
            update_data = {
                "boundary_points": [
                    {"x": 150, "y": 150},
                    {"x": 250, "y": 150},
                    {"x": 250, "y": 250},
                    {"x": 150, "y": 250},
                    {"x": 150, "y": 200}  # Additional point
                ]
            }
            
            async with self.session.put(f"{API_BASE}/kingdom-boundaries/{self.test_boundary_id}", json=update_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "message" not in result:
                        self.errors.append("Boundary update response missing message")
                        return False
                    
                    # Verify the update was applied
                    async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as get_response:
                        if get_response.status == 200:
                            boundaries = await get_response.json()
                            updated_boundary = next((b for b in boundaries if b['id'] == self.test_boundary_id), None)
                            
                            if not updated_boundary:
                                self.errors.append("Updated boundary not found in kingdom boundaries")
                                return False
                            
                            if len(updated_boundary['boundary_points']) != 5:
                                self.errors.append(f"Boundary update failed: expected 5 points, got {len(updated_boundary['boundary_points'])}")
                                return False
                            
                            print(f"      ✅ Updated boundary to {len(updated_boundary['boundary_points'])} points")
                            return True
                        else:
                            self.errors.append("Failed to verify boundary update")
                            return False
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Boundary update failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Boundary update error: {str(e)}")
            return False

    async def test_kingdom_boundaries_delete(self, kingdom_id):
        """Test deleting individual kingdom boundaries"""
        print("\n   🗑️ Testing Individual Boundary Deletion...")
        try:
            if not hasattr(self, 'test_boundary_id'):
                self.errors.append("No boundary ID available for delete test")
                return False
            
            # Get initial boundary count
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as response:
                if response.status == 200:
                    initial_boundaries = await response.json()
                    initial_count = len(initial_boundaries)
                else:
                    self.errors.append("Failed to get initial boundary count")
                    return False
            
            # Delete the boundary
            async with self.session.delete(f"{API_BASE}/kingdom-boundaries/{self.test_boundary_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "message" not in result:
                        self.errors.append("Boundary deletion response missing message")
                        return False
                    
                    # Verify the boundary was deleted
                    async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as get_response:
                        if get_response.status == 200:
                            remaining_boundaries = await get_response.json()
                            remaining_count = len(remaining_boundaries)
                            
                            if remaining_count != initial_count - 1:
                                self.errors.append(f"Boundary deletion failed: expected {initial_count - 1} boundaries, got {remaining_count}")
                                return False
                            
                            # Verify specific boundary is gone
                            deleted_boundary = next((b for b in remaining_boundaries if b['id'] == self.test_boundary_id), None)
                            if deleted_boundary:
                                self.errors.append("Deleted boundary still exists in kingdom boundaries")
                                return False
                            
                            print(f"      ✅ Deleted boundary successfully: {initial_count} → {remaining_count} boundaries")
                            return True
                        else:
                            self.errors.append("Failed to verify boundary deletion")
                            return False
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Boundary deletion failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Boundary deletion error: {str(e)}")
            return False

    async def test_kingdom_boundaries_clear_all(self, kingdom_id):
        """Test the new Clear All Boundaries endpoint"""
        print("\n   🧹 Testing Clear All Boundaries (NEW FEATURE)...")
        try:
            # First create some boundaries to clear
            boundaries_to_create = [
                {
                    "kingdom_id": kingdom_id,
                    "boundary_points": [{"x": 50, "y": 50}, {"x": 100, "y": 50}, {"x": 100, "y": 100}, {"x": 50, "y": 100}],
                    "color": "#ff0000"
                },
                {
                    "kingdom_id": kingdom_id,
                    "boundary_points": [{"x": 200, "y": 200}, {"x": 300, "y": 200}, {"x": 300, "y": 300}, {"x": 200, "y": 300}],
                    "color": "#00ff00"
                }
            ]
            
            created_boundary_ids = []
            for boundary_data in boundaries_to_create:
                async with self.session.post(f"{API_BASE}/kingdom-boundaries", json=boundary_data) as response:
                    if response.status == 200:
                        boundary = await response.json()
                        created_boundary_ids.append(boundary['id'])
                    else:
                        print(f"      ⚠️ Failed to create test boundary for clear all test")
            
            if len(created_boundary_ids) == 0:
                print("      ⚠️ No boundaries created for clear all test, but continuing...")
            
            # Get initial boundary count
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as response:
                if response.status == 200:
                    initial_boundaries = await response.json()
                    initial_count = len(initial_boundaries)
                    print(f"      Initial boundary count: {initial_count}")
                else:
                    self.errors.append("Failed to get initial boundary count for clear all test")
                    return False
            
            # Test the Clear All Boundaries endpoint
            async with self.session.delete(f"{API_BASE}/kingdom-boundaries/clear/{kingdom_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "message" not in result:
                        self.errors.append("Clear all boundaries response missing message")
                        return False
                    
                    # Verify all boundaries were cleared
                    async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as get_response:
                        if get_response.status == 200:
                            remaining_boundaries = await get_response.json()
                            remaining_count = len(remaining_boundaries)
                            
                            if remaining_count != 0:
                                self.errors.append(f"Clear all boundaries failed: expected 0 boundaries, got {remaining_count}")
                                return False
                            
                            print(f"      ✅ Cleared all boundaries successfully: {initial_count} → {remaining_count} boundaries")
                            
                            # Also verify in multi-kingdoms document
                            async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom_id}") as kingdom_response:
                                if kingdom_response.status == 200:
                                    kingdom_data = await kingdom_response.json()
                                    kingdom_boundaries = kingdom_data.get('boundaries', [])
                                    
                                    if len(kingdom_boundaries) != 0:
                                        self.errors.append(f"Clear all boundaries failed in multi-kingdoms document: expected 0, got {len(kingdom_boundaries)}")
                                        return False
                                    
                                    print(f"      ✅ Multi-kingdoms document also cleared: {len(kingdom_boundaries)} boundaries")
                                    return True
                                else:
                                    self.errors.append("Failed to verify clear all in multi-kingdoms document")
                                    return False
                        else:
                            self.errors.append("Failed to verify clear all boundaries")
                            return False
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Clear all boundaries failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Clear all boundaries error: {str(e)}")
            return False

    async def test_multi_kingdom_boundary_isolation(self, kingdom_ids):
        """Test that each kingdom's boundaries are independent"""
        print("\n   🏛️ Testing Multi-Kingdom Boundary Isolation...")
        try:
            if len(kingdom_ids) < 2:
                self.errors.append("Need at least 2 kingdoms for isolation testing")
                return False
            
            kingdom1_id = kingdom_ids[0]
            kingdom2_id = kingdom_ids[1]
            
            # Create boundaries for kingdom 1
            kingdom1_boundary = {
                "kingdom_id": kingdom1_id,
                "boundary_points": [{"x": 10, "y": 10}, {"x": 50, "y": 10}, {"x": 50, "y": 50}, {"x": 10, "y": 50}],
                "color": "#ff0000"
            }
            
            # Create boundaries for kingdom 2
            kingdom2_boundary = {
                "kingdom_id": kingdom2_id,
                "boundary_points": [{"x": 100, "y": 100}, {"x": 150, "y": 100}, {"x": 150, "y": 150}, {"x": 100, "y": 150}],
                "color": "#00ff00"
            }
            
            # Create boundaries for both kingdoms
            async with self.session.post(f"{API_BASE}/kingdom-boundaries", json=kingdom1_boundary) as response:
                if response.status != 200:
                    self.errors.append("Failed to create boundary for kingdom 1 in isolation test")
                    return False
                kingdom1_boundary_data = await response.json()
            
            async with self.session.post(f"{API_BASE}/kingdom-boundaries", json=kingdom2_boundary) as response:
                if response.status != 200:
                    self.errors.append("Failed to create boundary for kingdom 2 in isolation test")
                    return False
                kingdom2_boundary_data = await response.json()
            
            # Verify each kingdom only sees its own boundaries
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom1_id}") as response:
                if response.status == 200:
                    kingdom1_boundaries = await response.json()
                    kingdom1_count = len(kingdom1_boundaries)
                    
                    # Check that kingdom1 boundaries don't contain kingdom2's boundary
                    kingdom2_boundary_in_kingdom1 = any(b['id'] == kingdom2_boundary_data['id'] for b in kingdom1_boundaries)
                    if kingdom2_boundary_in_kingdom1:
                        self.errors.append("Kingdom 1 boundaries contain Kingdom 2's boundary - isolation failed")
                        return False
                else:
                    self.errors.append("Failed to get Kingdom 1 boundaries for isolation test")
                    return False
            
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom2_id}") as response:
                if response.status == 200:
                    kingdom2_boundaries = await response.json()
                    kingdom2_count = len(kingdom2_boundaries)
                    
                    # Check that kingdom2 boundaries don't contain kingdom1's boundary
                    kingdom1_boundary_in_kingdom2 = any(b['id'] == kingdom1_boundary_data['id'] for b in kingdom2_boundaries)
                    if kingdom1_boundary_in_kingdom2:
                        self.errors.append("Kingdom 2 boundaries contain Kingdom 1's boundary - isolation failed")
                        return False
                else:
                    self.errors.append("Failed to get Kingdom 2 boundaries for isolation test")
                    return False
            
            print(f"      ✅ Kingdom isolation verified: Kingdom 1 has {kingdom1_count} boundaries, Kingdom 2 has {kingdom2_count} boundaries")
            
            # Test that clearing one kingdom's boundaries doesn't affect the other
            async with self.session.delete(f"{API_BASE}/kingdom-boundaries/clear/{kingdom1_id}") as response:
                if response.status != 200:
                    self.errors.append("Failed to clear Kingdom 1 boundaries in isolation test")
                    return False
            
            # Verify Kingdom 1 boundaries are cleared but Kingdom 2 boundaries remain
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom1_id}") as response:
                if response.status == 200:
                    kingdom1_boundaries_after = await response.json()
                    if len(kingdom1_boundaries_after) != 0:
                        self.errors.append("Kingdom 1 boundaries not cleared in isolation test")
                        return False
                else:
                    self.errors.append("Failed to verify Kingdom 1 boundaries cleared")
                    return False
            
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom2_id}") as response:
                if response.status == 200:
                    kingdom2_boundaries_after = await response.json()
                    if len(kingdom2_boundaries_after) != kingdom2_count:
                        self.errors.append("Kingdom 2 boundaries affected by Kingdom 1 clear operation - isolation failed")
                        return False
                else:
                    self.errors.append("Failed to verify Kingdom 2 boundaries unaffected")
                    return False
            
            print(f"      ✅ Clear isolation verified: Kingdom 1 cleared, Kingdom 2 unaffected")
            return True
            
        except Exception as e:
            self.errors.append(f"Multi-kingdom boundary isolation error: {str(e)}")
            return False

    async def test_database_consistency(self, kingdom_id):
        """Test that boundaries exist in both kingdom_boundaries collection and multi_kingdoms documents"""
        print("\n   🔍 Testing Database Consistency...")
        try:
            # Create a test boundary
            test_boundary = {
                "kingdom_id": kingdom_id,
                "boundary_points": [{"x": 300, "y": 300}, {"x": 400, "y": 300}, {"x": 400, "y": 400}, {"x": 300, "y": 400}],
                "color": "#0000ff"
            }
            
            async with self.session.post(f"{API_BASE}/kingdom-boundaries", json=test_boundary) as response:
                if response.status != 200:
                    self.errors.append("Failed to create boundary for consistency test")
                    return False
                created_boundary = await response.json()
                boundary_id = created_boundary['id']
            
            # Check boundary exists in kingdom_boundaries collection
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as response:
                if response.status == 200:
                    boundaries_collection = await response.json()
                    boundary_in_collection = any(b['id'] == boundary_id for b in boundaries_collection)
                    
                    if not boundary_in_collection:
                        self.errors.append("Boundary not found in kingdom_boundaries collection")
                        return False
                else:
                    self.errors.append("Failed to get boundaries from collection")
                    return False
            
            # Check boundary exists in multi_kingdoms document
            async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom_id}") as response:
                if response.status == 200:
                    kingdom_document = await response.json()
                    embedded_boundaries = kingdom_document.get('boundaries', [])
                    boundary_in_document = any(b['id'] == boundary_id for b in embedded_boundaries)
                    
                    if not boundary_in_document:
                        self.errors.append("Boundary not found in multi_kingdoms document")
                        return False
                else:
                    self.errors.append("Failed to get kingdom document")
                    return False
            
            print(f"      ✅ Database consistency verified: boundary exists in both locations")
            
            # Test consistency after update
            update_data = {
                "boundary_points": [{"x": 350, "y": 350}, {"x": 450, "y": 350}, {"x": 450, "y": 450}, {"x": 350, "y": 450}]
            }
            
            async with self.session.put(f"{API_BASE}/kingdom-boundaries/{boundary_id}", json=update_data) as response:
                if response.status != 200:
                    self.errors.append("Failed to update boundary for consistency test")
                    return False
            
            # Verify update consistency in both locations
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as response:
                if response.status == 200:
                    boundaries_collection = await response.json()
                    updated_boundary_collection = next((b for b in boundaries_collection if b['id'] == boundary_id), None)
                    
                    if not updated_boundary_collection or len(updated_boundary_collection['boundary_points']) != 4:
                        self.errors.append("Boundary update not reflected in collection")
                        return False
                else:
                    self.errors.append("Failed to verify update in collection")
                    return False
            
            async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom_id}") as response:
                if response.status == 200:
                    kingdom_document = await response.json()
                    embedded_boundaries = kingdom_document.get('boundaries', [])
                    updated_boundary_document = next((b for b in embedded_boundaries if b['id'] == boundary_id), None)
                    
                    if not updated_boundary_document or len(updated_boundary_document['boundary_points']) != 4:
                        self.errors.append("Boundary update not reflected in document")
                        return False
                else:
                    self.errors.append("Failed to verify update in document")
                    return False
            
            print(f"      ✅ Update consistency verified: both locations updated")
            
            # Test consistency after deletion
            async with self.session.delete(f"{API_BASE}/kingdom-boundaries/{boundary_id}") as response:
                if response.status != 200:
                    self.errors.append("Failed to delete boundary for consistency test")
                    return False
            
            # Verify deletion consistency in both locations
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{kingdom_id}") as response:
                if response.status == 200:
                    boundaries_collection = await response.json()
                    deleted_boundary_collection = any(b['id'] == boundary_id for b in boundaries_collection)
                    
                    if deleted_boundary_collection:
                        self.errors.append("Deleted boundary still exists in collection")
                        return False
                else:
                    self.errors.append("Failed to verify deletion in collection")
                    return False
            
            async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom_id}") as response:
                if response.status == 200:
                    kingdom_document = await response.json()
                    embedded_boundaries = kingdom_document.get('boundaries', [])
                    deleted_boundary_document = any(b['id'] == boundary_id for b in embedded_boundaries)
                    
                    if deleted_boundary_document:
                        self.errors.append("Deleted boundary still exists in document")
                        return False
                else:
                    self.errors.append("Failed to verify deletion in document")
                    return False
            
            print(f"      ✅ Deletion consistency verified: boundary removed from both locations")
            return True
            
        except Exception as e:
            self.errors.append(f"Database consistency test error: {str(e)}")
            return False

    async def test_city_management_multi_kingdom(self):
        """Test city management functionality with multi-kingdom support"""
        print("\n🏘️ Testing City Management with Multi-Kingdom Support...")
        
        # Test city creation in active kingdom
        city_creation_success = await self.test_city_creation_multi_kingdom()
        self.test_results['city_creation_multi_kingdom'] = city_creation_success
        
        # Test city updates across kingdoms
        city_update_success = await self.test_city_update_multi_kingdom()
        self.test_results['city_update_multi_kingdom'] = city_update_success
        
        # Test city deletion from correct kingdom
        city_deletion_success = await self.test_city_deletion_multi_kingdom()
        self.test_results['city_deletion_multi_kingdom'] = city_deletion_success
        
        # Test city retrieval across all kingdoms
        city_retrieval_success = await self.test_city_retrieval_cross_kingdom()
        self.test_results['city_retrieval_cross_kingdom'] = city_retrieval_success
        
        # Test multi-kingdom city isolation
        city_isolation_success = await self.test_city_multi_kingdom_isolation()
        self.test_results['city_multi_kingdom_isolation'] = city_isolation_success
        
        # Summary
        city_tests = [
            city_creation_success, city_update_success, city_deletion_success,
            city_retrieval_success, city_isolation_success
        ]
        
        passed_city_tests = sum(city_tests)
        total_city_tests = len(city_tests)
        
        print(f"\n   📊 City Management Summary: {passed_city_tests}/{total_city_tests} tests passed")
        
        return passed_city_tests == total_city_tests

    async def test_city_creation_multi_kingdom(self):
        """Test city creation in active kingdom"""
        print("\n   🏗️ Testing City Creation in Active Kingdom...")
        try:
            # Get active kingdom
            async with self.session.get(f"{API_BASE}/active-kingdom") as response:
                if response.status != 200:
                    self.errors.append("Failed to get active kingdom for city creation test")
                    return False
                
                active_kingdom = await response.json()
                active_kingdom_id = active_kingdom['id']
                initial_city_count = len(active_kingdom.get('cities', []))
            
            # Create test city data
            test_city_data = {
                "name": "Test City for Multi-Kingdom",
                "governor": "Test Governor",
                "x_coordinate": 123.45,
                "y_coordinate": 67.89
            }
            
            # Create city
            async with self.session.post(f"{API_BASE}/cities", json=test_city_data) as response:
                if response.status == 200:
                    created_city = await response.json()
                    
                    # Verify city structure
                    required_fields = ['id', 'name', 'governor', 'x_coordinate', 'y_coordinate']
                    missing_fields = [field for field in required_fields if field not in created_city]
                    
                    if missing_fields:
                        self.errors.append(f"Created city missing fields: {missing_fields}")
                        return False
                    
                    # Verify city was added to active kingdom
                    async with self.session.get(f"{API_BASE}/active-kingdom") as verify_response:
                        if verify_response.status == 200:
                            updated_kingdom = await verify_response.json()
                            new_city_count = len(updated_kingdom.get('cities', []))
                            
                            if new_city_count != initial_city_count + 1:
                                self.errors.append(f"City not added to active kingdom: expected {initial_city_count + 1} cities, got {new_city_count}")
                                return False
                            
                            # Find the created city in the kingdom
                            created_city_in_kingdom = None
                            for city in updated_kingdom['cities']:
                                if city['id'] == created_city['id']:
                                    created_city_in_kingdom = city
                                    break
                            
                            if not created_city_in_kingdom:
                                self.errors.append("Created city not found in active kingdom")
                                return False
                            
                            print(f"      ✅ City '{created_city['name']}' created successfully in active kingdom")
                            print(f"      City ID: {created_city['id']}")
                            print(f"      Coordinates: ({created_city['x_coordinate']}, {created_city['y_coordinate']})")
                            
                            # Store city ID for later tests
                            self.test_city_id = created_city['id']
                            return True
                        else:
                            self.errors.append("Failed to verify city creation in active kingdom")
                            return False
                else:
                    error_text = await response.text()
                    self.errors.append(f"City creation failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"City creation test error: {str(e)}")
            return False

    async def test_city_update_multi_kingdom(self):
        """Test city updates across kingdoms"""
        print("\n   ✏️ Testing City Updates Across Kingdoms...")
        try:
            if not hasattr(self, 'test_city_id'):
                self.errors.append("No test city ID available for update test")
                return False
            
            # Update city coordinates and name
            update_data = {
                "name": "Updated Test City",
                "x_coordinate": 200.50,
                "y_coordinate": 150.75,
                "treasury": 2500
            }
            
            async with self.session.put(f"{API_BASE}/city/{self.test_city_id}", json=update_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "message" not in result:
                        self.errors.append("City update response missing message")
                        return False
                    
                    # Verify the update was applied by retrieving the city
                    async with self.session.get(f"{API_BASE}/city/{self.test_city_id}") as get_response:
                        if get_response.status == 200:
                            updated_city = await get_response.json()
                            
                            # Check if updates were applied
                            if updated_city['name'] != update_data['name']:
                                self.errors.append(f"City name not updated: expected '{update_data['name']}', got '{updated_city['name']}'")
                                return False
                            
                            if updated_city['x_coordinate'] != update_data['x_coordinate']:
                                self.errors.append(f"City x_coordinate not updated: expected {update_data['x_coordinate']}, got {updated_city['x_coordinate']}")
                                return False
                            
                            if updated_city['y_coordinate'] != update_data['y_coordinate']:
                                self.errors.append(f"City y_coordinate not updated: expected {update_data['y_coordinate']}, got {updated_city['y_coordinate']}")
                                return False
                            
                            if updated_city['treasury'] != update_data['treasury']:
                                self.errors.append(f"City treasury not updated: expected {update_data['treasury']}, got {updated_city['treasury']}")
                                return False
                            
                            print(f"      ✅ City updated successfully")
                            print(f"      New name: {updated_city['name']}")
                            print(f"      New coordinates: ({updated_city['x_coordinate']}, {updated_city['y_coordinate']})")
                            print(f"      New treasury: {updated_city['treasury']}")
                            
                            return True
                        else:
                            self.errors.append("Failed to retrieve updated city")
                            return False
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"City update failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"City update test error: {str(e)}")
            return False

    async def test_city_deletion_multi_kingdom(self):
        """Test city deletion from correct kingdom"""
        print("\n   🗑️ Testing City Deletion from Correct Kingdom...")
        try:
            if not hasattr(self, 'test_city_id'):
                self.errors.append("No test city ID available for deletion test")
                return False
            
            # Get initial city count in active kingdom
            async with self.session.get(f"{API_BASE}/active-kingdom") as response:
                if response.status == 200:
                    initial_kingdom = await response.json()
                    initial_city_count = len(initial_kingdom.get('cities', []))
                else:
                    self.errors.append("Failed to get initial city count for deletion test")
                    return False
            
            # Delete the city
            async with self.session.delete(f"{API_BASE}/city/{self.test_city_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if "message" not in result:
                        self.errors.append("City deletion response missing message")
                        return False
                    
                    # Verify the city was deleted from the kingdom
                    async with self.session.get(f"{API_BASE}/active-kingdom") as verify_response:
                        if verify_response.status == 200:
                            updated_kingdom = await verify_response.json()
                            new_city_count = len(updated_kingdom.get('cities', []))
                            
                            if new_city_count != initial_city_count - 1:
                                self.errors.append(f"City not deleted from kingdom: expected {initial_city_count - 1} cities, got {new_city_count}")
                                return False
                            
                            # Verify specific city is gone
                            deleted_city = None
                            for city in updated_kingdom['cities']:
                                if city['id'] == self.test_city_id:
                                    deleted_city = city
                                    break
                            
                            if deleted_city:
                                self.errors.append("Deleted city still exists in kingdom")
                                return False
                            
                            print(f"      ✅ City deleted successfully from kingdom: {initial_city_count} → {new_city_count} cities")
                            
                            # Verify city is no longer retrievable
                            async with self.session.get(f"{API_BASE}/city/{self.test_city_id}") as get_response:
                                if get_response.status == 404:
                                    print(f"      ✅ City no longer retrievable (404 as expected)")
                                    return True
                                else:
                                    self.errors.append("Deleted city still retrievable")
                                    return False
                        else:
                            self.errors.append("Failed to verify city deletion from kingdom")
                            return False
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"City deletion failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"City deletion test error: {str(e)}")
            return False

    async def test_city_retrieval_cross_kingdom(self):
        """Test city retrieval across all kingdoms"""
        print("\n   🔍 Testing City Retrieval Across All Kingdoms...")
        try:
            # Get all kingdoms
            async with self.session.get(f"{API_BASE}/multi-kingdoms") as response:
                if response.status != 200:
                    self.errors.append("Failed to get kingdoms for cross-kingdom retrieval test")
                    return False
                
                kingdoms = await response.json()
                if len(kingdoms) == 0:
                    self.errors.append("No kingdoms found for cross-kingdom retrieval test")
                    return False
            
            # Collect all city IDs from all kingdoms
            all_city_ids = []
            for kingdom in kingdoms:
                for city in kingdom.get('cities', []):
                    all_city_ids.append((city['id'], city['name'], kingdom['name']))
            
            if len(all_city_ids) == 0:
                self.errors.append("No cities found across all kingdoms")
                return False
            
            print(f"      Found {len(all_city_ids)} cities across {len(kingdoms)} kingdoms")
            
            # Test retrieving each city
            successful_retrievals = 0
            for city_id, city_name, kingdom_name in all_city_ids:
                async with self.session.get(f"{API_BASE}/city/{city_id}") as city_response:
                    if city_response.status == 200:
                        city_data = await city_response.json()
                        
                        # Verify city structure
                        required_fields = ['id', 'name', 'governor', 'population', 'treasury']
                        missing_fields = [field for field in required_fields if field not in city_data]
                        
                        if missing_fields:
                            self.errors.append(f"City {city_name} missing fields: {missing_fields}")
                            continue
                        
                        if city_data['id'] != city_id:
                            self.errors.append(f"City ID mismatch for {city_name}: expected {city_id}, got {city_data['id']}")
                            continue
                        
                        successful_retrievals += 1
                    else:
                        self.errors.append(f"Failed to retrieve city {city_name} (ID: {city_id}) from kingdom {kingdom_name}")
            
            if successful_retrievals == len(all_city_ids):
                print(f"      ✅ Successfully retrieved all {successful_retrievals} cities across kingdoms")
                return True
            else:
                self.errors.append(f"Only retrieved {successful_retrievals}/{len(all_city_ids)} cities")
                return False
                
        except Exception as e:
            self.errors.append(f"Cross-kingdom city retrieval test error: {str(e)}")
            return False

    async def test_city_multi_kingdom_isolation(self):
        """Test that cities are managed independently per kingdom"""
        print("\n   🏛️ Testing City Multi-Kingdom Isolation...")
        try:
            # Get all kingdoms
            async with self.session.get(f"{API_BASE}/multi-kingdoms") as response:
                if response.status != 200:
                    self.errors.append("Failed to get kingdoms for isolation test")
                    return False
                
                kingdoms = await response.json()
                if len(kingdoms) < 2:
                    # Create a second kingdom for testing
                    test_kingdom_data = {
                        "name": "Isolation Test Kingdom",
                        "ruler": "Isolation Test Ruler",
                        "government_type": "Test Monarchy",
                        "color": "#ff6600"
                    }
                    
                    async with self.session.post(f"{API_BASE}/multi-kingdoms", json=test_kingdom_data) as create_response:
                        if create_response.status == 200:
                            new_kingdom = await create_response.json()
                            kingdoms.append(new_kingdom)
                            print(f"      Created test kingdom: {new_kingdom['name']}")
                        else:
                            self.errors.append("Failed to create second kingdom for isolation test")
                            return False
            
            if len(kingdoms) < 2:
                self.errors.append("Need at least 2 kingdoms for isolation testing")
                return False
            
            kingdom1 = kingdoms[0]
            kingdom2 = kingdoms[1]
            
            # Set kingdom1 as active and create a city
            async with self.session.post(f"{API_BASE}/multi-kingdom/{kingdom1['id']}/set-active") as response:
                if response.status != 200:
                    self.errors.append("Failed to set kingdom1 as active")
                    return False
            
            kingdom1_city_data = {
                "name": "Kingdom1 Isolation City",
                "governor": "Kingdom1 Governor",
                "x_coordinate": 100.0,
                "y_coordinate": 100.0
            }
            
            async with self.session.post(f"{API_BASE}/cities", json=kingdom1_city_data) as response:
                if response.status != 200:
                    self.errors.append("Failed to create city in kingdom1")
                    return False
                kingdom1_city = await response.json()
            
            # Set kingdom2 as active and create a city
            async with self.session.post(f"{API_BASE}/multi-kingdom/{kingdom2['id']}/set-active") as response:
                if response.status != 200:
                    self.errors.append("Failed to set kingdom2 as active")
                    return False
            
            kingdom2_city_data = {
                "name": "Kingdom2 Isolation City",
                "governor": "Kingdom2 Governor",
                "x_coordinate": 200.0,
                "y_coordinate": 200.0
            }
            
            async with self.session.post(f"{API_BASE}/cities", json=kingdom2_city_data) as response:
                if response.status != 200:
                    self.errors.append("Failed to create city in kingdom2")
                    return False
                kingdom2_city = await response.json()
            
            # Verify each kingdom only contains its own city
            async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom1['id']}") as response:
                if response.status == 200:
                    updated_kingdom1 = await response.json()
                    kingdom1_cities = updated_kingdom1.get('cities', [])
                    
                    # Check that kingdom1 contains its city
                    kingdom1_has_own_city = any(city['id'] == kingdom1_city['id'] for city in kingdom1_cities)
                    if not kingdom1_has_own_city:
                        self.errors.append("Kingdom1 doesn't contain its own city")
                        return False
                    
                    # Check that kingdom1 doesn't contain kingdom2's city
                    kingdom1_has_kingdom2_city = any(city['id'] == kingdom2_city['id'] for city in kingdom1_cities)
                    if kingdom1_has_kingdom2_city:
                        self.errors.append("Kingdom1 contains Kingdom2's city - isolation failed")
                        return False
                else:
                    self.errors.append("Failed to get Kingdom1 data for isolation test")
                    return False
            
            async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom2['id']}") as response:
                if response.status == 200:
                    updated_kingdom2 = await response.json()
                    kingdom2_cities = updated_kingdom2.get('cities', [])
                    
                    # Check that kingdom2 contains its city
                    kingdom2_has_own_city = any(city['id'] == kingdom2_city['id'] for city in kingdom2_cities)
                    if not kingdom2_has_own_city:
                        self.errors.append("Kingdom2 doesn't contain its own city")
                        return False
                    
                    # Check that kingdom2 doesn't contain kingdom1's city
                    kingdom2_has_kingdom1_city = any(city['id'] == kingdom1_city['id'] for city in kingdom2_cities)
                    if kingdom2_has_kingdom1_city:
                        self.errors.append("Kingdom2 contains Kingdom1's city - isolation failed")
                        return False
                else:
                    self.errors.append("Failed to get Kingdom2 data for isolation test")
                    return False
            
            print(f"      ✅ City isolation verified: each kingdom contains only its own cities")
            
            # Test that deleting a city from one kingdom doesn't affect the other
            async with self.session.delete(f"{API_BASE}/city/{kingdom1_city['id']}") as response:
                if response.status != 200:
                    self.errors.append("Failed to delete Kingdom1 city in isolation test")
                    return False
            
            # Verify Kingdom1 city is deleted but Kingdom2 city remains
            async with self.session.get(f"{API_BASE}/city/{kingdom1_city['id']}") as response:
                if response.status != 404:
                    self.errors.append("Kingdom1 city not properly deleted")
                    return False
            
            async with self.session.get(f"{API_BASE}/city/{kingdom2_city['id']}") as response:
                if response.status != 200:
                    self.errors.append("Kingdom2 city affected by Kingdom1 city deletion - isolation failed")
                    return False
            
            print(f"      ✅ Deletion isolation verified: Kingdom1 city deleted, Kingdom2 city unaffected")
            return True
            
        except Exception as e:
            self.errors.append(f"City multi-kingdom isolation test error: {str(e)}")
            return False

    async def test_multi_kingdom_autogenerate_functionality(self):
        """Test multi-kingdom autogenerate functionality specifically"""
        print("\n🎲 Testing Multi-Kingdom Autogenerate Functionality...")
        
        try:
            # Get all kingdoms from multi_kingdoms collection
            async with self.session.get(f"{API_BASE}/multi-kingdoms") as response:
                if response.status != 200:
                    self.errors.append("Cannot test multi-kingdom autogenerate - Multi-kingdoms API failed")
                    return False
                
                kingdoms = await response.json()
                if not kingdoms:
                    self.errors.append("No kingdoms found in multi_kingdoms collection")
                    return False
                
                print(f"   Found {len(kingdoms)} kingdoms for testing")
                
                # Test autogenerate for each kingdom
                success_count = 0
                for kingdom in kingdoms:
                    kingdom_id = kingdom['id']
                    kingdom_name = kingdom['name']
                    cities = kingdom.get('cities', [])
                    
                    if not cities:
                        print(f"   ⚠️ Skipping {kingdom_name} - no cities")
                        continue
                    
                    print(f"\n   🏰 Testing autogenerate for kingdom: {kingdom_name}")
                    
                    # Test each registry type for this kingdom
                    registry_types = ["citizens", "slaves", "livestock", "garrison", "crimes", "tribute"]
                    kingdom_success = True
                    
                    for registry_type in registry_types:
                        city = cities[0]  # Use first city
                        city_id = city['id']
                        city_name = city['name']
                        
                        # Get initial count
                        initial_count = await self.get_multi_kingdom_registry_count(kingdom_id, city_id, registry_type)
                        
                        # Make autogenerate request
                        payload = {
                            "registry_type": registry_type,
                            "city_id": city_id,
                            "count": 1
                        }
                        
                        async with self.session.post(f"{API_BASE}/auto-generate", json=payload) as gen_response:
                            if gen_response.status == 200:
                                result = await gen_response.json()
                                
                                # Wait for database update
                                await asyncio.sleep(2)
                                
                                # Verify database was updated in multi_kingdoms collection
                                new_count = await self.get_multi_kingdom_registry_count(kingdom_id, city_id, registry_type)
                                
                                if new_count > initial_count:
                                    print(f"      ✅ {registry_type}: {initial_count} → {new_count}")
                                    
                                    # Check if event was created with kingdom_id
                                    event_found = await self.check_kingdom_specific_event(kingdom_id, registry_type, city_name)
                                    if event_found:
                                        print(f"         📜 Event created with kingdom_id")
                                    else:
                                        print(f"         ⚠️ Event may not have kingdom_id tag")
                                else:
                                    print(f"      ❌ {registry_type}: Database not updated ({initial_count} → {new_count})")
                                    kingdom_success = False
                                    self.errors.append(f"Multi-kingdom autogenerate failed for {registry_type} in {kingdom_name}")
                            else:
                                error_text = await gen_response.text()
                                print(f"      ❌ {registry_type}: HTTP {gen_response.status} - {error_text}")
                                kingdom_success = False
                                self.errors.append(f"Multi-kingdom autogenerate API error for {registry_type} in {kingdom_name}")
                    
                    if kingdom_success:
                        success_count += 1
                        print(f"   ✅ All registry types working for {kingdom_name}")
                    else:
                        print(f"   ❌ Some registry types failed for {kingdom_name}")
                
                # Overall success if all kingdoms worked
                overall_success = success_count == len([k for k in kingdoms if k.get('cities')])
                
                print(f"\n   📊 Multi-Kingdom Autogenerate Summary: {success_count}/{len([k for k in kingdoms if k.get('cities')])} kingdoms working")
                
                self.test_results['multi_kingdom_autogenerate'] = overall_success
                return overall_success
                
        except Exception as e:
            self.errors.append(f"Multi-kingdom autogenerate test error: {str(e)}")
            return False

    async def get_multi_kingdom_registry_count(self, kingdom_id, city_id, registry_type):
        """Get registry count from multi_kingdoms collection"""
        try:
            async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom_id}") as response:
                if response.status == 200:
                    kingdom_data = await response.json()
                    cities = kingdom_data.get('cities', [])
                    
                    # Find the specific city
                    city = next((c for c in cities if c['id'] == city_id), None)
                    if not city:
                        return 0
                    
                    registry_map = {
                        "citizens": "citizens",
                        "slaves": "slaves", 
                        "livestock": "livestock",
                        "garrison": "garrison",
                        "crimes": "crime_records",
                        "tribute": "tribute_records"
                    }
                    
                    registry_key = registry_map.get(registry_type, registry_type)
                    items = city.get(registry_key, [])
                    return len(items)
                else:
                    return 0
        except:
            return 0

    async def check_kingdom_specific_event(self, kingdom_id, registry_type, city_name):
        """Check if event was created with kingdom_id tag"""
        try:
            async with self.session.get(f"{API_BASE}/events?limit=20") as response:
                if response.status == 200:
                    events = await response.json()
                    
                    # Look for recent events with kingdom_id
                    current_time = datetime.utcnow()
                    
                    for event in events:
                        # Check if event has kingdom_id
                        if event.get('kingdom_id') == kingdom_id:
                            event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                            time_diff = (current_time - event_time.replace(tzinfo=None)).total_seconds()
                            
                            if time_diff <= 60:  # Within last minute
                                description = event['description'].lower()
                                city_match = city_name.lower() in description
                                
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

    async def test_real_time_dashboard_updates(self):
        """Test that simulation engine events actually modify database counts"""
        print("\n📊 Testing Real-time Dashboard Updates from Events...")
        
        try:
            # Get initial kingdom state
            async with self.session.get(f"{API_BASE}/active-kingdom") as response:
                if response.status != 200:
                    self.errors.append("Cannot test dashboard updates - Active kingdom API failed")
                    return False
                
                initial_kingdom = await response.json()
                kingdom_id = initial_kingdom['id']
                initial_population = initial_kingdom.get('total_population', 0)
                
                print(f"   Initial kingdom population: {initial_population}")
                
                # Get initial city populations
                initial_city_populations = {}
                for city in initial_kingdom.get('cities', []):
                    initial_city_populations[city['id']] = {
                        'name': city['name'],
                        'population': city.get('population', 0),
                        'citizens': len(city.get('citizens', [])),
                        'treasury': city.get('treasury', 0)
                    }
                
                print(f"   Monitoring {len(initial_city_populations)} cities for changes...")
                
                # Wait for simulation engine to generate life events
                print("   Waiting 60 seconds for life events that modify database...")
                await asyncio.sleep(60)
                
                # Check for database changes
                async with self.session.get(f"{API_BASE}/multi-kingdom/{kingdom_id}") as response:
                    if response.status != 200:
                        self.errors.append("Failed to get updated kingdom data")
                        return False
                    
                    updated_kingdom = await response.json()
                    updated_population = updated_kingdom.get('total_population', 0)
                    
                    print(f"   Updated kingdom population: {updated_population}")
                    
                    # Check for population changes
                    population_changed = updated_population != initial_population
                    
                    # Check individual city changes
                    city_changes = []
                    for city in updated_kingdom.get('cities', []):
                        city_id = city['id']
                        if city_id in initial_city_populations:
                            initial = initial_city_populations[city_id]
                            current_pop = city.get('population', 0)
                            current_citizens = len(city.get('citizens', []))
                            current_treasury = city.get('treasury', 0)
                            
                            if (current_pop != initial['population'] or 
                                current_citizens != initial['citizens'] or
                                current_treasury != initial['treasury']):
                                
                                city_changes.append({
                                    'name': city['name'],
                                    'population_change': current_pop - initial['population'],
                                    'citizens_change': current_citizens - initial['citizens'],
                                    'treasury_change': current_treasury - initial['treasury']
                                })
                    
                    # Check for life events in recent events
                    life_events_found = await self.check_for_life_events(kingdom_id)
                    
                    # Evaluate results
                    if population_changed or city_changes or life_events_found:
                        print("   ✅ Real-time database updates detected:")
                        
                        if population_changed:
                            change = updated_population - initial_population
                            print(f"      📈 Kingdom population changed by {change}")
                        
                        for change in city_changes:
                            print(f"      🏘️ {change['name']}:")
                            if change['population_change'] != 0:
                                print(f"         Population: {change['population_change']:+d}")
                            if change['citizens_change'] != 0:
                                print(f"         Citizens: {change['citizens_change']:+d}")
                            if change['treasury_change'] != 0:
                                print(f"         Treasury: {change['treasury_change']:+d} GP")
                        
                        if life_events_found:
                            print(f"      📜 Life events with database impact found")
                        
                        self.test_results['real_time_dashboard_updates'] = True
                        return True
                    else:
                        print("   ⚠️ No database changes detected during monitoring period")
                        print("      This could mean:")
                        print("      - Simulation engine is not generating life events")
                        print("      - Life events are not modifying database")
                        print("      - Monitoring period was too short")
                        
                        # Still check if the system is capable of updates
                        if life_events_found:
                            print("      ✅ Life events are being generated (system is working)")
                            self.test_results['real_time_dashboard_updates'] = True
                            return True
                        else:
                            self.errors.append("No life events or database changes detected")
                            self.test_results['real_time_dashboard_updates'] = False
                            return False
                
        except Exception as e:
            self.errors.append(f"Real-time dashboard updates test error: {str(e)}")
            return False

    async def check_for_life_events(self, kingdom_id):
        """Check for life events that should modify database"""
        try:
            async with self.session.get(f"{API_BASE}/events?limit=50") as response:
                if response.status == 200:
                    events = await response.json()
                    
                    # Look for life events in the last 2 minutes
                    current_time = datetime.utcnow()
                    life_event_indicators = [
                        "died", "death", "passed away", "born", "birth", "executed", 
                        "population decreased", "population increased", "treasury",
                        "disease outbreak", "natural disaster", "economic boost"
                    ]
                    
                    life_events_found = 0
                    for event in events:
                        # Check if event belongs to this kingdom
                        if event.get('kingdom_id') == kingdom_id:
                            event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                            time_diff = (current_time - event_time.replace(tzinfo=None)).total_seconds()
                            
                            if time_diff <= 120:  # Within last 2 minutes
                                description = event['description'].lower()
                                
                                if any(indicator in description for indicator in life_event_indicators):
                                    life_events_found += 1
                                    print(f"      📜 Life event: {event['description'][:80]}...")
                    
                    return life_events_found > 0
                else:
                    return False
        except:
            return False

    async def run_all_tests(self):
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
            
            # PRIORITY TESTS FOR CURRENT FOCUS
            print("\n" + "🎯" * 20 + " PRIORITY TESTS " + "🎯" * 20)
            await self.test_multi_kingdom_autogenerate_functionality()
            await self.test_real_time_dashboard_updates()
            print("🎯" * 60)
            
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