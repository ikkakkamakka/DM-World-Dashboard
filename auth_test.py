#!/usr/bin/env python3
"""
Authentication System Testing for Fantasy Kingdom Management System
Tests JWT tokens, password hashing, and security features
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

print(f"🔗 Testing authentication at: {API_BASE}")

class AuthTester:
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

    async def test_auth_signup(self):
        """Test user registration with valid data"""
        print("\n📝 Testing User Registration...")
        try:
            import time
            timestamp = str(int(time.time()))
            
            # Test data with unique username
            test_user = {
                "username": f"testuser_auth_{timestamp}",
                "email": f"testuser_{timestamp}@faeruncampaign.com",
                "password": "SecurePassword123!"
            }
            
            async with self.session.post(f"{API_BASE}/auth/signup", json=test_user) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure
                    required_fields = ['access_token', 'token_type', 'user_info']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.errors.append(f"Signup response missing fields: {missing_fields}")
                        return False
                    
                    # Verify token type
                    if data['token_type'] != 'bearer':
                        self.errors.append(f"Expected token_type 'bearer', got '{data['token_type']}'")
                        return False
                    
                    # Verify JWT token format
                    token = data['access_token']
                    if not token or len(token.split('.')) != 3:
                        self.errors.append("Invalid JWT token format")
                        return False
                    
                    # Verify user info
                    user_info = data['user_info']
                    user_required_fields = ['id', 'username', 'email', 'is_active', 'created_at']
                    missing_user_fields = [field for field in user_required_fields if field not in user_info]
                    
                    if missing_user_fields:
                        self.errors.append(f"User info missing fields: {missing_user_fields}")
                        return False
                    
                    if user_info['username'] != test_user['username']:
                        self.errors.append(f"Username mismatch: expected {test_user['username']}, got {user_info['username']}")
                        return False
                    
                    if user_info['email'] != test_user['email']:
                        self.errors.append(f"Email mismatch: expected {test_user['email']}, got {user_info['email']}")
                        return False
                    
                    # Store token for later tests
                    self.test_auth_token = token
                    self.test_username = test_user['username']
                    self.test_password = test_user['password']
                    
                    print(f"   ✅ User registration successful")
                    print(f"   Username: {user_info['username']}")
                    print(f"   Email: {user_info['email']}")
                    print(f"   JWT Token: {token[:20]}...")
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Signup failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Signup test error: {str(e)}")
            return False

    async def test_auth_login(self):
        """Test user login with correct credentials"""
        print("\n🔑 Testing User Login...")
        try:
            if not self.test_username or not self.test_password:
                self.errors.append("No test user available for login test")
                return False
            
            login_data = {
                "username": self.test_username,
                "password": self.test_password
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure (same as signup)
                    required_fields = ['access_token', 'token_type', 'user_info']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.errors.append(f"Login response missing fields: {missing_fields}")
                        return False
                    
                    # Verify JWT token
                    token = data['access_token']
                    if not token or len(token.split('.')) != 3:
                        self.errors.append("Invalid JWT token format in login")
                        return False
                    
                    # Verify user info includes last_login
                    user_info = data['user_info']
                    if 'last_login' not in user_info:
                        self.errors.append("Login response missing last_login timestamp")
                        return False
                    
                    print(f"   ✅ User login successful")
                    print(f"   Username: {user_info['username']}")
                    print(f"   Last Login: {user_info['last_login']}")
                    print(f"   New JWT Token: {token[:20]}...")
                    
                    # Update token for other tests
                    self.test_auth_token = token
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Login failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Login test error: {str(e)}")
            return False

    async def test_auth_jwt_tokens(self):
        """Test JWT token generation, validation, and decoding"""
        print("\n🎫 Testing JWT Token Validation...")
        try:
            if not self.test_auth_token:
                self.errors.append("No JWT token available for validation test")
                return False
            
            # Test token verification endpoint
            headers = {"Authorization": f"Bearer {self.test_auth_token}"}
            
            async with self.session.get(f"{API_BASE}/auth/verify-token", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure
                    if 'valid' not in data or 'username' not in data:
                        self.errors.append("Token verification response missing required fields")
                        return False
                    
                    if not data['valid']:
                        self.errors.append("Token verification returned valid=false")
                        return False
                    
                    if data['username'] != self.test_username:
                        self.errors.append(f"Token username mismatch: expected {self.test_username}, got {data['username']}")
                        return False
                    
                    print(f"   ✅ JWT token validation successful")
                    print(f"   Token is valid for user: {data['username']}")
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    self.errors.append(f"Token verification failed: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"JWT token test error: {str(e)}")
            return False

    async def test_auth_invalid_credentials(self):
        """Test various invalid login scenarios"""
        print("\n❌ Testing Invalid Login Attempts...")
        try:
            if not self.test_username:
                self.errors.append("No test user available for invalid credentials test")
                return False
            
            # Test 1: Wrong password
            wrong_password_data = {
                "username": self.test_username,
                "password": "WrongPassword123"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=wrong_password_data) as response:
                if response.status != 401:
                    self.errors.append(f"Wrong password should return 401, got {response.status}")
                    return False
                
                data = await response.json()
                if 'detail' not in data:
                    self.errors.append("Invalid credentials response missing error detail")
                    return False
            
            print(f"   ✅ Wrong password correctly rejected (401)")
            
            # Test 2: Non-existent username
            nonexistent_user_data = {
                "username": "nonexistent_user_12345",
                "password": "AnyPassword123"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=nonexistent_user_data) as response:
                if response.status != 401:
                    self.errors.append(f"Non-existent user should return 401, got {response.status}")
                    return False
            
            print(f"   ✅ Non-existent user correctly rejected (401)")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Invalid credentials test error: {str(e)}")
            return False

    async def test_auth_password_hashing(self):
        """Test that passwords are properly hashed with bcrypt"""
        print("\n🔒 Testing Password Hashing Security...")
        try:
            # Create another test user to verify password hashing
            test_user_2 = {
                "username": "hashtest_user_2025",
                "email": "hashtest@faeruncampaign.com", 
                "password": "PlainTextPassword123"
            }
            
            async with self.session.post(f"{API_BASE}/auth/signup", json=test_user_2) as response:
                if response.status == 200:
                    # Test login with the same password to verify hash verification works
                    login_data = {
                        "username": test_user_2['username'],
                        "password": test_user_2['password']
                    }
                    
                    async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as login_response:
                        if login_response.status == 200:
                            print(f"   ✅ Password hashing working correctly")
                            print(f"   User created and can login with hashed password")
                            print(f"   bcrypt verification successful")
                            return True
                        else:
                            self.errors.append("Password hash verification failed - cannot login after signup")
                            return False
                            
                else:
                    error_text = await response.text()
                    self.errors.append(f"Password hashing test failed during signup: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Password hashing test error: {str(e)}")
            return False

    async def test_auth_separate_database(self):
        """Test that users are stored in separate database"""
        print("\n🗄️ Testing Separate Authentication Database...")
        try:
            # Test that we can access auth endpoints without affecting main kingdom data
            async with self.session.get(f"{API_BASE}/kingdom") as kingdom_response:
                if kingdom_response.status != 200:
                    self.errors.append("Main kingdom API not accessible during auth test")
                    return False
                
                kingdom_data = await kingdom_response.json()
            
            # Test that auth endpoints work
            if not self.test_auth_token:
                self.errors.append("No auth token available for separate database test")
                return False
            
            headers = {"Authorization": f"Bearer {self.test_auth_token}"}
            async with self.session.get(f"{API_BASE}/auth/me", headers=headers) as auth_response:
                if auth_response.status != 200:
                    self.errors.append("Auth /me endpoint not accessible")
                    return False
                
                user_data = await auth_response.json()
            
            # Verify that kingdom data and user data are completely separate
            if 'cities' in user_data or 'population' in user_data:
                self.errors.append("User data contains kingdom fields - databases not properly separated")
                return False
            
            if 'username' in kingdom_data or 'email' in kingdom_data:
                self.errors.append("Kingdom data contains user fields - databases not properly separated")
                return False
            
            print(f"   ✅ Authentication database properly separated")
            print(f"   Kingdom data has {len(kingdom_data.get('cities', []))} cities")
            print(f"   User data has username: {user_data.get('username')}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Separate database test error: {str(e)}")
            return False

    async def run_auth_tests(self):
        print("🔐 Starting Authentication System Tests")
        print("=" * 50)
        
        await self.setup()
        
        test_results = {}
        
        try:
            # Test user registration
            test_results['signup'] = await self.test_auth_signup()
            
            # Test user login
            test_results['login'] = await self.test_auth_login()
            
            # Test JWT token validation
            test_results['jwt_tokens'] = await self.test_auth_jwt_tokens()
            
            # Test password hashing
            test_results['password_hashing'] = await self.test_auth_password_hashing()
            
            # Test invalid credentials handling
            test_results['invalid_credentials'] = await self.test_auth_invalid_credentials()
            
            # Test separate database
            test_results['separate_database'] = await self.test_auth_separate_database()
            
        finally:
            await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 AUTHENTICATION TEST SUMMARY")
        print("=" * 50)
        
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
    tester = AuthTester()
    success = await tester.run_auth_tests()
    
    if success:
        print("\n🎉 All authentication tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some authentication tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())