import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.core.database import get_db
from app.core.config import settings
from app.models.payment import Payment, PaymentType, PaymentStatus, PaymentPlan, PaymentNotification, PartnershipDeactivation
from app.models.partnership_pricing import PartnershipLevelModel
from app.models.partnership_fees import PartnershipFees, PartnershipLevelGroup
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
from app.utils.partnership_level_mapping import (
    get_partnership_level_group, are_in_same_level, is_upward_movement,
    get_level_number
)
from app.utils.lateral_access_rules import can_switch_laterally as validate_lateral_switch
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)
payments_router = APIRouter(prefix="/payments", tags=["payments"])

stripe.api_key = settings.STRIPE_SECRET_KEY

async def get_admin_role(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def get_user_active_partnerships(user: User) -> List[PartnershipLevel]:
    """Get list of active partnerships from user's partnership_level JSON array"""
    if user.partnership_level is None:
        return [PartnershipLevel.DROP_SHIPPING]
    if isinstance(user.partnership_level, list):
        return [PartnershipLevel(p) if isinstance(p, str) else p for p in user.partnership_level]
    if isinstance(user.partnership_level, str):
        return [PartnershipLevel(user.partnership_level)]
    return [PartnershipLevel.DROP_SHIPPING]

def add_partnership_to_user(user: User, partnership: PartnershipLevel):
    """Add a partnership to user's active partnerships array"""
    current = get_user_active_partnerships(user)
    if partnership not in current:
        current.append(partnership)
    user.partnership_level = [p.value for p in current]

@payments_router.post("/monthly", response_model=SubscriptionResponse)
async def create_monthly_subscription(
    request: PaymentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create monthly recurring subscription for a partnership.
    Each partnership has 3 tiers: 1st, 2nd, 3rd
    """
    try:
        # Get user from database
        result = await db.execute(select(User).filter(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        partnership = request.partnership_level
        
        # Check if user already has an active monthly subscription for this partnership
        existing_subscription = await db.execute(
            select(Payment).filter(
                and_(
                    Payment.user_id == current_user.id,
                    Payment.partnership_level == partnership,
                    Payment.payment_type == PaymentType.MONTHLY,
                    Payment.payment_status == PaymentStatus.SUCCESS
                )
            )
        )
        if existing_subscription.scalar_one_or_none():
            raise HTTPException(
                status_code=400, 
                detail=f"Monthly subscription already exists for {partnership.value}"
            )

        # Get pricing for this partnership
        result = await db.execute(
            select(PartnershipLevelModel).filter(PartnershipLevelModel.partnership_name == partnership)
        )
        level = result.scalar_one_or_none()
        if not level:
            raise HTTPException(status_code=404, detail=f"Pricing not found for {partnership.value}")
        
        # Get price for the selected tier (1st, 2nd, or 3rd)
        price_key = request.plan.value  # "1st", "2nd", or "3rd"
        price = level.prices.get(price_key)
        if price is None:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid plan {price_key} for partnership {partnership.value}"
            )
        
        amount = int(float(price) * 100)  # Convert to cents
        
        # Create or get existing Stripe customer
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": str(current_user.id)}
        )
        
        product = stripe.Product.create(
            name=f"{partnership.value} - {price_key} tier",
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
                "partnership_level": partnership.value, 
                "plan": price_key, 
                "type": "monthly"
            }
        )
        
        next_due = datetime.utcnow() + timedelta(days=30)
        new_payment = Payment(
            user_id=current_user.id,
            partnership_level=partnership,
            plan=request.plan,
            amount=float(price),
            payment_type=PaymentType.MONTHLY,
            stripe_payment_id=subscription.id,
            stripe_customer_id=customer.id,
            next_payment_due=next_due
        )
        db.add(new_payment)
        # Note: Partnership will be added to user's array when invoice.paid webhook is received
        await db.commit()
        
        return SubscriptionResponse(
            subscription_id=subscription.id,
            client_secret=subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None,
            amount=float(price),
            next_payment_due=next_due
        )
    except stripe.error.StripeError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating monthly subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create monthly subscription: {str(e)}")

@payments_router.post("/lateral", response_model=PaymentResponse)
async def create_lateral_payment(
    request: PaymentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create lateral payment for switching between partnerships in the same level.
    
    LOOSE VALIDATION: Users can switch to any partnership in the same level.
    The 'plan' field represents the lateral tier (1st, 2nd, or 3rd) used for fee calculation.
    No restrictions on which specific partnership they can move to within the same level.
    
    Requires from_partnership to be specified.
    """
    try:
        if not request.from_partnership:
            raise HTTPException(status_code=400, detail="from_partnership is required for lateral payments")
        
        # Get user from database
        result = await db.execute(select(User).filter(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        from_partnership = request.from_partnership
        to_partnership = request.partnership_level
        
        # Check if user has the from_partnership active
        active_partnerships = get_user_active_partnerships(user)
        if from_partnership not in active_partnerships:
            raise HTTPException(
                status_code=400,
                detail=f"You must have {from_partnership.value} active to switch laterally"
            )
        
        # Check if user already has the to_partnership active
        if to_partnership in active_partnerships:
            raise HTTPException(
                status_code=400,
                detail=f"You already have {to_partnership.value} active"
            )
        
        # Check if both partnerships are in the same level
        if not are_in_same_level(from_partnership, to_partnership):
            raise HTTPException(
                status_code=400,
                detail="Lateral payment only allowed for partnerships in the same level"
            )
        
        # Validate lateral movement: Only checks if both partnerships are in the same level
        # No restriction on which specific partnership they can move to
        can_switch, error_message = validate_lateral_switch(
            from_partnership,
            to_partnership,
            request.plan  # This is the lateral tier (1st, 2nd, or 3rd) - used for fee calculation only
        )
        if not can_switch:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Get lateral fee for this level and tier
        level_group = get_partnership_level_group(to_partnership)
        result = await db.execute(
            select(PartnershipFees).filter(PartnershipFees.level_group == level_group)
        )
        fees = result.scalar_one_or_none()
        if not fees:
            raise HTTPException(
                status_code=404, 
                detail=f"Lateral fees not configured for level {level_group.value}"
            )
        
        # Get the lateral fee for the specific tier (1st, 2nd, or 3rd)
        tier_key = request.plan.value  # "1st", "2nd", or "3rd"
        lateral_fee = fees.lateral_fees.get(tier_key)
        if lateral_fee is None:
            raise HTTPException(
                status_code=400,
                detail=f"Lateral fee for tier {tier_key} not configured for level {level_group.value}"
            )
        
        amount = int(float(lateral_fee) * 100)  # Convert to cents
        
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            payment_method_types=["card"],
            metadata={
                "user_id": str(current_user.id), 
                "from_partnership": from_partnership.value,
                "to_partnership": to_partnership.value, 
                "type": "lateral"
            }
        )
        
        new_payment = Payment(
            user_id=current_user.id,
            partnership_level=to_partnership,
            plan=request.plan,  # Lateral tier (1st, 2nd, or 3rd)
            amount=float(lateral_fee),
            payment_type=PaymentType.LATERAL,
            stripe_payment_id=intent.id
        )
        db.add(new_payment)
        await db.commit()
        
        return PaymentResponse(
            payment_intent_id=intent.id,
            client_secret=intent.client_secret,
            amount=float(lateral_fee),
            status="pending"
        )
    except stripe.error.StripeError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating lateral payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create lateral payment: {str(e)}")

@payments_router.post("/registration", response_model=PaymentResponse)
async def create_registration_payment(
    request: PaymentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create registration payment for moving from a lower level to a higher level.
    Requires from_partnership to be specified.
    Registration fees are only for: Level 1→2, Level 2→3, Level 3→4
    """
    try:
        if not request.from_partnership:
            raise HTTPException(status_code=400, detail="from_partnership is required for registration payments")
        
        # Get user from database
        result = await db.execute(select(User).filter(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        from_partnership = request.from_partnership
        to_partnership = request.partnership_level
        
        # Check if this is an upward movement
        if not is_upward_movement(from_partnership, to_partnership):
            raise HTTPException(
                status_code=400, 
                detail="Registration payment only allowed for upward movement to higher level"
            )
        
        # Check if user has the from_partnership active
        active_partnerships = get_user_active_partnerships(user)
        if from_partnership not in active_partnerships:
            raise HTTPException(
                status_code=400,
                detail=f"You must have {from_partnership.value} active to upgrade"
            )
        
        # Check if user already has the to_partnership active
        if to_partnership in active_partnerships:
            raise HTTPException(
                status_code=400,
                detail=f"You already have {to_partnership.value} active"
            )
        
        # Get registration fee for the target level
        to_level_group = get_partnership_level_group(to_partnership)
        result = await db.execute(
            select(PartnershipFees).filter(PartnershipFees.level_group == to_level_group)
        )
        fees = result.scalar_one_or_none()
        if not fees:
            raise HTTPException(
                status_code=404, 
                detail=f"Registration fee not configured for level {to_level_group.value}"
            )
        
        amount = int(float(fees.registration_fee) * 100)  # Convert to cents
        
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            payment_method_types=["card"],
            metadata={
                "user_id": str(current_user.id), 
                "from_partnership": from_partnership.value,
                "to_partnership": to_partnership.value, 
                "type": "registration"
            }
        )
        
        new_payment = Payment(
            user_id=current_user.id,
            partnership_level=to_partnership,
            plan=PaymentPlan.FIRST,  # Not applicable for registration, but required field
            amount=float(fees.registration_fee),
            payment_type=PaymentType.REGISTRATION,
            stripe_payment_id=intent.id
        )
        db.add(new_payment)
        await db.commit()
        
        return PaymentResponse(
            payment_intent_id=intent.id,
            client_secret=intent.client_secret,
            amount=float(fees.registration_fee),
            status="pending"
        )
    except stripe.error.StripeError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating registration payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create registration payment: {str(e)}")

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
            payment_type = metadata.get("type")
            
            result = await db.execute(
                select(Payment).filter(Payment.stripe_payment_id == payment_intent.id)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.payment_status = PaymentStatus.SUCCESS
                
                # Get user and update their active partnerships
                user_result = await db.execute(select(User).filter(User.id == payment.user_id))
                user = user_result.scalar_one_or_none()
                
                if user and payment_type in ["lateral", "registration"]:
                    # Add the new partnership to user's active partnerships
                    add_partnership_to_user(user, payment.partnership_level)
                    db.add(user)
                
                db.add(payment)
                await db.commit()
                logger.info(f"{payment_type} payment succeeded for user_id={metadata.get('user_id')}")
                
        elif event.type == "invoice.paid":
            subscription = event.data.object.subscription
            result = await db.execute(
                select(Payment).filter(Payment.stripe_payment_id == subscription)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.payment_status = PaymentStatus.SUCCESS
                payment.next_payment_due = datetime.utcnow() + timedelta(days=30)
                
                # Get user and add partnership to active partnerships array
                user_result = await db.execute(select(User).filter(User.id == payment.user_id))
                user = user_result.scalar_one_or_none()
                
                if user:
                    # Add the partnership to user's active partnerships if not already present
                    add_partnership_to_user(user, payment.partnership_level)
                    db.add(user)
                
                db.add(payment)
                await db.commit()
                logger.info(f"Monthly payment succeeded for subscription={subscription}, partnership {payment.partnership_level.value} added to user {payment.user_id}")
                
        elif event.type == "invoice.payment_failed":
            subscription = event.data.object.subscription
            result = await db.execute(
                select(Payment).filter(Payment.stripe_payment_id == subscription)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.payment_status = PaymentStatus.FAILED
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
                    days_overdue=days_delinquent,
                    message=message
                )
                db.add(payment_notification)
                
                logger.info(f"Payment notification sent: {notification_type} for user_id={payment.user_id}")
                
    except Exception as e:
        logger.error(f"Error sending payment notification: {str(e)}")

async def deactivate_partnership(payment: Payment, db: AsyncSession):
    """Deactivate partnership after 30 days of non-payment"""
    try:
        result = await db.execute(select(User).filter(User.id == payment.user_id))
        user = result.scalar_one_or_none()
        
        if user:
            # Remove partnership from user's active partnerships
            active_partnerships = get_user_active_partnerships(user)
            if payment.partnership_level in active_partnerships:
                active_partnerships.remove(payment.partnership_level)
                # Ensure user has at least DROP_SHIPPING
                if not active_partnerships:
                    active_partnerships = [PartnershipLevel.DROP_SHIPPING]
                user.partnership_level = [p.value for p in active_partnerships]
            
            # Create deactivation record
            deactivation = PartnershipDeactivation(
                user_id=payment.user_id,
                partnership_level=payment.partnership_level,
                deactivation_reason="Non-payment after 30 days"
            )
            db.add(deactivation)
            db.add(user)
            
            logger.info(f"Partnership deactivated for user_id={payment.user_id}")
            
    except Exception as e:
        logger.error(f"Error deactivating partnership: {str(e)}")

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
        payments_result = await db.execute(select(Payment))
        all_payments = payments_result.scalars().all()
        
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
        
        deactivated_result = await db.execute(select(PartnershipDeactivation))
        deactivated_partnerships = deactivated_result.scalars().all()
        
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
                "partnership_level": level.partnership_name.value,
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
