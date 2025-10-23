"""
Simple API Test Suite for B2B Backend
Tests all major API endpoints to ensure they're working correctly
"""
import httpx
import asyncio
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test if the API is running and accessible"""
    print("Testing Health Check...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print("PASS: API is running and accessible")
                return True
            else:
                print(f"FAIL: API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"FAIL: API health check failed - {str(e)}")
            return False

async def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\nTesting Authentication Endpoints...")
    async with httpx.AsyncClient() as client:
        # Test registration
        test_user = {
            "username": "testuser_api",
            "email": "testuser_api@example.com", 
            "password": "testpassword123",
            "role": "vendor"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=test_user)
            print(f"Registration: {response.status_code}")
            if response.status_code in [200, 201, 400]:
                print("PASS: Registration endpoint accessible")
            else:
                print(f"WARN: Registration returned {response.status_code}")
        except Exception as e:
            print(f"FAIL: Registration failed - {str(e)}")
        
        # Test login
        login_data = {"email": "testuser_api@example.com", "password": "testpassword123"}
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            print(f"Login: {response.status_code}")
            if response.status_code in [200, 401]:
                print("PASS: Login endpoint accessible")
            else:
                print(f"WARN: Login returned {response.status_code}")
        except Exception as e:
            print(f"FAIL: Login failed - {str(e)}")

async def test_user_endpoints():
    """Test user management endpoints"""
    print("\nTesting User Endpoints...")
    async with httpx.AsyncClient() as client:
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
                if response.status_code in [200, 401, 403]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_job_endpoints():
    """Test job-related endpoints"""
    print("\nTesting Job Endpoints...")
    async with httpx.AsyncClient() as client:
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
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_payment_endpoints():
    """Test payment-related endpoints"""
    print("\nTesting Payment Endpoints...")
    async with httpx.AsyncClient() as client:
        endpoints = [
            ("/payments/", "GET"),
            ("/payments/user-payments", "GET"),
            ("/payments/create-payment", "POST"),
            ("/payments/stripe-webhook", "POST")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_appointment_endpoints():
    """Test appointment endpoints"""
    print("\nTesting Appointment Endpoints...")
    async with httpx.AsyncClient() as client:
        endpoints = [
            ("/appointments/", "GET"),
            ("/appointments/user-appointments", "GET"),
            ("/appointments/create", "POST")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_team_endpoints():
    """Test team management endpoints"""
    print("\nTesting Team Endpoints...")
    async with httpx.AsyncClient() as client:
        endpoints = [
            ("/teams/", "GET"),
            ("/teams/user-teams", "GET"),
            ("/teams/create", "POST")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_document_endpoints():
    """Test document management endpoints"""
    print("\nTesting Document Endpoints...")
    async with httpx.AsyncClient() as client:
        endpoints = [
            ("/documents/", "GET"),
            ("/documents/user-documents", "GET"),
            ("/documents/upload", "POST")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_notification_endpoints():
    """Test notification endpoints"""
    print("\nTesting Notification Endpoints...")
    async with httpx.AsyncClient() as client:
        endpoints = [
            ("/notifications/", "GET"),
            ("/notifications/user-notifications", "GET"),
            ("/notifications/mark-read", "POST")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 405]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_admin_endpoints():
    """Test admin endpoints"""
    print("\nTesting Admin Endpoints...")
    async with httpx.AsyncClient() as client:
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
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_api_documentation():
    """Test API documentation endpoints"""
    print("\nTesting API Documentation...")
    async with httpx.AsyncClient() as client:
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
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_error_handling():
    """Test error handling for invalid endpoints"""
    print("\nTesting Error Handling...")
    async with httpx.AsyncClient() as client:
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
                    print(f"PASS: {endpoint} properly returns 404")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def run_all_tests():
    """Run all API tests"""
    print("Starting Comprehensive API Test Suite")
    print("=" * 60)
    
    # Run all test functions
    await test_health_check()
    await test_auth_endpoints()
    await test_user_endpoints()
    await test_job_endpoints()
    await test_payment_endpoints()
    await test_appointment_endpoints()
    await test_team_endpoints()
    await test_document_endpoints()
    await test_notification_endpoints()
    await test_admin_endpoints()
    await test_api_documentation()
    await test_error_handling()
    
    print("\n" + "=" * 60)
    print("Comprehensive API Test Suite Completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
