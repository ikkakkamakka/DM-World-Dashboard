#!/usr/bin/env python3
"""
Comprehensive Authentication System Testing
Tests additional security scenarios and edge cases
"""

import asyncio
import aiohttp
import json
import sys
import jwt
import time

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

print(f"🔗 Testing comprehensive authentication at: {API_BASE}")

class ComprehensiveAuthTester:
    def __init__(self):
        self.session = None
        self.errors = []
        self.test_auth_token = None
        self.test_username = None
        self.test_password = None

    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def test_jwt_token_structure(self):
        """Test JWT token structure and content"""
        print("\n🔍 Testing JWT Token Structure and Content...")
        try:
            timestamp = str(int(time.time()))
            
            # Create test user
            test_user = {
                "username": f"jwt_test_{timestamp}",
                "email": f"jwt_test_{timestamp}@faeruncampaign.com",
                "password": "JWTTestPassword123!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/signup", json=test_user) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data['access_token']
                    
                    # Decode JWT token without verification to check structure
                    try:
                        # Decode header
                        header = jwt.get_unverified_header(token)
                        print(f"   JWT Header: {header}")
                        
                        # Check algorithm
                        if header.get('alg') != 'HS256':
                            self.errors.append(f"Expected HS256 algorithm, got {header.get('alg')}")
                            return False
                        
                        # Decode payload without verification
                        payload = jwt.decode(token, options={"verify_signature": False})
                        print(f"   JWT Payload keys: {list(payload.keys())}")
                        
                        # Check required claims
                        required_claims = ['sub', 'exp']
                        missing_claims = [claim for claim in required_claims if claim not in payload]
                        
                        if missing_claims:
                            self.errors.append(f"JWT missing required claims: {missing_claims}")
                            return False
                        
                        # Check subject matches username
                        if payload['sub'] != test_user['username']:
                            self.errors.append(f"JWT subject mismatch: expected {test_user['username']}, got {payload['sub']}")
                            return False
                        
                        # Check expiration is in the future
                        if payload['exp'] <= time.time():
                            self.errors.append("JWT token already expired")
                            return False
                        
                        print(f"   ✅ JWT token structure valid")
                        print(f"   Subject: {payload['sub']}")
                        print(f"   Expires: {payload['exp']} (in {payload['exp'] - time.time():.0f} seconds)")
                        
                        return True
                        
                    except Exception as jwt_error:
                        self.errors.append(f"JWT decoding error: {jwt_error}")
                        return False
                        
                else:
                    error_text = await response.text()
                    self.errors.append(f"JWT test signup failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"JWT token structure test error: {str(e)}")
            return False

    async def test_duplicate_registration_edge_cases(self):
        """Test various duplicate registration scenarios"""
        print("\n👥 Testing Duplicate Registration Edge Cases...")
        try:
            timestamp = str(int(time.time()))
            
            # Create initial user
            base_user = {
                "username": f"duplicate_test_{timestamp}",
                "email": f"duplicate_test_{timestamp}@faeruncampaign.com",
                "password": "DuplicateTestPassword123!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/signup", json=base_user) as response:
                if response.status != 200:
                    self.errors.append("Failed to create base user for duplicate testing")
                    return False
            
            # Test 1: Exact duplicate
            async with self.session.post(f"{API_BASE}/auth/signup", json=base_user) as response:
                if response.status != 400:
                    self.errors.append(f"Exact duplicate should return 400, got {response.status}")
                    return False
                
                data = await response.json()
                if 'username' not in data['detail'].lower():
                    self.errors.append("Duplicate username error should mention username")
                    return False
            
            print(f"   ✅ Exact duplicate correctly rejected")
            
            # Test 2: Same username, different email
            different_email_user = {
                "username": base_user['username'],  # Same username
                "email": f"different_{timestamp}@faeruncampaign.com",  # Different email
                "password": "DifferentPassword123!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/signup", json=different_email_user) as response:
                if response.status != 400:
                    self.errors.append(f"Duplicate username should return 400, got {response.status}")
                    return False
            
            print(f"   ✅ Duplicate username with different email correctly rejected")
            
            # Test 3: Different username, same email
            different_username_user = {
                "username": f"different_user_{timestamp}",  # Different username
                "email": base_user['email'],  # Same email
                "password": "DifferentPassword123!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/signup", json=different_username_user) as response:
                if response.status != 400:
                    self.errors.append(f"Duplicate email should return 400, got {response.status}")
                    return False
                
                data = await response.json()
                if 'email' not in data['detail'].lower():
                    self.errors.append("Duplicate email error should mention email")
                    return False
            
            print(f"   ✅ Duplicate email with different username correctly rejected")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Duplicate registration test error: {str(e)}")
            return False

    async def test_password_validation(self):
        """Test password validation requirements"""
        print("\n🔐 Testing Password Validation...")
        try:
            timestamp = str(int(time.time()))
            
            # Test weak passwords
            weak_passwords = [
                "123",  # Too short
                "short",  # Too short
                "12345",  # Too short
            ]
            
            for i, weak_password in enumerate(weak_passwords):
                test_user = {
                    "username": f"weak_pass_test_{timestamp}_{i}",
                    "email": f"weak_pass_test_{timestamp}_{i}@faeruncampaign.com",
                    "password": weak_password
                }
                
                async with self.session.post(f"{API_BASE}/auth/signup", json=test_user) as response:
                    if response.status not in [400, 422]:  # Should be validation error
                        self.errors.append(f"Weak password '{weak_password}' should be rejected, got {response.status}")
                        return False
            
            print(f"   ✅ Weak passwords correctly rejected")
            
            # Test valid strong password
            strong_user = {
                "username": f"strong_pass_test_{timestamp}",
                "email": f"strong_pass_test_{timestamp}@faeruncampaign.com",
                "password": "StrongPassword123!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/signup", json=strong_user) as response:
                if response.status != 200:
                    self.errors.append(f"Strong password should be accepted, got {response.status}")
                    return False
            
            print(f"   ✅ Strong password correctly accepted")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Password validation test error: {str(e)}")
            return False

    async def test_invalid_token_scenarios(self):
        """Test various invalid token scenarios"""
        print("\n🚫 Testing Invalid Token Scenarios...")
        try:
            # Test 1: No token
            async with self.session.get(f"{API_BASE}/auth/me") as response:
                if response.status != 401:
                    self.errors.append(f"No token should return 401, got {response.status}")
                    return False
            
            print(f"   ✅ No token correctly rejected (401)")
            
            # Test 2: Invalid token format
            invalid_headers = {"Authorization": "Bearer invalid.token.format"}
            async with self.session.get(f"{API_BASE}/auth/me", headers=invalid_headers) as response:
                if response.status != 401:
                    self.errors.append(f"Invalid token format should return 401, got {response.status}")
                    return False
            
            print(f"   ✅ Invalid token format correctly rejected (401)")
            
            # Test 3: Malformed Authorization header
            malformed_headers = {"Authorization": "InvalidFormat token"}
            async with self.session.get(f"{API_BASE}/auth/me", headers=malformed_headers) as response:
                if response.status != 401:
                    self.errors.append(f"Malformed auth header should return 401, got {response.status}")
                    return False
            
            print(f"   ✅ Malformed authorization header correctly rejected (401)")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Invalid token test error: {str(e)}")
            return False

    async def test_database_separation_comprehensive(self):
        """Comprehensive test of database separation"""
        print("\n🗄️ Testing Comprehensive Database Separation...")
        try:
            timestamp = str(int(time.time()))
            
            # Create test user
            test_user = {
                "username": f"db_sep_test_{timestamp}",
                "email": f"db_sep_test_{timestamp}@faeruncampaign.com",
                "password": "DatabaseSeparationTest123!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/signup", json=test_user) as response:
                if response.status != 200:
                    self.errors.append("Failed to create user for database separation test")
                    return False
                
                data = await response.json()
                token = data['access_token']
            
            # Test that user operations don't affect kingdom data
            async with self.session.get(f"{API_BASE}/kingdom") as kingdom_response:
                if kingdom_response.status != 200:
                    self.errors.append("Kingdom API not accessible during database separation test")
                    return False
                
                kingdom_data_before = await kingdom_response.json()
                initial_city_count = len(kingdom_data_before.get('cities', []))
            
            # Perform user operations
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.get(f"{API_BASE}/auth/me", headers=headers) as me_response:
                if me_response.status != 200:
                    self.errors.append("Auth /me not accessible during database separation test")
                    return False
                
                user_data = await me_response.json()
            
            # Verify kingdom data unchanged
            async with self.session.get(f"{API_BASE}/kingdom") as kingdom_response2:
                if kingdom_response2.status != 200:
                    self.errors.append("Kingdom API not accessible after auth operations")
                    return False
                
                kingdom_data_after = await kingdom_response2.json()
                final_city_count = len(kingdom_data_after.get('cities', []))
            
            if initial_city_count != final_city_count:
                self.errors.append("Auth operations affected kingdom data - database separation failed")
                return False
            
            # Verify data types are completely separate
            kingdom_fields = set(kingdom_data_after.keys())
            user_fields = set(user_data.keys())
            
            # Should have no overlap except maybe common fields like 'id'
            overlap = kingdom_fields.intersection(user_fields) - {'id'}
            if overlap:
                self.errors.append(f"Kingdom and user data have overlapping fields: {overlap}")
                return False
            
            print(f"   ✅ Database separation verified")
            print(f"   Kingdom fields: {sorted(kingdom_fields)}")
            print(f"   User fields: {sorted(user_fields)}")
            print(f"   No inappropriate field overlap")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Database separation test error: {str(e)}")
            return False

    async def run_comprehensive_tests(self):
        print("🔐 Starting Comprehensive Authentication Tests")
        print("=" * 55)
        
        await self.setup()
        
        test_results = {}
        
        try:
            # Test JWT token structure
            test_results['jwt_structure'] = await self.test_jwt_token_structure()
            
            # Test duplicate registration edge cases
            test_results['duplicate_edge_cases'] = await self.test_duplicate_registration_edge_cases()
            
            # Test password validation
            test_results['password_validation'] = await self.test_password_validation()
            
            # Test invalid token scenarios
            test_results['invalid_tokens'] = await self.test_invalid_token_scenarios()
            
            # Test comprehensive database separation
            test_results['database_separation'] = await self.test_database_separation_comprehensive()
            
        finally:
            await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 55)
        print("📊 COMPREHENSIVE AUTHENTICATION TEST SUMMARY")
        print("=" * 55)
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if self.errors:
            print("\n🚨 ERRORS ENCOUNTERED:")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")
        
        return passed == total

async def main():
    tester = ComprehensiveAuthTester()
    success = await tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 All comprehensive authentication tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some comprehensive authentication tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())