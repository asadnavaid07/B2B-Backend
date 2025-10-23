import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.core.database import get_db
from app.core.config import settings
from app.models.payment import Payment, PaymentType, PaymentStatus, PaymentPlan, PaymentNotification, PartnershipDeactivation
from app.models.partnership_pricing import PartnershipLevelModel
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse, UserRole
from app.schema.payment import (
    PaymentRequest, PaymentResponse, SubscriptionResponse, PaymentWebhook,
    PaymentHistoryResponse, PaymentNotificationResponse, PartnershipDeactivationResponse,
    PaymentAnalyticsResponse
)
from app.models.user import User
from app.models.notification import Notification, NotificationTargetType
from app.models.registration import PartnershipLevel
from datetime import datetime, timedelta
from app.utils.partnership_levels import partnership_level
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
payments_router = APIRouter(prefix="/payments", tags=["payments"])

stripe.api_key = settings.STRIPE_SECRET_KEY

partnership_levels = partnership_level

async def get_admin_role(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@payments_router.post("/lateral", response_model=PaymentResponse)
async def create_lateral_payment(
    request: PaymentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        level_enum = request.partnership_level
        
        # Check if lateral entry is allowed for this partnership level
        if level_enum == PartnershipLevel.DROP_SHIPPING:
            raise HTTPException(status_code=400, detail="No lateral entry available for DROP_SHIPPING")
        
        # Last three partnership levels don't allow lateral entry
        last_three_levels = [
            PartnershipLevel.MUSEUM_INSTITUTIONAL,
            PartnershipLevel.NGO_GOVERNMENT, 
            PartnershipLevel.TECHNOLOGY_PARTNERSHIP
        ]
        if level_enum in last_three_levels:
            raise HTTPException(status_code=400, detail="No lateral entry available for the last three partnership levels")

        # Check if user already has a lateral payment for this partnership level
        existing_payment = await db.execute(
            select(Payment).filter(
                and_(
                    Payment.user_id == current_user.id,
                    Payment.partnership_level == level_enum,  # Use enum directly
                    Payment.payment_type == PaymentType.LATERAL,
                    Payment.payment_status == PaymentStatus.SUCCESS
                )
            )
        )
        if existing_payment.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Lateral entry payment already completed for this partnership level")

        result = await db.execute(
            select(PartnershipLevelModel).filter(PartnershipLevelModel.partnership_name == level_enum)
        )
        level = result.scalar_one_or_none()
        if not level:
            raise HTTPException(status_code=404, detail="Partnership level not found")
        
        price = level.prices.get(request.plan.value)
        if price is None:
            raise HTTPException(status_code=400, detail="Invalid plan for this partnership level")
        
        amount = int(float(price) * 100)  # Convert to cents
        
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            payment_method_types=["card"],
            metadata={
                "user_id": str(current_user.id), 
                "partnership_level": level_enum.value, 
                "plan": request.plan.value, 
                "type": "lateral"
            }
        )
        
        new_payment = Payment(
            user_id=current_user.id,
            partnership_level=level_enum,  # Use enum directly
            plan=request.plan,  # Use enum directly
            amount=float(price),
            payment_type=PaymentType.LATERAL,
            stripe_payment_id=intent.id
        )
        db.add(new_payment)
        await db.commit()
        
        return PaymentResponse(
            payment_intent_id=intent.id,
            client_secret=intent.client_secret,
            amount=float(price),
            status="pending"
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except Exception as e:
        logger.error(f"Error creating lateral payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create lateral payment: {str(e)}")

@payments_router.post("/monthly", response_model=SubscriptionResponse)
async def create_monthly_subscription(
    request: PaymentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        level_enum = request.partnership_level
        
        # Check if user already has an active monthly subscription for this partnership level
        existing_subscription = await db.execute(
            select(Payment).filter(
                and_(
                    Payment.user_id == current_user.id,
                    Payment.partnership_level == level_enum,  # Use enum directly
                    Payment.payment_type == PaymentType.MONTHLY,
                    Payment.payment_status == PaymentStatus.SUCCESS
                )
            )
        )
        if existing_subscription.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Monthly subscription already exists for this partnership level")

        result = await db.execute(
            select(PartnershipLevelModel).filter(PartnershipLevelModel.partnership_name == level_enum)
        )
        level = result.scalar_one_or_none()
        if not level:
            raise HTTPException(status_code=404, detail="Partnership level not found")
        
        price = level.prices.get(request.plan.value)
        if price is None:
            raise HTTPException(status_code=400, detail="Invalid plan for this partnership level")
        
        amount = int(float(price) * 100)  # Convert to cents
        
        # Create or get existing Stripe customer
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": str(current_user.id)}
        )
        
        product = stripe.Product.create(
            name=f"{level_enum.value} - {request.plan.value}",
            type="service"
        )
        
        stripe_price = stripe.Price.create(
            unit_amount=amount,
            currency="usd",
            recurring={"interval": "month"},
            product=product.id,
        )
        
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": stripe_price.id}],
            metadata={
                "user_id": str(current_user.id), 
                "partnership_level": level_enum.value, 
                "plan": request.plan.value, 
                "type": "monthly"
            }
        )
        
        next_due = datetime.utcnow() + timedelta(days=30)
        new_payment = Payment(
            user_id=current_user.id,
            partnership_level=level_enum,  # Use enum directly
            plan=request.plan,  # Use enum directly
            amount=float(price),
            payment_type=PaymentType.MONTHLY,
            stripe_payment_id=subscription.id,
            stripe_customer_id=customer.id,
            next_payment_due=next_due
        )
        db.add(new_payment)
        await db.commit()
        
        return SubscriptionResponse(
            subscription_id=subscription.id,
            client_secret=subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None,
            amount=float(price),
            next_payment_due=next_due
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except Exception as e:
        logger.error(f"Error creating monthly subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create monthly subscription: {str(e)}")

@payments_router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        event = stripe.Event.construct_from(payload, stripe.api_key)
        
        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            metadata = payment_intent.metadata
            if metadata.get("type") == "lateral":
                result = await db.execute(
                    select(Payment).filter(Payment.stripe_payment_id == payment_intent.id)
                )
                payment = result.scalar_one_or_none()
                if payment:
                    payment.payment_status = PaymentStatus.SUCCESS
                    db.add(payment)
                    await db.commit()
                    logger.info(f"Lateral payment succeeded for user_id={metadata.get('user_id')}")
                    
        elif event.type == "invoice.paid":
            subscription = event.data.object.subscription
            result = await db.execute(
                select(Payment).filter(Payment.stripe_payment_id == subscription)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.payment_status = PaymentStatus.SUCCESS
                payment.next_payment_due = datetime.utcnow() + timedelta(days=30)
                db.add(payment)
                await db.commit()
                logger.info(f"Monthly payment succeeded for subscription={subscription}")
                
        elif event.type == "invoice.payment_failed":
            subscription = event.data.object.subscription
            result = await db.execute(
                select(Payment).filter(Payment.stripe_payment_id == subscription)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.payment_status = PaymentStatus.FAILED
                payment.failure_reason = "Payment failed via Stripe webhook"
                db.add(payment)
                
                # Calculate days overdue
                days_delinquent = (datetime.utcnow() - payment.next_payment_due).days if payment.next_payment_due else 0
                
                # Send notifications based on days overdue
                await send_payment_notification(payment, days_delinquent, db)
                
                # Deactivate partnership after 30 days
                if days_delinquent >= 30:
                    await deactivate_partnership(payment, db)
                
                await db.commit()
                logger.warning(f"Monthly payment failed for subscription={subscription}")
        else:
            logger.warning(f"Unhandled webhook event type: {event.type}")
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def send_payment_notification(payment: Payment, days_delinquent: int, db: AsyncSession):
    """Send payment notifications based on days overdue"""
    try:
        # Check if notification already sent for this period
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
            # Check if notification already sent
            existing_notification = await db.execute(
                select(PaymentNotification).filter(
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
                
    except Exception as e:
        logger.error(f"Error sending payment notification: {str(e)}")

async def deactivate_partnership(payment: Payment, db: AsyncSession):
    """Deactivate partnership after 30 days of non-payment"""
    try:
        # Get user
        result = await db.execute(select(User).filter(User.id == payment.user_id))
        user = result.scalar_one_or_none()
        
        if user and user.partnership_level == payment.partnership_level:
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
            
    except Exception as e:
        logger.error(f"Error deactivating partnership: {str(e)}")

# Additional endpoints for payment management

@payments_router.get("/history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment history for current user"""
    try:
        result = await db.execute(
            select(Payment).filter(Payment.user_id == current_user.id).order_by(Payment.created_at.desc())
        )
        payments = result.scalars().all()
        return payments
    except Exception as e:
        logger.error(f"Error fetching payment history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch payment history: {str(e)}")

@payments_router.get("/notifications", response_model=List[PaymentNotificationResponse])
async def get_payment_notifications(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment notifications for current user"""
    try:
        result = await db.execute(
            select(PaymentNotification).filter(PaymentNotification.user_id == current_user.id).order_by(PaymentNotification.sent_at.desc())
        )
        notifications = result.scalars().all()
        return notifications
    except Exception as e:
        logger.error(f"Error fetching payment notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch payment notifications: {str(e)}")

@payments_router.get("/analytics", response_model=PaymentAnalyticsResponse)
async def get_payment_analytics(
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get payment analytics for admin"""
    try:
        # Get all payments
        payments_result = await db.execute(select(Payment))
        all_payments = payments_result.scalars().all()
        
        # Get overdue payments
        overdue_result = await db.execute(
            select(Payment).filter(
                and_(
                    Payment.payment_type == PaymentType.MONTHLY,
                    Payment.payment_status == PaymentStatus.FAILED,
                    Payment.next_payment_due < datetime.utcnow()
                )
            )
        )
        overdue_payments = overdue_result.scalars().all()
        
        # Get deactivated partnerships
        deactivated_result = await db.execute(select(PartnershipDeactivation))
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
        
        return PaymentAnalyticsResponse(
            total_payments=total_payments,
            successful_payments=successful_payments,
            failed_payments=failed_payments,
            total_revenue=total_revenue,
            monthly_recurring_revenue=monthly_recurring_revenue,
            overdue_payments=overdue_count,
            deactivated_partnerships=deactivated_count,
            payment_success_rate=success_rate
        )
    except Exception as e:
        logger.error(f"Error fetching payment analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch payment analytics: {str(e)}")

# Pricing endpoints removed - use /partnership-levels/ instead
# GET /partnership-levels/ - Get all partnership levels with pricing
# POST /partnership-levels/ - Create new partnership level with pricing  
# PUT /partnership-levels/{id} - Update partnership level pricing

@payments_router.get("/pricing/{partnership_level}", response_model=dict)
async def get_payment_pricing(
    partnership_level: PartnershipLevel,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pricing information for a specific partnership level"""
    try:
        result = await db.execute(
            select(PartnershipLevelModel).filter(PartnershipLevelModel.partnership_name == partnership_level)
        )
        level = result.scalar_one_or_none()
        if not level:
            raise HTTPException(status_code=404, detail="Partnership level not found")
        
        return {
            "partnership_level": partnership_level.value,
            "pricing": level.prices,
            "available_plans": list(level.prices.keys()),
            "currency": "USD"
        }
    except Exception as e:
        logger.error(f"Error fetching pricing for {partnership_level.value}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pricing: {str(e)}")

@payments_router.get("/pricing", response_model=List[dict])
async def get_all_payment_pricing(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pricing information for all partnership levels"""
    try:
        result = await db.execute(select(PartnershipLevelModel))
        levels = result.scalars().all()
        
        pricing_info = []
        for level in levels:
            pricing_info.append({
                "partnership_level": level.partnership_name,
                "pricing": level.prices,
                "available_plans": list(level.prices.keys()),
                "currency": "USD"
            })
        
        return pricing_info
    except Exception as e:
        logger.error(f"Error fetching all pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pricing: {str(e)}")

@payments_router.post("/check-overdue", status_code=status.HTTP_200_OK)
async def check_overdue_payments(
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Manually check for overdue payments and send notifications (Admin only)"""
    try:
        # Get all failed monthly payments
        result = await db.execute(
            select(Payment).filter(
                and_(
                    Payment.payment_type == PaymentType.MONTHLY,
                    Payment.payment_status == PaymentStatus.FAILED,
                    Payment.next_payment_due < datetime.utcnow()
                )
            )
        )
        overdue_payments = result.scalars().all()
        
        processed_count = 0
        for payment in overdue_payments:
            days_delinquent = (datetime.utcnow() - payment.next_payment_due).days
            await send_payment_notification(payment, days_delinquent, db)
            
            # Deactivate if 30+ days overdue
            if days_delinquent >= 30:
                await deactivate_partnership(payment, db)
            
            processed_count += 1
        
        await db.commit()
        
        return {
            "message": f"Processed {processed_count} overdue payments",
            "processed_count": processed_count
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error checking overdue payments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check overdue payments: {str(e)}")

@payments_router.get("/deactivations", response_model=List[PartnershipDeactivationResponse])
async def get_partnership_deactivations(
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get all partnership deactivations (Admin only)"""
    try:
        result = await db.execute(
            select(PartnershipDeactivation).order_by(PartnershipDeactivation.deactivated_at.desc())
        )
        deactivations = result.scalars().all()
        return deactivations
    except Exception as e:
        logger.error(f"Error fetching deactivations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch deactivations: {str(e)}")