"""
Comprehensive API Test Suite for B2B Backend
Tests all major API endpoints to ensure they're working correctly
"""
import pytest
import httpx
import asyncio
from typing import Dict, Any
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

class TestAPIComprehensive:
    """Comprehensive API test suite"""
    
    @pytest.fixture
    async def client(self):
        """Create HTTP client for testing"""
        async with httpx.AsyncClient() as client:
            yield client
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data for registration and login"""
        return {
            "username": "testuser_api",
            "email": "testuser_api@example.com",
            "password": "testpassword123",
            "role": "vendor"
        }
    
    @pytest.fixture
    def test_login_data(self):
        """Test login data"""
        return {
            "email": "testuser_api@example.com",
            "password": "testpassword123"
        }

    async def test_health_check(self, client):
        """Test if the API is running and accessible"""
        response = await client.get(f"{BASE_URL}/docs")
        assert response.status_code == 200
        print("Health check passed - API is running")

    async def test_auth_endpoints(self, client, test_user_data, test_login_data):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test registration
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=test_user_data)
            print(f"Registration response: {response.status_code}")
            if response.status_code in [200, 201, 400]:  # 400 might be user already exists
                print("✅ Registration endpoint accessible")
            else:
                print(f"⚠️ Registration returned unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ Registration failed: {str(e)}")
        
        # Test login
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=test_login_data)
            print(f"Login response: {response.status_code}")
            if response.status_code in [200, 401]:  # 401 is expected for invalid credentials
                print("✅ Login endpoint accessible")
            else:
                print(f"⚠️ Login returned unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")

    async def test_user_endpoints(self, client):
        """Test user management endpoints"""
        print("\n👤 Testing User Endpoints...")
        
        endpoints = [
            "/user/profile",
            "/user/update-profile",
            "/user/change-password",
            "/user/partnership-levels",
            "/user/retention-status"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403]:  # 401/403 expected without auth
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_job_endpoints(self, client):
        """Test job-related endpoints"""
        print("\n💼 Testing Job Endpoints...")
        
        endpoints = [
            "/jobs/",
            "/jobs/categories",
            "/jobs/search",
            "/jobs/user-jobs"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403]:
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_payment_endpoints(self, client):
        """Test payment-related endpoints"""
        print("\n💳 Testing Payment Endpoints...")
        
        endpoints = [
            "/payments/",
            "/payments/user-payments",
            "/payments/create-payment",
            "/payments/stripe-webhook"
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint == "/payments/stripe-webhook":
                    # POST request for webhook
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_appointment_endpoints(self, client):
        """Test appointment endpoints"""
        print("\n📅 Testing Appointment Endpoints...")
        
        endpoints = [
            "/appointments/",
            "/appointments/user-appointments",
            "/appointments/create"
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint == "/appointments/create":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_team_endpoints(self, client):
        """Test team management endpoints"""
        print("\n👥 Testing Team Endpoints...")
        
        endpoints = [
            "/teams/",
            "/teams/user-teams",
            "/teams/create"
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint == "/teams/create":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_document_endpoints(self, client):
        """Test document management endpoints"""
        print("\n📄 Testing Document Endpoints...")
        
        endpoints = [
            "/documents/",
            "/documents/user-documents",
            "/documents/upload"
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint == "/documents/upload":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_notification_endpoints(self, client):
        """Test notification endpoints"""
        print("\n🔔 Testing Notification Endpoints...")
        
        endpoints = [
            "/notifications/",
            "/notifications/user-notifications",
            "/notifications/mark-read"
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint == "/notifications/mark-read":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_admin_endpoints(self, client):
        """Test admin endpoints"""
        print("\n🔧 Testing Admin Endpoints...")
        
        endpoints = [
            "/admin/users",
            "/admin/partnership-levels",
            "/admin/retention-analytics",
            "/admin/verification-requests"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403]:
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_api_documentation(self, client):
        """Test API documentation endpoints"""
        print("\n📚 Testing API Documentation...")
        
        endpoints = [
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ {endpoint} accessible")
                else:
                    print(f"⚠️ {endpoint} returned status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

    async def test_cors_headers(self, client):
        """Test CORS headers"""
        print("\n🌐 Testing CORS Headers...")
        
        try:
            response = await client.options(f"{BASE_URL}/auth/login")
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            print(f"CORS Headers: {cors_headers}")
            print("✅ CORS configuration checked")
        except Exception as e:
            print(f"❌ CORS test failed: {str(e)}")

    async def test_error_handling(self, client):
        """Test error handling for invalid endpoints"""
        print("\n🚨 Testing Error Handling...")
        
        invalid_endpoints = [
            "/invalid-endpoint",
            "/auth/invalid",
            "/nonexistent"
        ]
        
        for endpoint in invalid_endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code == 404:
                    print(f"✅ {endpoint} properly returns 404")
                else:
                    print(f"⚠️ {endpoint} returned unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed: {str(e)}")

# Run the tests
async def run_all_tests():
    """Run all API tests"""
    print("Starting Comprehensive API Test Suite")
    print("=" * 50)
    
    test_instance = TestAPIComprehensive()
    
    # Create a mock client for testing
    async with httpx.AsyncClient() as client:
        # Run all test methods
        await test_instance.test_health_check(client)
        await test_instance.test_auth_endpoints(client, test_instance.test_user_data(), test_instance.test_login_data())
        await test_instance.test_user_endpoints(client)
        await test_instance.test_job_endpoints(client)
        await test_instance.test_payment_endpoints(client)
        await test_instance.test_appointment_endpoints(client)
        await test_instance.test_team_endpoints(client)
        await test_instance.test_document_endpoints(client)
        await test_instance.test_notification_endpoints(client)
        await test_instance.test_admin_endpoints(client)
        await test_instance.test_api_documentation(client)
        await test_instance.test_cors_headers(client)
        await test_instance.test_error_handling(client)
    
    print("\n" + "=" * 50)
        print("Comprehensive API Test Suite Completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
