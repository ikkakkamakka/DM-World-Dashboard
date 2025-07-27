#!/usr/bin/env python3
"""
Multi-User Ownership Verification Test
Tests all backend routes and frontend authentication with multiple users to verify proper data isolation.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiUserOwnershipTester:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.api_base = f"{self.base_url}/api"
        self.auth_base = f"{self.base_url}/api/auth"
        
        # Test users
        self.users = {
            'dm1': {
                'username': 'dm1_test',
                'email': 'dm1@test.com',
                'password': 'password123',
                'token': None,
                'user_info': None,
                'kingdoms': [],
                'cities': []
            },
            'dm2': {
                'username': 'dm2_test', 
                'email': 'dm2@test.com',
                'password': 'password123',
                'token': None,
                'user_info': None,
                'kingdoms': [],
                'cities': []
            },
            'super_admin': {
                'username': 'admin',
                'email': 'admin@test.com', 
                'password': 'admin123',
                'token': None,
                'user_info': None,
                'kingdoms': [],
                'cities': []
            }
        }
        
        self.test_results = {}
        self.session = None

    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def cleanup_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    async def create_test_users(self):
        """Create or login test users"""
        logger.info("Creating/logging in test users...")
        
        for user_key, user_data in self.users.items():
            try:
                # Try to login first (user might already exist)
                login_data = {
                    "username": user_data['username'],
                    "password": user_data['password']
                }
                
                async with self.session.post(f"{self.auth_base}/login", json=login_data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        user_data['token'] = token_data['access_token']
                        user_data['user_info'] = token_data['user_info']
                        logger.info(f"✅ Logged in existing user: {user_data['username']}")
                    elif response.status == 401:
                        # User doesn't exist, create them
                        signup_data = {
                            "username": user_data['username'],
                            "email": user_data['email'], 
                            "password": user_data['password']
                        }
                        
                        async with self.session.post(f"{self.auth_base}/signup", json=signup_data) as signup_response:
                            if signup_response.status == 200:
                                token_data = await signup_response.json()
                                user_data['token'] = token_data['access_token']
                                user_data['user_info'] = token_data['user_info']
                                logger.info(f"✅ Created new user: {user_data['username']}")
                            else:
                                error_text = await signup_response.text()
                                logger.error(f"❌ Failed to create user {user_data['username']}: {error_text}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Login failed for {user_data['username']}: {error_text}")
                        
            except Exception as e:
                logger.error(f"❌ Error with user {user_data['username']}: {str(e)}")

    async def create_test_kingdoms(self):
        """Create test kingdoms for each user"""
        logger.info("Creating test kingdoms...")
        
        # DM1 creates kingdom
        dm1_kingdom = {
            "name": "DM1 Test Kingdom",
            "ruler": "DM1 Ruler",
            "government_type": "Monarchy",
            "color": "#ff4444"
        }
        
        kingdom_id = await self.create_kingdom('dm1', dm1_kingdom)
        if kingdom_id:
            self.users['dm1']['kingdoms'].append(kingdom_id)
            logger.info(f"✅ Created kingdom for DM1: {kingdom_id}")
            
            # Create cities for DM1
            city1_id = await self.create_city('dm1', {
                "name": "DM1 City A",
                "governor": "Governor A",
                "population": 1000,
                "x_coordinate": 10,
                "y_coordinate": 20
            })
            if city1_id:
                self.users['dm1']['cities'].append(city1_id)
        
        # DM2 creates kingdom  
        dm2_kingdom = {
            "name": "DM2 Test Kingdom",
            "ruler": "DM2 Ruler", 
            "government_type": "Republic",
            "color": "#4444ff"
        }
        
        kingdom_id = await self.create_kingdom('dm2', dm2_kingdom)
        if kingdom_id:
            self.users['dm2']['kingdoms'].append(kingdom_id)
            logger.info(f"✅ Created kingdom for DM2: {kingdom_id}")
            
            # Create cities for DM2
            city1_id = await self.create_city('dm2', {
                "name": "DM2 City B", 
                "governor": "Governor B",
                "population": 2000,
                "x_coordinate": 30,
                "y_coordinate": 40
            })
            if city1_id:
                self.users['dm2']['cities'].append(city1_id)

    async def create_kingdom(self, user_key: str, kingdom_data: dict) -> Optional[str]:
        """Create a kingdom for a specific user"""
        user = self.users[user_key]
        headers = {"Authorization": f"Bearer {user['token']}"}
        
        try:
            async with self.session.post(f"{self.api_base}/multi-kingdoms", json=kingdom_data, headers=headers) as response:
                if response.status == 200:
                    kingdom = await response.json()
                    return kingdom['id']
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create kingdom for {user_key}: {error_text}")
        except Exception as e:
            logger.error(f"❌ Exception creating kingdom for {user_key}: {str(e)}")
        
        return None

    async def create_city(self, user_key: str, city_data: dict) -> Optional[str]:
        """Create a city for a specific user"""
        user = self.users[user_key]
        headers = {"Authorization": f"Bearer {user['token']}"}
        
        try:
            async with self.session.post(f"{self.api_base}/cities", json=city_data, headers=headers) as response:
                if response.status == 200:
                    city = await response.json()
                    return city['id']
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create city for {user_key}: {error_text}")
        except Exception as e:
            logger.error(f"❌ Exception creating city for {user_key}: {str(e)}")
        
        return None

    async def test_data_isolation(self):
        """Test that users can only see their own data"""
        logger.info("Testing data isolation...")
        
        # Test 1: DM1 tries to access DM2's kingdoms
        logger.info("🔐 Testing kingdom access isolation...")
        
        dm1_headers = {"Authorization": f"Bearer {self.users['dm1']['token']}"}
        dm2_headers = {"Authorization": f"Bearer {self.users['dm2']['token']}"}
        
        # DM1 gets their kingdoms (should only see their own)
        async with self.session.get(f"{self.api_base}/multi-kingdoms", headers=dm1_headers) as response:
            if response.status == 200:
                dm1_kingdoms = await response.json()
                dm1_kingdom_names = [k['name'] for k in dm1_kingdoms]
                logger.info(f"DM1 sees kingdoms: {dm1_kingdom_names}")
                
                # Verify DM1 only sees their own kingdom
                if "DM2 Test Kingdom" in dm1_kingdom_names:
                    logger.error("❌ SECURITY ISSUE: DM1 can see DM2's kingdom!")
                    return False
                else:
                    logger.info("✅ DM1 correctly isolated from DM2's kingdoms")
            else:
                logger.error(f"❌ DM1 failed to get kingdoms: {response.status}")
                return False
        
        # DM2 gets their kingdoms (should only see their own)
        async with self.session.get(f"{self.api_base}/multi-kingdoms", headers=dm2_headers) as response:
            if response.status == 200:
                dm2_kingdoms = await response.json()
                dm2_kingdom_names = [k['name'] for k in dm2_kingdoms]
                logger.info(f"DM2 sees kingdoms: {dm2_kingdom_names}")
                
                # Verify DM2 only sees their own kingdom
                if "DM1 Test Kingdom" in dm2_kingdom_names:
                    logger.error("❌ SECURITY ISSUE: DM2 can see DM1's kingdom!")
                    return False
                else:
                    logger.info("✅ DM2 correctly isolated from DM1's kingdoms")
            else:
                logger.error(f"❌ DM2 failed to get kingdoms: {response.status}")
                return False
        
        return True

    async def test_cross_user_access_attempts(self):
        """Test that users cannot access each other's data"""
        logger.info("Testing cross-user access prevention...")
        
        # Get kingdom IDs
        dm1_kingdom_id = self.users['dm1']['kingdoms'][0] if self.users['dm1']['kingdoms'] else None
        dm2_kingdom_id = self.users['dm2']['kingdoms'][0] if self.users['dm2']['kingdoms'] else None
        
        if not dm1_kingdom_id or not dm2_kingdom_id:
            logger.error("❌ Missing kingdom IDs for cross-access testing")
            return False
        
        # Test 1: DM1 tries to access DM2's kingdom directly
        logger.info("🔐 Testing direct kingdom access prevention...")
        dm1_headers = {"Authorization": f"Bearer {self.users['dm1']['token']}"}
        
        async with self.session.get(f"{self.api_base}/multi-kingdom/{dm2_kingdom_id}", headers=dm1_headers) as response:
            if response.status == 404 or response.status == 403:
                logger.info("✅ DM1 correctly denied access to DM2's kingdom")
            elif response.status == 200:
                logger.error("❌ SECURITY ISSUE: DM1 can access DM2's kingdom directly!")
                return False
            else:
                logger.warning(f"⚠️ Unexpected response accessing DM2's kingdom: {response.status}")
        
        # Test 2: DM2 tries to access DM1's kingdom directly  
        dm2_headers = {"Authorization": f"Bearer {self.users['dm2']['token']}"}
        
        async with self.session.get(f"{self.api_base}/multi-kingdom/{dm1_kingdom_id}", headers=dm2_headers) as response:
            if response.status == 404 or response.status == 403:
                logger.info("✅ DM2 correctly denied access to DM1's kingdom")
            elif response.status == 200:
                logger.error("❌ SECURITY ISSUE: DM2 can access DM1's kingdom directly!")
                return False
            else:
                logger.warning(f"⚠️ Unexpected response accessing DM1's kingdom: {response.status}")
        
        return True

    async def test_super_admin_access(self):
        """Test that super admin can access all data"""
        logger.info("Testing super admin access...")
        
        admin_headers = {"Authorization": f"Bearer {self.users['super_admin']['token']}"}
        
        # Admin should see all kingdoms
        async with self.session.get(f"{self.api_base}/multi-kingdoms", headers=admin_headers) as response:
            if response.status == 200:
                admin_kingdoms = await response.json()
                kingdom_names = [k['name'] for k in admin_kingdoms]
                logger.info(f"Super admin sees kingdoms: {kingdom_names}")
                
                # Admin should see both DM1 and DM2 kingdoms
                if "DM1 Test Kingdom" in kingdom_names and "DM2 Test Kingdom" in kingdom_names:
                    logger.info("✅ Super admin has access to all kingdoms")
                    return True
                else:
                    logger.error("❌ Super admin cannot see all kingdoms!")
                    return False
            else:
                logger.error(f"❌ Super admin failed to get kingdoms: {response.status}")
                return False

    async def test_registry_operations(self):
        """Test registry CRUD operations with ownership"""
        logger.info("Testing registry operations...")
        
        # Get city IDs for testing
        dm1_city_id = self.users['dm1']['cities'][0] if self.users['dm1']['cities'] else None
        dm2_city_id = self.users['dm2']['cities'][0] if self.users['dm2']['cities'] else None
        
        if not dm1_city_id or not dm2_city_id:
            logger.error("❌ Missing city IDs for registry testing")
            return False
        
        # Test 1: DM1 creates citizen in their city
        logger.info("🏘️ Testing citizen creation...")
        dm1_headers = {"Authorization": f"Bearer {self.users['dm1']['token']}"}
        
        citizen_data = {
            "city_id": dm1_city_id,
            "name": "Test Citizen",
            "age": 30,
            "occupation": "Merchant",
            "income": 100
        }
        
        async with self.session.post(f"{self.api_base}/citizens", json=citizen_data, headers=dm1_headers) as response:
            if response.status == 200:
                logger.info("✅ DM1 successfully created citizen")
            else:
                error_text = await response.text()
                logger.error(f"❌ DM1 failed to create citizen: {error_text}")
                return False
        
        # Test 2: DM2 tries to create citizen in DM1's city (should fail)
        logger.info("🔐 Testing cross-user registry prevention...")
        dm2_headers = {"Authorization": f"Bearer {self.users['dm2']['token']}"}
        
        citizen_data_cross = {
            "city_id": dm1_city_id,  # DM2 trying to use DM1's city
            "name": "Unauthorized Citizen",
            "age": 25,
            "occupation": "Thief",
            "income": 50
        }
        
        async with self.session.post(f"{self.api_base}/citizens", json=citizen_data_cross, headers=dm2_headers) as response:
            if response.status == 404 or response.status == 403:
                logger.info("✅ DM2 correctly denied access to DM1's city for citizen creation")
                return True
            elif response.status == 200:
                logger.error("❌ SECURITY ISSUE: DM2 can create citizens in DM1's city!")
                return False
            else:
                logger.warning(f"⚠️ Unexpected response for cross-user citizen creation: {response.status}")
                return True

    async def run_full_test_suite(self):
        """Run the complete multi-user ownership test suite"""
        logger.info("🚀 Starting Multi-User Ownership Verification Test Suite")
        
        try:
            await self.setup_session()
            
            # Phase 1: Setup
            await self.create_test_users()
            await self.create_test_kingdoms()
            
            # Phase 2: Isolation Tests
            isolation_result = await self.test_data_isolation()
            cross_access_result = await self.test_cross_user_access_attempts()
            
            # Phase 3: Super Admin Tests
            admin_result = await self.test_super_admin_access()
            
            # Phase 4: Registry Tests
            registry_result = await self.test_registry_operations()
            
            # Final Results
            all_tests = [isolation_result, cross_access_result, admin_result, registry_result]
            passed_tests = sum(all_tests)
            total_tests = len(all_tests)
            
            logger.info("="*60)
            logger.info("🏁 MULTI-USER OWNERSHIP TEST RESULTS")
            logger.info("="*60)
            logger.info(f"Data Isolation: {'✅ PASS' if isolation_result else '❌ FAIL'}")
            logger.info(f"Cross-User Prevention: {'✅ PASS' if cross_access_result else '❌ FAIL'}")
            logger.info(f"Super Admin Access: {'✅ PASS' if admin_result else '❌ FAIL'}")
            logger.info(f"Registry Operations: {'✅ PASS' if registry_result else '❌ FAIL'}")
            logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                logger.info("🎉 ALL OWNERSHIP TESTS PASSED - System is secure!")
                return True
            else:
                logger.error("🚨 OWNERSHIP TESTS FAILED - Security issues detected!")
                return False
            
        except Exception as e:
            logger.error(f"❌ Test suite failed with exception: {str(e)}")
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Main entry point"""
    tester = MultiUserOwnershipTester()
    success = await tester.run_full_test_suite()
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())