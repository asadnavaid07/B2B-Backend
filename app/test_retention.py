"""
Test script for the retention tracking system
This script can be run to test the retention functionality
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.retention_service import RetentionService
from app.models.user import User, RegistrationStatus

async def test_retention_calculation():
    """Test the retention calculation logic"""
    print("Testing retention calculation...")
    
    # Test with a mock user
    class MockUser:
        def __init__(self, retention_start_date, retention_period=0):
            self.retention_start_date = retention_start_date
            self.retention_period = retention_period
    
    # Test case 1: User approved 1 month ago
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    user1 = MockUser(one_month_ago)
    months1 = await RetentionService.calculate_retention_months(user1)
    print(f"User approved 1 month ago: {months1} months")
    
    # Test case 2: User approved 3 months ago
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    user2 = MockUser(three_months_ago)
    months2 = await RetentionService.calculate_retention_months(user2)
    print(f"User approved 3 months ago: {months2} months")
    
    # Test case 3: User approved 6 months ago
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    user3 = MockUser(six_months_ago)
    months3 = await RetentionService.calculate_retention_months(user3)
    print(f"User approved 6 months ago: {months3} months")
    
    # Test case 4: User approved today
    today = datetime.utcnow()
    user4 = MockUser(today)
    months4 = await RetentionService.calculate_retention_months(user4)
    print(f"User approved today: {months4} months")
    
    print("Retention calculation test completed!")

async def test_retention_analytics():
    """Test the retention analytics functionality"""
    print("\nTesting retention analytics...")
    
    try:
        async for db in get_db():
            try:
                analytics = await RetentionService.get_retention_analytics(db)
                print(f"Retention Analytics: {analytics}")
            except Exception as e:
                print(f"Error getting analytics: {str(e)}")
            finally:
                await db.close()
            break
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

async def test_eligible_users():
    """Test getting users eligible for partnership upgrades"""
    print("\nTesting eligible users for upgrades...")
    
    try:
        async for db in get_db():
            try:
                eligible_users = await RetentionService.get_users_eligible_for_partnership_upgrade(db)
                print(f"Found {len(eligible_users)} users eligible for partnership upgrades")
                for item in eligible_users[:3]:  # Show first 3
                    print(f"  - User {item['user'].email}: {item['current_retention']} months (requires {item['required_retention']})")
            except Exception as e:
                print(f"Error getting eligible users: {str(e)}")
            finally:
                await db.close()
            break
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

async def main():
    """Run all tests"""
    print("=== Retention System Test ===")
    
    await test_retention_calculation()
    await test_retention_analytics()
    await test_eligible_users()
    
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    asyncio.run(main())
