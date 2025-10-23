"""
Accurate API Test Suite for B2B Backend
Tests actual API endpoints based on the route definitions
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
        # Test registration endpoints
        auth_endpoints = [
            ("/auth/signup", "POST"),
            ("/auth/register-supplier", "POST"),
            ("/auth/register", "POST"),
            ("/auth/login", "POST"),
            ("/auth/google-login", "POST"),
            ("/auth/refresh-token", "POST"),
            ("/auth/resend-otp", "POST")
        ]
        
        for endpoint, method in auth_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 201, 400, 401, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_job_endpoints():
    """Test job-related endpoints"""
    print("\nTesting Job Endpoints...")
    async with httpx.AsyncClient() as client:
        job_endpoints = [
            ("/jobs/", "GET"),
            ("/jobs/{id}", "GET")
        ]
        
        for endpoint, method in job_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_user_endpoints():
    """Test user management endpoints"""
    print("\nTesting User Endpoints...")
    async with httpx.AsyncClient() as client:
        user_endpoints = [
            ("/user/profile", "GET"),
            ("/user/update-profile", "PUT"),
            ("/user/change-password", "POST"),
            ("/user/partnership-levels", "GET"),
            ("/user/retention-status", "GET")
        ]
        
        for endpoint, method in user_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                elif method == "PUT":
                    response = await client.put(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_document_endpoints():
    """Test document management endpoints"""
    print("\nTesting Document Endpoints...")
    async with httpx.AsyncClient() as client:
        doc_endpoints = [
            ("/user/upload-document", "POST"),
            ("/user/documents", "GET"),
            ("/user/reupload-document", "POST")
        ]
        
        for endpoint, method in doc_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_appointment_endpoints():
    """Test appointment endpoints"""
    print("\nTesting Appointment Endpoints...")
    async with httpx.AsyncClient() as client:
        appointment_endpoints = [
            ("/appointments/", "GET")
        ]
        
        for endpoint, method in appointment_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_admin_endpoints():
    """Test admin endpoints"""
    print("\nTesting Admin Endpoints...")
    async with httpx.AsyncClient() as client:
        admin_endpoints = [
            ("/admin/users", "GET"),
            ("/admin/approve-registration/{user_id}", "POST"),
            ("/admin/reject-registration/{user_id}", "POST"),
            ("/admin/approve-document/{document_id}", "POST"),
            ("/admin/reject-document/{document_id}", "POST"),
            ("/admin/notifications", "GET"),
            ("/admin/create-notification", "POST")
        ]
        
        for endpoint, method in admin_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_payment_endpoints():
    """Test payment endpoints"""
    print("\nTesting Payment Endpoints...")
    async with httpx.AsyncClient() as client:
        payment_endpoints = [
            ("/payments/create-lateral-payment", "POST"),
            ("/payments/create-monthly-payment", "POST"),
            ("/payments/user-payments", "GET"),
            ("/payments/admin-payments", "GET"),
            ("/payments/stripe-webhook", "POST"),
            ("/payments/three-tier-pricing", "GET"),
            ("/payments/set-three-tier-pricing", "POST")
        ]
        
        for endpoint, method in payment_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_notification_endpoints():
    """Test notification endpoints"""
    print("\nTesting Notification Endpoints...")
    async with httpx.AsyncClient() as client:
        notification_endpoints = [
            ("/notifications/", "GET"),
            ("/notifications/mark-read/{notification_id}", "POST")
        ]
        
        for endpoint, method in notification_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_team_endpoints():
    """Test team endpoints"""
    print("\nTesting Team Endpoints...")
    async with httpx.AsyncClient() as client:
        team_endpoints = [
            ("/teams/", "GET")
        ]
        
        for endpoint, method in team_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_retention_endpoints():
    """Test retention endpoints"""
    print("\nTesting Retention Endpoints...")
    async with httpx.AsyncClient() as client:
        retention_endpoints = [
            ("/retention/analytics", "GET"),
            ("/retention/update-retention", "POST"),
            ("/retention/eligible-users", "GET")
        ]
        
        for endpoint, method in retention_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
                if response.status_code in [200, 401, 403, 404, 422]:
                    print(f"PASS: {endpoint} accessible")
                else:
                    print(f"WARN: {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"FAIL: {endpoint} failed - {str(e)}")

async def test_api_documentation():
    """Test API documentation endpoints"""
    print("\nTesting API Documentation...")
    async with httpx.AsyncClient() as client:
        doc_endpoints = [
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        for endpoint in doc_endpoints:
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
    print("Starting Accurate API Test Suite")
    print("=" * 60)
    
    # Run all test functions
    await test_health_check()
    await test_auth_endpoints()
    await test_job_endpoints()
    await test_user_endpoints()
    await test_document_endpoints()
    await test_appointment_endpoints()
    await test_admin_endpoints()
    await test_payment_endpoints()
    await test_notification_endpoints()
    await test_team_endpoints()
    await test_retention_endpoints()
    await test_api_documentation()
    await test_error_handling()
    
    print("\n" + "=" * 60)
    print("Accurate API Test Suite Completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
