# Payment Integration System - Complete Implementation Guide

## Overview

This document outlines the complete payment integration system implemented for the B2B Backend, including lateral entry payments, monthly subscriptions, automated notifications, and partnership deactivation logic.

## System Architecture

### 1. Payment Models (`app/models/payment.py`)

#### Payment Table
- **Purpose**: Stores all payment transactions (lateral and monthly)
- **Key Fields**:
  - `user_id`: Reference to user
  - `partnership_level`: Partnership level being paid for
  - `plan`: Three-tier pricing (1st, 2nd, 3rd)
  - `payment_type`: LATERAL or MONTHLY
  - `payment_status`: PENDING, SUCCESS, FAILED, CANCELLED, REFUNDED
  - `stripe_payment_id`: Stripe payment intent or subscription ID
  - `next_payment_due`: For monthly payments

#### PaymentNotification Table
- **Purpose**: Tracks payment notifications sent to users
- **Key Fields**:
  - `notification_type`: 7_days, 14_days, 21_days, 30_days_deactivation
  - `days_overdue`: Number of days payment is overdue
  - `sent_at`: When notification was sent

#### PartnershipDeactivation Table
- **Purpose**: Records partnership deactivations due to non-payment
- **Key Fields**:
  - `deactivation_reason`: Reason for deactivation
  - `reactivation_available`: Whether partnership can be reactivated

### 2. Payment Schemas (`app/schema/payment.py`)

Comprehensive Pydantic models for:
- Payment requests and responses
- Subscription management
- Payment analytics
- Three-tier pricing management
- Notification responses

### 3. Payment Routes (`app/api/routes/payments.py`)

#### Core Endpoints

##### Lateral Entry Payment
```
POST /payments/lateral
```
- **Purpose**: One-time payment for lateral entry to partnership levels
- **Restrictions**:
  - No lateral entry for DROP_SHIPPING
  - No lateral entry for last three partnership levels (MUSEUM_INSTITUTIONAL, NGO_GOVERNMENT, TECHNOLOGY_PARTNERSHIP)
  - One lateral payment per partnership level per user

##### Monthly Subscription
```
POST /payments/monthly
```
- **Purpose**: Monthly recurring payment for all partnership levels
- **Features**:
  - Stripe subscription creation
  - Automatic renewal every 30 days
  - Prevents duplicate subscriptions

##### Stripe Webhook
```
POST /payments/webhook
```
- **Purpose**: Handles Stripe payment events
- **Events Handled**:
  - `payment_intent.succeeded`: Lateral payments
  - `invoice.paid`: Monthly subscription payments
  - `invoice.payment_failed`: Failed payments with notification logic

#### Management Endpoints

##### Payment History
```
GET /payments/history
```
- Returns payment history for current user

##### Payment Notifications
```
GET /payments/notifications
```
- Returns payment notifications for current user

##### Payment Analytics (Admin Only)
```
GET /payments/analytics
```
- Comprehensive payment analytics including:
  - Total revenue
  - Monthly recurring revenue
  - Success rates
  - Overdue payments
  - Deactivated partnerships

##### Three-Tier Pricing Management (Admin Only)
```
POST /payments/pricing
GET /payments/pricing
```
- Set and retrieve three-tier pricing for partnership levels

##### Overdue Payment Check (Admin Only)
```
POST /payments/check-overdue
```
- Manually trigger overdue payment monitoring

##### Partnership Deactivations (Admin Only)
```
GET /payments/deactivations
```
- View all partnership deactivations

### 4. Payment Service (`app/services/payment_service.py`)

#### Key Functions

##### `check_overdue_payments()`
- Monitors all failed monthly payments
- Sends notifications based on days overdue
- Deactivates partnerships after 30 days

##### `send_payment_notification()`
- Sends notifications at 7, 14, 21, and 30 days
- Prevents duplicate notifications
- Creates notification records

##### `deactivate_partnership()`
- Deactivates partnership after 30 days of non-payment
- Reverts user to DROP_SHIPPING level
- Creates deactivation record

##### `get_payment_analytics()`
- Comprehensive analytics for admin dashboard
- Revenue by partnership level
- Payment distribution by type

### 5. Background Task Service (`app/services/background_tasks.py`)

#### Automated Monitoring
- **Daily Payment Monitoring**: Checks for overdue payments every 24 hours
- **Monthly Retention Updates**: Updates user retention periods monthly
- **Notification System**: Automatically sends payment notifications
- **Deactivation System**: Automatically deactivates partnerships after 30 days

## Payment Flow

### Lateral Entry Payment Flow

1. **User Request**: User requests lateral entry to a partnership level
2. **Validation**: System validates:
   - Partnership level allows lateral entry
   - User hasn't already made lateral payment for this level
   - Valid pricing tier selected
3. **Stripe Integration**: Creates Stripe payment intent
4. **Database Record**: Creates payment record with PENDING status
5. **Webhook Processing**: Stripe webhook updates payment status to SUCCESS
6. **User Access**: User gains access to partnership level

### Monthly Subscription Flow

1. **User Request**: User requests monthly subscription
2. **Validation**: System validates:
   - No existing active subscription for partnership level
   - Valid pricing tier selected
3. **Stripe Integration**: Creates Stripe customer, product, price, and subscription
4. **Database Record**: Creates payment record with next payment due date
5. **Webhook Processing**: Stripe webhook handles recurring payments
6. **Monitoring**: Background service monitors for payment failures

### Payment Failure and Notification Flow

1. **Payment Failure**: Stripe webhook receives `invoice.payment_failed` event
2. **Status Update**: Payment status updated to FAILED
3. **Notification Logic**: Based on days overdue:
   - **7 days**: First warning notification
   - **14 days**: Second warning notification
   - **21 days**: Final warning notification
   - **30 days**: Deactivation notification and partnership deactivation
4. **User Reversion**: User reverted to DROP_SHIPPING level
5. **Record Keeping**: Deactivation record created

## Three-Tier Pricing System

### Pricing Structure
Each partnership level has three pricing tiers:
- **1st Tier**: Basic pricing
- **2nd Tier**: Mid-level pricing
- **3rd Tier**: Premium pricing

### Admin Management
- Admins can set pricing for each partnership level
- Pricing is stored in JSON format in the database
- Real-time pricing updates available

## Security Features

### Authentication
- All payment endpoints require user authentication
- Admin-only endpoints require admin role verification

### Data Protection
- Stripe handles sensitive payment data
- Only payment IDs and metadata stored locally
- Secure webhook verification

### Validation
- Comprehensive input validation
- Duplicate payment prevention
- Partnership level restrictions enforced

## Monitoring and Analytics

### Real-time Monitoring
- Daily automated payment monitoring
- Immediate webhook processing
- Background task monitoring

### Analytics Dashboard
- Total revenue tracking
- Monthly recurring revenue
- Payment success rates
- Overdue payment tracking
- Partnership deactivation metrics

## Error Handling

### Comprehensive Error Management
- Stripe API error handling
- Database transaction rollbacks
- Detailed error logging
- User-friendly error messages

### Recovery Mechanisms
- Failed payment retry logic
- Webhook event replay capability
- Manual payment monitoring triggers

## Deployment Considerations

### Environment Variables
- `STRIPE_SECRET_KEY`: Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: Webhook verification secret

### Database Migration
- Run migration: `payment_models_migration.py`
- Creates all payment-related tables and enums

### Background Services
- Payment monitoring runs automatically
- Retention updates run monthly
- All services start with application startup

## API Documentation

### Swagger/OpenAPI
- Complete API documentation available at `/docs`
- All endpoints documented with examples
- Authentication requirements specified

### Testing
- Comprehensive error handling
- Input validation
- Edge case coverage

## Future Enhancements

### Potential Improvements
1. **Payment Methods**: Support for additional payment methods
2. **Refund System**: Automated refund processing
3. **Payment Plans**: Flexible payment plan options
4. **Analytics**: Advanced reporting and dashboards
5. **Notifications**: Email and SMS notifications
6. **Reactivation**: Partnership reactivation system

## Conclusion

The payment integration system provides a comprehensive solution for managing lateral entry payments, monthly subscriptions, automated notifications, and partnership deactivation. The system is designed for scalability, security, and ease of management while providing detailed analytics and monitoring capabilities.

All requirements have been implemented:
✅ Lateral entry payments (one-time, no dropshipping, no last three levels)
✅ Monthly payments for all partnerships
✅ Three-tier pricing system
✅ Automated notifications (7, 14, 21 days)
✅ 30-day deactivation system
✅ Admin dashboard integration
✅ Background monitoring and automation
