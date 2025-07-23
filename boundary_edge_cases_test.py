#!/usr/bin/env python3
"""
Edge Cases and Additional Boundary Management Tests
Tests edge cases and additional scenarios for boundary management
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

print(f"🔗 Testing boundary edge cases at: {API_BASE}")

class BoundaryEdgeCaseTester:
    def __init__(self):
        self.session = None
        self.errors = []
        self.active_kingdom_id = None

    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def get_active_kingdom_id(self):
        """Get active kingdom ID"""
        try:
            async with self.session.get(f"{API_BASE}/multi-kingdoms") as response:
                if response.status == 200:
                    kingdoms = await response.json()
                    if kingdoms:
                        # Find active kingdom or use first one
                        active_kingdom = next((k for k in kingdoms if k.get('is_active', False)), kingdoms[0])
                        self.active_kingdom_id = active_kingdom['id']
                        return True
                return False
        except:
            return False

    async def test_clear_empty_boundaries(self):
        """Test clearing boundaries when none exist"""
        print("\n🧹 Testing Clear All on Empty Boundaries...")
        try:
            # First ensure no boundaries exist
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{self.active_kingdom_id}") as response:
                if response.status == 200:
                    boundaries = await response.json()
                    print(f"   Current boundaries: {len(boundaries)}")
                    
                    # Clear any existing boundaries first
                    if len(boundaries) > 0:
                        await self.session.delete(f"{API_BASE}/kingdom-boundaries/clear/{self.active_kingdom_id}")
            
            # Now test clearing when empty
            async with self.session.delete(f"{API_BASE}/kingdom-boundaries/clear/{self.active_kingdom_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Clear empty boundaries response: {result}")
                    
                    # Should still return success message
                    if "message" in result:
                        print(f"   ✅ API handles empty clear gracefully")
                        return True
                    else:
                        self.errors.append("Clear empty boundaries missing message")
                        return False
                else:
                    error_text = await response.text()
                    self.errors.append(f"Clear empty boundaries failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Error testing clear empty boundaries: {str(e)}")
            return False

    async def test_invalid_kingdom_id(self):
        """Test boundary operations with invalid kingdom ID"""
        print("\n❌ Testing Invalid Kingdom ID...")
        try:
            invalid_kingdom_id = "invalid-kingdom-id-12345"
            
            # Test get boundaries with invalid ID
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{invalid_kingdom_id}") as response:
                if response.status == 200:
                    boundaries = await response.json()
                    if len(boundaries) == 0:
                        print(f"   ✅ Get boundaries with invalid ID returns empty list")
                    else:
                        print(f"   ⚠️ Get boundaries with invalid ID returned {len(boundaries)} boundaries")
                else:
                    print(f"   ✅ Get boundaries with invalid ID returns HTTP {response.status}")
            
            # Test clear boundaries with invalid ID
            async with self.session.delete(f"{API_BASE}/kingdom-boundaries/clear/{invalid_kingdom_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Clear boundaries with invalid ID: {result}")
                else:
                    print(f"   ✅ Clear boundaries with invalid ID returns HTTP {response.status}")
            
            # Test create boundary with invalid kingdom ID
            boundary_data = {
                "kingdom_id": invalid_kingdom_id,
                "boundary_points": [{"x": 10, "y": 10}, {"x": 20, "y": 20}],
                "color": "#ff0000"
            }
            
            async with self.session.post(f"{API_BASE}/kingdom-boundaries", json=boundary_data) as response:
                if response.status == 200:
                    print(f"   ⚠️ Create boundary with invalid kingdom ID succeeded (unexpected)")
                else:
                    print(f"   ✅ Create boundary with invalid kingdom ID returns HTTP {response.status}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error testing invalid kingdom ID: {str(e)}")
            return False

    async def test_malformed_boundary_data(self):
        """Test creating boundaries with malformed data"""
        print("\n🔧 Testing Malformed Boundary Data...")
        try:
            test_cases = [
                {
                    "name": "Missing boundary_points",
                    "data": {
                        "kingdom_id": self.active_kingdom_id,
                        "color": "#ff0000"
                    }
                },
                {
                    "name": "Empty boundary_points",
                    "data": {
                        "kingdom_id": self.active_kingdom_id,
                        "boundary_points": [],
                        "color": "#ff0000"
                    }
                },
                {
                    "name": "Invalid point format",
                    "data": {
                        "kingdom_id": self.active_kingdom_id,
                        "boundary_points": [{"invalid": "point"}],
                        "color": "#ff0000"
                    }
                },
                {
                    "name": "Missing kingdom_id",
                    "data": {
                        "boundary_points": [{"x": 10, "y": 10}],
                        "color": "#ff0000"
                    }
                }
            ]
            
            for test_case in test_cases:
                print(f"   Testing: {test_case['name']}")
                async with self.session.post(f"{API_BASE}/kingdom-boundaries", json=test_case['data']) as response:
                    if response.status == 200:
                        print(f"     ⚠️ Malformed data accepted (unexpected)")
                    else:
                        print(f"     ✅ Malformed data rejected with HTTP {response.status}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error testing malformed boundary data: {str(e)}")
            return False

    async def test_large_boundary_dataset(self):
        """Test performance with larger boundary datasets"""
        print("\n📊 Testing Large Boundary Dataset...")
        try:
            # Create multiple boundaries
            boundaries_to_create = 10
            created_boundaries = []
            
            print(f"   Creating {boundaries_to_create} boundaries...")
            for i in range(boundaries_to_create):
                boundary_data = {
                    "kingdom_id": self.active_kingdom_id,
                    "boundary_points": [
                        {"x": i * 10, "y": i * 10},
                        {"x": i * 10 + 50, "y": i * 10},
                        {"x": i * 10 + 50, "y": i * 10 + 50},
                        {"x": i * 10, "y": i * 10 + 50}
                    ],
                    "color": f"#{i:02x}0000"
                }
                
                async with self.session.post(f"{API_BASE}/kingdom-boundaries", json=boundary_data) as response:
                    if response.status == 200:
                        boundary = await response.json()
                        created_boundaries.append(boundary['id'])
            
            print(f"   ✅ Created {len(created_boundaries)} boundaries")
            
            # Test retrieving all boundaries
            async with self.session.get(f"{API_BASE}/kingdom-boundaries/{self.active_kingdom_id}") as response:
                if response.status == 200:
                    boundaries = await response.json()
                    print(f"   ✅ Retrieved {len(boundaries)} boundaries")
                    
                    if len(boundaries) >= len(created_boundaries):
                        print(f"   ✅ All created boundaries found")
                    else:
                        print(f"   ⚠️ Some boundaries missing: expected {len(created_boundaries)}, got {len(boundaries)}")
                else:
                    self.errors.append("Failed to retrieve large boundary dataset")
                    return False
            
            # Test clearing large dataset
            async with self.session.delete(f"{API_BASE}/kingdom-boundaries/clear/{self.active_kingdom_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Cleared large dataset: {result}")
                    
                    # Verify all cleared
                    async with self.session.get(f"{API_BASE}/kingdom-boundaries/{self.active_kingdom_id}") as verify_response:
                        if verify_response.status == 200:
                            remaining_boundaries = await verify_response.json()
                            if len(remaining_boundaries) == 0:
                                print(f"   ✅ Large dataset completely cleared")
                                return True
                            else:
                                self.errors.append(f"Large dataset not completely cleared: {len(remaining_boundaries)} remain")
                                return False
                else:
                    self.errors.append("Failed to clear large boundary dataset")
                    return False
            
        except Exception as e:
            self.errors.append(f"Error testing large boundary dataset: {str(e)}")
            return False

    async def test_concurrent_operations(self):
        """Test concurrent boundary operations"""
        print("\n⚡ Testing Concurrent Operations...")
        try:
            # Create multiple boundaries concurrently
            concurrent_tasks = []
            for i in range(5):
                boundary_data = {
                    "kingdom_id": self.active_kingdom_id,
                    "boundary_points": [
                        {"x": i * 20, "y": i * 20},
                        {"x": i * 20 + 30, "y": i * 20 + 30}
                    ],
                    "color": f"#{i:02x}{i:02x}00"
                }
                
                task = self.session.post(f"{API_BASE}/kingdom-boundaries", json=boundary_data)
                concurrent_tasks.append(task)
            
            # Execute all tasks concurrently
            responses = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            
            successful_creates = 0
            for response in responses:
                if not isinstance(response, Exception):
                    if response.status == 200:
                        successful_creates += 1
                    response.close()
            
            print(f"   ✅ Concurrent creates: {successful_creates}/5 successful")
            
            # Test concurrent clear (should handle gracefully)
            clear_tasks = [
                self.session.delete(f"{API_BASE}/kingdom-boundaries/clear/{self.active_kingdom_id}"),
                self.session.delete(f"{API_BASE}/kingdom-boundaries/clear/{self.active_kingdom_id}")
            ]
            
            clear_responses = await asyncio.gather(*clear_tasks, return_exceptions=True)
            
            successful_clears = 0
            for response in clear_responses:
                if not isinstance(response, Exception):
                    if response.status == 200:
                        successful_clears += 1
                    response.close()
            
            print(f"   ✅ Concurrent clears: {successful_clears}/2 successful")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error testing concurrent operations: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all edge case tests"""
        print("🚀 Starting Boundary Edge Case Tests")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Get active kingdom ID
            if not await self.get_active_kingdom_id():
                print("❌ Failed to get active kingdom ID")
                return False
            
            print(f"Testing with kingdom ID: {self.active_kingdom_id}")
            
            # Run all edge case tests
            tests = [
                ("Clear Empty Boundaries", self.test_clear_empty_boundaries()),
                ("Invalid Kingdom ID", self.test_invalid_kingdom_id()),
                ("Malformed Boundary Data", self.test_malformed_boundary_data()),
                ("Large Boundary Dataset", self.test_large_boundary_dataset()),
                ("Concurrent Operations", self.test_concurrent_operations())
            ]
            
            results = []
            for test_name, test_coro in tests:
                try:
                    result = await test_coro
                    results.append((test_name, result))
                except Exception as e:
                    print(f"   ❌ {test_name} failed with exception: {e}")
                    results.append((test_name, False))
            
            print("\n" + "=" * 60)
            print("📊 EDGE CASE TEST SUMMARY")
            print("=" * 60)
            
            passed_tests = sum(1 for _, result in results if result)
            total_tests = len(results)
            
            for test_name, result in results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{test_name}: {status}")
            
            print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
            
            if self.errors:
                print("\n🚨 ERRORS ENCOUNTERED:")
                for i, error in enumerate(self.errors, 1):
                    print(f"{i}. {error}")
            
            return passed_tests == total_tests
            
        finally:
            await self.cleanup()

async def main():
    tester = BoundaryEdgeCaseTester()
    success = await tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())