
from typing import List
from datetime import datetime, timedelta
from app.models.notification import Notification, NotificationTargetType
from app.models.registration import PartnershipLevel
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


def retention_str_to_days(retention_period: str) -> int:

    if retention_period is None:
        return 0
    if str(retention_period).lower() == "none":
        return 0
    retention_period = str(retention_period).strip()
    
    try:
            return int(retention_period) * 30
    except ValueError:
            return 0

def is_retention_period_over(retention_period: str, retention_start_date: datetime, current_date: datetime) -> bool:
    days = retention_str_to_days(retention_period)
    if days == 0 or retention_start_date is None:
        return True
    retention_end = retention_start_date + timedelta(days=days)
    return current_date >= retention_end

def get_retention_expiration(retention_period: str, retention_start_date: datetime) -> datetime | None:
    days = retention_str_to_days(retention_period)
    if days == 0 or retention_start_date is None:
        return None
    return retention_start_date + timedelta(days=days)


def get_available_partnerships(kpi_score: float, current_level: PartnershipLevel, retention_period: str) -> List[PartnershipLevel]:

    partnership_levels = partnership_dic
    
    current_index = 0
    for i in range(len(partnership_levels)):
        if partnership_levels[i]["level"] == current_level:
            current_index = i
            break
    
    available = []
    current_date = datetime.utcnow()
    
    for i in range(current_index + 1, len(partnership_levels)):
        next_level = partnership_levels[i]

        if retention_period==0:
             return []
             
        if retention_period>=months_till_level[next_level["level"]] and kpi_score >= next_level["min_kpi"]:
            available.append(next_level["level"])
        else:
             break
    print(f"Available partnership levels: {available}")
    return available
    

async def update_partnership_level(user: User, kpi_score: float, db: AsyncSession) -> bool:
    partnership_levels = partnership_dic

    
    current_level_index = next((i for i, level in enumerate(partnership_levels) if level["level"] == user.partnership_level), 0)
    current_level = partnership_levels[current_level_index]
    next_level = partnership_levels[min(current_level_index + 1, len(partnership_levels) - 1)] if current_level_index < len(partnership_levels) - 1 else current_level
    
    current_date = datetime.utcnow()
    if kpi_score >= next_level["min_kpi"] and is_retention_period_over(user.retention_period, user.retention_start_date or current_date, current_date):
        user.partnership_level = next_level["level"]
        user.retention_period = next_level["retention"]
        user.retention_start_date = datetime.utcnow()
        
        # Create notification for user
        notification = Notification(
            admin_id=user.id,
            message=f"Congratulations! Your partnership level has been upgraded to {next_level['level']}.",
            target_type=NotificationTargetType.ALL_USERS,
            visibility=True,
            created_at=datetime.utcnow()
        )
        db.add(notification)
        return True
    return False


partnership_level = [
    {"level": PartnershipLevel.DROP_SHIPPING, "min_kpi": 0, "retention": 0},
    {"level": PartnershipLevel.CONSIGNMENT, "min_kpi": 6.0, "retention": 12},
    {"level": PartnershipLevel.WHOLESALE, "min_kpi": 6.5, "retention": 4},
    {"level": PartnershipLevel.IMPORT_EXPORT, "min_kpi": 7.0, "retention": 4},
    {"level": PartnershipLevel.EXHIBITION, "min_kpi": 7.0, "retention": 4},
    {"level": PartnershipLevel.AUCTION, "min_kpi": 7.5, "retention": 4},
    {"level": PartnershipLevel.WHITE_LABEL, "min_kpi": 8.0, "retention": 4},
    {"level": PartnershipLevel.BRICK_MORTRAR, "min_kpi": 8.0, "retention": 4},
    {"level": PartnershipLevel.DESIGN_COLLABORATION, "min_kpi": 8.0, "retention": 4},
    {"level": PartnershipLevel.STORYTELLING, "min_kpi": 8.5, "retention": 4},
    {"level": PartnershipLevel.WAREHOUSE, "min_kpi": 8.5, "retention": 4},
    {"level": PartnershipLevel.PACKAGING, "min_kpi": 8.0, "retention": 18},
    {"level": PartnershipLevel.LOGISTICS, "min_kpi": 0, "retention": 12},  
    {"level": PartnershipLevel.MUSEUM_INSTITUTIONAL, "min_kpi": 0, "retention": 0},
    {"level": PartnershipLevel.NGO_GOVERNMENT, "min_kpi": 0, "retention": 0},
    {"level": PartnershipLevel.TECHNOLOGY_PARTNERSHIP, "min_kpi": 0, "retention": 0},
]


partnership_dic = [
    {"level": "DROP_SHIPPING", "min_kpi": 0, "retention":0},
    {"level": "CONSIGNMENT", "min_kpi": 6.0, "retention": 12},
    {"level": "IMPORT_EXPORT", "min_kpi": 6.5, "retention": 4},
    {"level": "WHOLESALE", "min_kpi": 7.0, "retention": 4},
    {"level": "EXHIBITION", "min_kpi": 7.0, "retention": 4},
    {"level": "AUCTION", "min_kpi": 7.5, "retention": 4},
    {"level": "WHITE_LABEL", "min_kpi": 8.0, "retention": 4},
    {"level": "BRICK_MORTRAR", "min_kpi": 8.0, "retention": 4},
    {"level": "DESIGN_COLLABORATION", "min_kpi": 8.0, "retention": 4},
    {"level": "STORYTELLING", "min_kpi": 8.5, "retention": 4},
    {"level": "WAREHOUSE", "min_kpi": 8.5, "retention": 4},
    {"level": "PACKAGING", "min_kpi": 8.0, "retention": 18},
    {"level": "LOGISTICS", "min_kpi": 0, "retention": 12},
    {"level": "MUSEUM_INSTITUTIONAL", "min_kpi": 0, "retention": 0},
    {"level": "NGO_GOVERNMENT", "min_kpi": 0, "retention": 0},
    {"level": "TECHNOLOGY_PARTNERSHIP", "min_kpi": 0, "retention": 0}
]


months_till_level = {
    "DROP_SHIPPING": 0,
    "CONSIGNMENT": 12,
    "IMPORT_EXPORT": 16,
    "WHOLESALE": 20,
    "EXHIBITION": 24,
    "AUCTION": 28,
    "WHITE_LABEL": 32,
    "BRICK_MORTRAR": 36,
    "DESIGN_COLLABORATION": 40,
    "STORYTELLING": 44,
    "WAREHOUSE": 48,
    "PACKAGING": 66,
    "LOGISTICS": 78,
    "MUSEUM_INSTITUTIONAL": 78,
    "NGO_GOVERNMENT": 78,
    "TECHNOLOGY_PARTNERSHIP": 78
}