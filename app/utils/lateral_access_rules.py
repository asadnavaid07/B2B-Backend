"""
Lateral access rules based on partnership position in level
Each partnership has 3 lateral tiers (1st, 2nd, 3rd) that map to other partnerships in the same level
"""
from app.models.registration import PartnershipLevel
from app.models.partnership_fees import PartnershipLevelGroup
from app.models.payment import PaymentPlan
from app.utils.partnership_level_mapping import get_partnership_level_group, get_partnerships_in_level
from typing import Optional, Dict

# Lateral tier mapping: For each partnership, define which partnerships are in each lateral tier
# Format: {partnership: {"1st": target_partnership, "2nd": target_partnership, "3rd": target_partnership}}
LATERAL_TIER_MAPPING: Dict[PartnershipLevel, Dict[str, PartnershipLevel]] = {
    # Level 1: Core Trade
    PartnershipLevel.DROP_SHIPPING: {
        "1st": PartnershipLevel.CONSIGNMENT,
        "2nd": PartnershipLevel.WHOLESALE,
        "3rd": PartnershipLevel.IMPORT_EXPORT,
    },
    PartnershipLevel.CONSIGNMENT: {
        "1st": PartnershipLevel.DROP_SHIPPING,
        "2nd": PartnershipLevel.WHOLESALE,
        "3rd": PartnershipLevel.IMPORT_EXPORT,
    },
    PartnershipLevel.WHOLESALE: {
        "1st": PartnershipLevel.DROP_SHIPPING,
        "2nd": PartnershipLevel.CONSIGNMENT,
        "3rd": PartnershipLevel.IMPORT_EXPORT,
    },
    PartnershipLevel.IMPORT_EXPORT: {
        "1st": PartnershipLevel.DROP_SHIPPING,
        "2nd": PartnershipLevel.CONSIGNMENT,
        "3rd": PartnershipLevel.WHOLESALE,
    },
    
    # Level 2: Brand Expansion
    PartnershipLevel.EXHIBITION: {
        "1st": PartnershipLevel.AUCTION,
        "2nd": PartnershipLevel.WHITE_LABEL,
        "3rd": PartnershipLevel.BRICK_MORTRAR,
    },
    PartnershipLevel.AUCTION: {
        "1st": PartnershipLevel.EXHIBITION,
        "2nd": PartnershipLevel.WHITE_LABEL,
        "3rd": PartnershipLevel.BRICK_MORTRAR,
    },
    PartnershipLevel.WHITE_LABEL: {
        "1st": PartnershipLevel.EXHIBITION,
        "2nd": PartnershipLevel.AUCTION,
        "3rd": PartnershipLevel.BRICK_MORTRAR,
    },
    PartnershipLevel.BRICK_MORTRAR: {
        "1st": PartnershipLevel.EXHIBITION,
        "2nd": PartnershipLevel.AUCTION,
        "3rd": PartnershipLevel.WHITE_LABEL,
    },
    
    # Level 3: Collaborative
    PartnershipLevel.DESIGN_COLLABORATION: {
        "1st": PartnershipLevel.STORYTELLING,
        "2nd": PartnershipLevel.WAREHOUSE,
        "3rd": PartnershipLevel.PACKAGING,
    },
    PartnershipLevel.STORYTELLING: {
        "1st": PartnershipLevel.DESIGN_COLLABORATION,
        "2nd": PartnershipLevel.WAREHOUSE,
        "3rd": PartnershipLevel.PACKAGING,
    },
    PartnershipLevel.WAREHOUSE: {
        "1st": PartnershipLevel.DESIGN_COLLABORATION,
        "2nd": PartnershipLevel.STORYTELLING,
        "3rd": PartnershipLevel.PACKAGING,
    },
    PartnershipLevel.PACKAGING: {
        "1st": PartnershipLevel.DESIGN_COLLABORATION,
        "2nd": PartnershipLevel.STORYTELLING,
        "3rd": PartnershipLevel.WAREHOUSE,
    },
    
    # Level 4: Technology
    PartnershipLevel.LOGISTICS: {
        "1st": PartnershipLevel.MUSEUM_INSTITUTIONAL,
        "2nd": PartnershipLevel.NGO_GOVERNMENT,
        "3rd": PartnershipLevel.TECHNOLOGY_PARTNERSHIP,
    },
    PartnershipLevel.MUSEUM_INSTITUTIONAL: {
        "1st": PartnershipLevel.LOGISTICS,
        "2nd": PartnershipLevel.NGO_GOVERNMENT,
        "3rd": PartnershipLevel.TECHNOLOGY_PARTNERSHIP,
    },
    PartnershipLevel.NGO_GOVERNMENT: {
        "1st": PartnershipLevel.LOGISTICS,
        "2nd": PartnershipLevel.MUSEUM_INSTITUTIONAL,
        "3rd": PartnershipLevel.TECHNOLOGY_PARTNERSHIP,
    },
    PartnershipLevel.TECHNOLOGY_PARTNERSHIP: {
        "1st": PartnershipLevel.LOGISTICS,
        "2nd": PartnershipLevel.MUSEUM_INSTITUTIONAL,
        "3rd": PartnershipLevel.NGO_GOVERNMENT,
    },
}

def get_lateral_target_partnership(
    from_partnership: PartnershipLevel,
    lateral_tier: PaymentPlan
) -> Optional[PartnershipLevel]:
    """
    Get the target partnership for a lateral tier from a given partnership.
    
    Args:
        from_partnership: The partnership user is currently on
        lateral_tier: The lateral tier (1st, 2nd, or 3rd)
    
    Returns:
        The target partnership for that tier, or None if not found
    """
    partnership_mapping = LATERAL_TIER_MAPPING.get(from_partnership)
    if not partnership_mapping:
        return None
    
    tier_key = lateral_tier.value  # "1st", "2nd", or "3rd"
    return partnership_mapping.get(tier_key)

def can_switch_laterally(
    from_partnership: PartnershipLevel,
    to_partnership: PartnershipLevel,
    lateral_tier: PaymentPlan
) -> tuple[bool, str]:
    """
    Check if user can switch laterally from from_partnership to to_partnership using the specified lateral tier.
    
    Args:
        from_partnership: Partnership user is switching from
        to_partnership: Partnership user wants to switch to
        lateral_tier: The lateral tier (1st, 2nd, or 3rd)
    
    Returns:
        (is_allowed, error_message)
    """
    # Check if both partnerships are in the same level
    from_level = get_partnership_level_group(from_partnership)
    to_level = get_partnership_level_group(to_partnership)
    
    if from_level != to_level:
        return False, "Lateral payment only allowed for partnerships in the same level"
    
    # Get the target partnership for this tier
    target_partnership = get_lateral_target_partnership(from_partnership, lateral_tier)
    
    if target_partnership is None:
        return False, f"No lateral tier mapping found for {from_partnership.value}"
    
    # Check if the target matches the requested partnership
    if target_partnership != to_partnership:
        tier_name = lateral_tier.value
        return False, f"Lateral tier {tier_name} from {from_partnership.value} leads to {target_partnership.value}, not {to_partnership.value}"
    
    return True, ""
