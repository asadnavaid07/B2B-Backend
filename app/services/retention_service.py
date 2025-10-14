from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import Select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, RegistrationStatus
from app.models.registration import RegistrationLevel
import logging

logger = logging.getLogger(__name__)

class RetentionService:
    """Service to handle user retention tracking and calculations"""
    
    @staticmethod
    async def calculate_retention_months(user: User) -> int:
        """
        Calculate the number of months since user registration was approved
        
        Args:
            user: User object with retention_start_date
            
        Returns:
            int: Number of months since approval
        """
        if not user.retention_start_date:
            return 0
            
        now = datetime.utcnow()
        start_date = user.retention_start_date
        
        # Calculate the difference in months
        months = (now.year - start_date.year) * 12 + (now.month - start_date.month)
        
        # If the day of month is less than the start day, subtract 1 month
        if now.day < start_date.day:
            months -= 1
            
        return max(0, months)
    
    @staticmethod
    async def update_user_retention_period(user_id: int, db: AsyncSession) -> Optional[int]:
        """
        Update the retention period for a specific user
        
        Args:
            user_id: ID of the user to update
            db: Database session
            
        Returns:
            int: Updated retention period in months, or None if user not found
        """
        try:
            result = await db.execute(
                Select(User).filter(
                    and_(
                        User.id == user_id,
                        User.is_registered == RegistrationStatus.APPROVED,
                        User.retention_start_date.isnot(None)
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User {user_id} not found or not approved for retention tracking")
                return None
                
            new_retention_period = await RetentionService.calculate_retention_months(user)
            
            if new_retention_period != user.retention_period:
                user.retention_period = new_retention_period
                user.updated_at = datetime.utcnow()
                db.add(user)
                await db.commit()
                
                logger.info(f"Updated retention period for user {user.email} to {new_retention_period} months")
                return new_retention_period
            else:
                logger.debug(f"Retention period for user {user.email} unchanged: {new_retention_period} months")
                return new_retention_period
                
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating retention period for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    async def update_all_users_retention_periods(db: AsyncSession) -> dict:
        """
        Update retention periods for all approved users
        
        Args:
            db: Database session
            
        Returns:
            dict: Summary of updates performed
        """
        try:
            # Get all approved users with retention start dates
            result = await db.execute(
                Select(User).filter(
                    and_(
                        User.is_registered == RegistrationStatus.APPROVED,
                        User.retention_start_date.isnot(None)
                    )
                )
            )
            users = result.scalars().all()
            
            updated_count = 0
            unchanged_count = 0
            errors = []
            
            for user in users:
                try:
                    new_retention_period = await RetentionService.calculate_retention_months(user)
                    
                    if new_retention_period != user.retention_period:
                        user.retention_period = new_retention_period
                        user.updated_at = datetime.utcnow()
                        db.add(user)
                        updated_count += 1
                        logger.info(f"Updated retention period for user {user.email} to {new_retention_period} months")
                    else:
                        unchanged_count += 1
                        
                except Exception as e:
                    error_msg = f"Error updating user {user.id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            await db.commit()
            
            summary = {
                "total_users_processed": len(users),
                "updated_count": updated_count,
                "unchanged_count": unchanged_count,
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Retention period update completed: {summary}")
            return summary
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in bulk retention period update: {str(e)}")
            raise
    
    @staticmethod
    async def get_users_eligible_for_partnership_upgrade(db: AsyncSession) -> List[User]:
        """
        Get users who are eligible for partnership level upgrades based on retention period
        
        Args:
            db: Database session
            
        Returns:
            List[User]: Users eligible for partnership upgrades
        """
        try:
            # Get all approved users with their registration levels
            result = await db.execute(
                Select(User).filter(
                    and_(
                        User.is_registered == RegistrationStatus.APPROVED,
                        User.retention_start_date.isnot(None)
                    )
                )
            )
            users = result.scalars().all()
            
            eligible_users = []
            
            for user in users:
                # Get user's registration levels
                levels_result = await db.execute(
                    Select(RegistrationLevel).filter(RegistrationLevel.user_id == user.id)
                )
                user_levels = levels_result.scalars().all()
                
                for level in user_levels:
                    # Check if user meets retention requirement for this level
                    if user.retention_period >= level.retention_period_months:
                        eligible_users.append({
                            "user": user,
                            "level": level,
                            "current_retention": user.retention_period,
                            "required_retention": level.retention_period_months
                        })
            
            return eligible_users
            
        except Exception as e:
            logger.error(f"Error getting users eligible for partnership upgrade: {str(e)}")
            raise
    
    @staticmethod
    async def get_retention_analytics(db: AsyncSession) -> dict:
        """
        Get analytics about user retention periods
        
        Args:
            db: Database session
            
        Returns:
            dict: Retention analytics data
        """
        try:
            # Get all approved users
            result = await db.execute(
                Select(User).filter(
                    and_(
                        User.is_registered == RegistrationStatus.APPROVED,
                        User.retention_start_date.isnot(None)
                    )
                )
            )
            users = result.scalars().all()
            
            if not users:
                return {
                    "total_users": 0,
                    "average_retention": 0,
                    "retention_distribution": {},
                    "users_by_partnership_level": {}
                }
            
            retention_periods = [user.retention_period for user in users]
            average_retention = sum(retention_periods) / len(retention_periods)
            
            # Distribution of retention periods
            retention_distribution = {}
            for period in retention_periods:
                retention_distribution[period] = retention_distribution.get(period, 0) + 1
            
            # Users by partnership level
            users_by_level = {}
            for user in users:
                level = user.partnership_level or "UNKNOWN"
                users_by_level[level] = users_by_level.get(level, 0) + 1
            
            return {
                "total_users": len(users),
                "average_retention": round(average_retention, 2),
                "retention_distribution": retention_distribution,
                "users_by_partnership_level": users_by_level,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting retention analytics: {str(e)}")
            raise
