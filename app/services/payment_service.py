from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import Select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment, PaymentType, PaymentStatus, PaymentNotification
from app.models.user import User
from app.models.notification import Notification, NotificationTargetType
from app.models.registration import PartnershipLevel
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    """Service to handle payment monitoring and automated tasks"""
    
    @staticmethod
    async def check_overdue_payments(db: AsyncSession) -> dict:
        """
        Check for overdue payments and send notifications
        
        Args:
            db: Database session
            
        Returns:
            dict: Summary of processed payments
        """
        try:
            # Get all failed monthly payments that are overdue
            result = await db.execute(
                Select(Payment).filter(
                    and_(
                        Payment.payment_type == PaymentType.MONTHLY,
                        Payment.payment_status == PaymentStatus.FAILED,
                        Payment.next_payment_due < datetime.utcnow()
                    )
                )
            )
            overdue_payments = result.scalars().all()
            
            processed_count = 0
            notifications_sent = 0
            deactivations = 0
            
            for payment in overdue_payments:
                days_delinquent = (datetime.utcnow() - payment.next_payment_due).days
                
                # Send notification if not already sent for this period
                notification_sent = await PaymentService._send_payment_notification(payment, days_delinquent, db)
                if notification_sent:
                    notifications_sent += 1
                
                # Deactivate partnership if 30+ days overdue
                if days_delinquent >= 30:
                    deactivated = await PaymentService._deactivate_partnership(payment, db)
                    if deactivated:
                        deactivations += 1
                
                processed_count += 1
            
            await db.commit()
            
            summary = {
                "processed_payments": processed_count,
                "notifications_sent": notifications_sent,
                "deactivations": deactivations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Payment monitoring completed: {summary}")
            return summary
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in payment monitoring: {str(e)}")
            raise
    
    @staticmethod
    async def _send_payment_notification(payment: Payment, days_delinquent: int, db: AsyncSession) -> bool:
        """Send payment notification based on days overdue"""
        try:
            notification_type = None
            message = ""
            
            if days_delinquent >= 7 and days_delinquent < 14:
                notification_type = "7_days"
                message = f"Your {payment.partnership_level.value} partnership payment is overdue by {days_delinquent} days. Pay within {14 - days_delinquent} days to avoid further action."
            elif days_delinquent >= 14 and days_delinquent < 21:
                notification_type = "14_days"
                message = f"Your {payment.partnership_level.value} partnership payment is overdue by {days_delinquent} days. Pay within {21 - days_delinquent} days to avoid deactivation."
            elif days_delinquent >= 21 and days_delinquent < 30:
                notification_type = "21_days"
                message = f"Your {payment.partnership_level.value} partnership will be deactivated in {30 - days_delinquent} days due to non-payment."
            elif days_delinquent >= 30:
                notification_type = "30_days_deactivation"
                message = f"Your {payment.partnership_level.value} partnership has been deactivated due to non-payment after 30 days."
            
            if notification_type:
                # Check if notification already sent for this period
                existing_notification = await db.execute(
                    Select(PaymentNotification).filter(
                        and_(
                            PaymentNotification.payment_id == payment.id,
                            PaymentNotification.notification_type == notification_type
                        )
                    )
                )
                
                if not existing_notification.scalar_one_or_none():
                    # Create notification
                    notification = Notification(
                        admin_id=payment.user_id,
                        message=message,
                        target_type=NotificationTargetType.USER,
                        visibility=True
                    )
                    db.add(notification)
                    
                    # Create payment notification record
                    payment_notification = PaymentNotification(
                        user_id=payment.user_id,
                        payment_id=payment.id,
                        notification_type=notification_type,
                        days_overdue=days_delinquent
                    )
                    db.add(payment_notification)
                    
                    logger.info(f"Payment notification sent: {notification_type} for user_id={payment.user_id}")
                    return True
            
            return False
                
        except Exception as e:
            logger.error(f"Error sending payment notification: {str(e)}")
            return False
    
    @staticmethod
    async def _deactivate_partnership(payment: Payment, db: AsyncSession) -> bool:
        """Deactivate partnership after 30 days of non-payment"""
        try:
            # Get user
            result = await db.execute(Select(User).filter(User.id == payment.user_id))
            user = result.scalar_one_or_none()
            
            if user and user.partnership_level == payment.partnership_level.value:
                # Check if already deactivated
                from app.models.payment import PartnershipDeactivation
                existing_deactivation = await db.execute(
                    Select(PartnershipDeactivation).filter(
                        and_(
                            PartnershipDeactivation.user_id == payment.user_id,
                            PartnershipDeactivation.partnership_level == payment.partnership_level
                        )
                    )
                )
                
                if not existing_deactivation.scalar_one_or_none():
                    # Create deactivation record
                    deactivation = PartnershipDeactivation(
                        user_id=payment.user_id,
                        partnership_level=payment.partnership_level,
                        deactivation_reason="Non-payment after 30 days"
                    )
                    db.add(deactivation)
                    
                    # Revert user to base level
                    user.partnership_level = PartnershipLevel.DROP_SHIPPING.value
                    db.add(user)
                    
                    logger.info(f"Partnership deactivated for user_id={payment.user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deactivating partnership: {str(e)}")
            return False
    
    @staticmethod
    async def get_payment_analytics(db: AsyncSession) -> dict:
        """
        Get comprehensive payment analytics
        
        Args:
            db: Database session
            
        Returns:
            dict: Payment analytics data
        """
        try:
            # Get all payments
            payments_result = await db.execute(Select(Payment))
            all_payments = payments_result.scalars().all()
            
            # Get overdue payments
            overdue_result = await db.execute(
                Select(Payment).filter(
                    and_(
                        Payment.payment_type == PaymentType.MONTHLY,
                        Payment.payment_status == PaymentStatus.FAILED,
                        Payment.next_payment_due < datetime.utcnow()
                    )
                )
            )
            overdue_payments = overdue_result.scalars().all()
            
            # Get deactivated partnerships
            from app.models.payment import PartnershipDeactivation
            deactivated_result = await db.execute(Select(PartnershipDeactivation))
            deactivated_partnerships = deactivated_result.scalars().all()
            
            # Calculate metrics
            total_payments = len(all_payments)
            successful_payments = len([p for p in all_payments if p.payment_status == PaymentStatus.SUCCESS])
            failed_payments = len([p for p in all_payments if p.payment_status == PaymentStatus.FAILED])
            total_revenue = sum(p.amount for p in all_payments if p.payment_status == PaymentStatus.SUCCESS)
            monthly_recurring_revenue = sum(p.amount for p in all_payments if p.payment_type == PaymentType.MONTHLY and p.payment_status == PaymentStatus.SUCCESS)
            overdue_count = len(overdue_payments)
            deactivated_count = len(deactivated_partnerships)
            success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
            
            # Revenue by partnership level
            revenue_by_level = {}
            for payment in all_payments:
                if payment.payment_status == PaymentStatus.SUCCESS:
                    level = payment.partnership_level.value
                    revenue_by_level[level] = revenue_by_level.get(level, 0) + payment.amount
            
            # Payment distribution by type
            lateral_payments = len([p for p in all_payments if p.payment_type == PaymentType.LATERAL])
            monthly_payments = len([p for p in all_payments if p.payment_type == PaymentType.MONTHLY])
            
            return {
                "total_payments": total_payments,
                "successful_payments": successful_payments,
                "failed_payments": failed_payments,
                "total_revenue": total_revenue,
                "monthly_recurring_revenue": monthly_recurring_revenue,
                "overdue_payments": overdue_count,
                "deactivated_partnerships": deactivated_count,
                "payment_success_rate": success_rate,
                "revenue_by_partnership_level": revenue_by_level,
                "payment_distribution": {
                    "lateral_payments": lateral_payments,
                    "monthly_payments": monthly_payments
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting payment analytics: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_payment_summary(user_id: int, db: AsyncSession) -> dict:
        """
        Get payment summary for a specific user
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            dict: User payment summary
        """
        try:
            # Get user payments
            result = await db.execute(
                Select(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc())
            )
            payments = result.scalars().all()
            
            # Get payment notifications
            notifications_result = await db.execute(
                Select(PaymentNotification).filter(PaymentNotification.user_id == user_id).order_by(PaymentNotification.sent_at.desc())
            )
            notifications = notifications_result.scalars().all()
            
            # Calculate summary
            total_payments = len(payments)
            successful_payments = len([p for p in payments if p.payment_status == PaymentStatus.SUCCESS])
            failed_payments = len([p for p in payments if p.payment_status == PaymentStatus.FAILED])
            total_spent = sum(p.amount for p in payments if p.payment_status == PaymentStatus.SUCCESS)
            
            # Active subscriptions
            active_subscriptions = [
                p for p in payments 
                if p.payment_type == PaymentType.MONTHLY and p.payment_status == PaymentStatus.SUCCESS
            ]
            
            # Overdue payments
            overdue_payments = [
                p for p in payments 
                if p.payment_type == PaymentType.MONTHLY 
                and p.payment_status == PaymentStatus.FAILED 
                and p.next_payment_due and p.next_payment_due < datetime.utcnow()
            ]
            
            return {
                "user_id": user_id,
                "total_payments": total_payments,
                "successful_payments": successful_payments,
                "failed_payments": failed_payments,
                "total_spent": total_spent,
                "active_subscriptions": len(active_subscriptions),
                "overdue_payments": len(overdue_payments),
                "recent_notifications": len(notifications),
                "payment_history": payments,
                "notifications": notifications
            }
            
        except Exception as e:
            logger.error(f"Error getting user payment summary: {str(e)}")
            raise
