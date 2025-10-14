# User Retention Tracking System

## Overview

The User Retention Tracking System automatically tracks and updates user retention periods from the moment their registration is approved. The system calculates retention in months and provides analytics and management capabilities.

## Features

### 1. Automatic Retention Tracking
- **Start Date**: When a user's registration is approved (`is_registered = APPROVED`), the system automatically sets `retention_start_date` to the current timestamp
- **Initial Period**: The `retention_period` is initialized to 0 months
- **Monthly Updates**: The system automatically updates retention periods every month

### 2. Background Scheduler
- **Automatic Updates**: Runs monthly to update all users' retention periods
- **Startup Integration**: Automatically starts when the application launches
- **Graceful Shutdown**: Properly stops when the application shuts down

### 3. API Endpoints

#### Admin Endpoints (Super Admin Access Required)
- `POST /retention/update-all` - Manually trigger retention update for all users
- `POST /retention/update-user/{user_id}` - Update retention for specific user
- `GET /retention/analytics` - Get retention analytics
- `GET /retention/eligible-upgrades` - Get users eligible for partnership upgrades
- `POST /retention/scheduler/start` - Start the monthly scheduler
- `POST /retention/scheduler/stop` - Stop the monthly scheduler
- `GET /retention/scheduler/status` - Get scheduler status

#### Admin/Sub-Admin Endpoints
- `GET /retention/analytics` - Get retention analytics
- `GET /retention/eligible-upgrades` - Get users eligible for partnership upgrades
- `GET /retention/scheduler/status` - Get scheduler status

## Database Schema

### User Table Fields
```sql
retention_period INTEGER DEFAULT 0  -- Current retention period in months
retention_start_date DATETIME       -- When retention tracking started (approval date)
```

### Registration Level Requirements
Each partnership level has specific retention requirements:
- **DROP_SHIPPING**: 0 months
- **CONSIGNMENT**: 12 months
- **WHOLESALE**: 4 months
- **IMPORT_EXPORT**: 4 months
- **EXHIBITION**: 4 months
- **AUCTION**: 4 months
- **WHITE_LABEL**: 4 months
- **BRICK_MORTRAR**: 4 months
- **DESIGN_COLLABORATION**: 4 months
- **STORYTELLING**: 4 months
- **WAREHOUSE**: 4 months
- **PACKAGING**: 18 months
- **LOGISTICS**: 12 months
- **MUSEUM_INSTITUTIONAL**: 0 months
- **NGO_GOVERNMENT**: 0 months
- **TECHNOLOGY_PARTNERSHIP**: 0 months

## How It Works

### 1. Registration Approval Process
When an admin approves a user's registration:
```python
if approval.status == "APPROVED":
    user.retention_start_date = datetime.utcnow()
    user.retention_period = 0  # Initialize to 0 months
    user.is_registered = RegistrationStatus.APPROVED
```

### 2. Monthly Calculation
The system calculates retention months using this logic:
```python
def calculate_retention_months(user):
    now = datetime.utcnow()
    start_date = user.retention_start_date
    
    # Calculate difference in months
    months = (now.year - start_date.year) * 12 + (now.month - start_date.month)
    
    # Adjust if day hasn't reached the start day
    if now.day < start_date.day:
        months -= 1
        
    return max(0, months)
```

### 3. Automatic Updates
- **Schedule**: Runs on the 1st of every month at midnight UTC
- **Process**: Updates all approved users' retention periods
- **Logging**: Comprehensive logging of all updates and errors

## Usage Examples

### Manual Retention Update
```bash
curl -X POST "http://localhost:8000/retention/update-all" \
  -H "Authorization: Bearer <admin_token>"
```

### Get Retention Analytics
```bash
curl -X GET "http://localhost:8000/retention/analytics" \
  -H "Authorization: Bearer <admin_token>"
```

### Check Scheduler Status
```bash
curl -X GET "http://localhost:8000/retention/scheduler/status" \
  -H "Authorization: Bearer <admin_token>"
```

## Analytics Data

The system provides comprehensive analytics:
```json
{
  "total_users": 150,
  "average_retention": 3.2,
  "retention_distribution": {
    "0": 45,
    "1": 30,
    "2": 25,
    "3": 20,
    "4": 15,
    "5": 10,
    "6": 5
  },
  "users_by_partnership_level": {
    "DROP_SHIPPING": 50,
    "WHOLESALE": 30,
    "CONSIGNMENT": 20,
    "IMPORT_EXPORT": 15
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Partnership Level Eligibility

The system can identify users eligible for partnership level upgrades:
```json
{
  "eligible_users": [
    {
      "user_id": 123,
      "email": "user@example.com",
      "current_retention_months": 6,
      "partnership_level": "WHOLESALE",
      "required_retention_months": 4,
      "kpi_score": 7.5,
      "retention_start_date": "2023-07-15T10:30:00Z"
    }
  ],
  "total_eligible": 1,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Handling

The system includes comprehensive error handling:
- **Database Errors**: Proper rollback and logging
- **Scheduler Errors**: Automatic retry with exponential backoff
- **API Errors**: Detailed error messages and proper HTTP status codes
- **Validation**: Input validation for all endpoints

## Monitoring and Logging

All operations are logged with appropriate levels:
- **INFO**: Successful operations, scheduler status
- **WARNING**: Non-critical issues, user not found
- **ERROR**: Database errors, system failures
- **DEBUG**: Detailed operation information

## Testing

Run the test script to verify functionality:
```bash
python app/test_retention.py
```

## Security

- All admin endpoints require super admin or sub-admin authentication
- JWT token validation for all API calls
- Proper authorization checks for sensitive operations

## Performance Considerations

- **Batch Updates**: All users updated in a single transaction
- **Background Processing**: Non-blocking monthly updates
- **Efficient Queries**: Optimized database queries with proper indexing
- **Memory Management**: Proper cleanup of database sessions

## Future Enhancements

Potential improvements:
1. **Retention Notifications**: Email users on retention milestones
2. **Retention Reports**: Generate detailed reports for management
3. **Retention Policies**: Configurable retention requirements
4. **Retention Rewards**: Automatic benefits based on retention period
5. **Retention Dashboard**: Real-time dashboard for monitoring
