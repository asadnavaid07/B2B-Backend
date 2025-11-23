"""
Utility functions to map partnerships to their level groups
According to the document structure:
- Level 1: Core Trade (DROP_SHIPPING, CONSIGNMENT, WHOLESALE, IMPORT_EXPORT)
- Level 2: Brand Expansion (EXHIBITION, AUCTION, WHITE_LABEL, BRICK_MORTRAR)
- Level 3: Collaborative (DESIGN_COLLABORATION, STORYTELLING, WAREHOUSE, PACKAGING)
- Level 4: Technology (LOGISTICS, MUSEUM_INSTITUTIONAL, NGO_GOVERNMENT, TECHNOLOGY_PARTNERSHIP)
"""
from app.models.registration import PartnershipLevel
from app.models.partnership_fees import PartnershipLevelGroup

# Mapping of partnerships to their level groups
PARTNERSHIP_TO_LEVEL = {
    PartnershipLevel.DROP_SHIPPING: PartnershipLevelGroup.LEVEL_1,
    PartnershipLevel.CONSIGNMENT: PartnershipLevelGroup.LEVEL_1,
    PartnershipLevel.WHOLESALE: PartnershipLevelGroup.LEVEL_1,
    PartnershipLevel.IMPORT_EXPORT: PartnershipLevelGroup.LEVEL_1,
    PartnershipLevel.EXHIBITION: PartnershipLevelGroup.LEVEL_2,
    PartnershipLevel.AUCTION: PartnershipLevelGroup.LEVEL_2,
    PartnershipLevel.WHITE_LABEL: PartnershipLevelGroup.LEVEL_2,
    PartnershipLevel.BRICK_MORTRAR: PartnershipLevelGroup.LEVEL_2,
    PartnershipLevel.DESIGN_COLLABORATION: PartnershipLevelGroup.LEVEL_3,
    PartnershipLevel.STORYTELLING: PartnershipLevelGroup.LEVEL_3,
    PartnershipLevel.WAREHOUSE: PartnershipLevelGroup.LEVEL_3,
    PartnershipLevel.PACKAGING: PartnershipLevelGroup.LEVEL_3,
    PartnershipLevel.LOGISTICS: PartnershipLevelGroup.LEVEL_4,
    PartnershipLevel.MUSEUM_INSTITUTIONAL: PartnershipLevelGroup.LEVEL_4,
    PartnershipLevel.NGO_GOVERNMENT: PartnershipLevelGroup.LEVEL_4,
    PartnershipLevel.TECHNOLOGY_PARTNERSHIP: PartnershipLevelGroup.LEVEL_4,
}

# Level groups with their partnerships
LEVEL_PARTNERSHIPS = {
    PartnershipLevelGroup.LEVEL_1: [
        PartnershipLevel.DROP_SHIPPING,
        PartnershipLevel.CONSIGNMENT,
        PartnershipLevel.WHOLESALE,
        PartnershipLevel.IMPORT_EXPORT,
    ],
    PartnershipLevelGroup.LEVEL_2: [
        PartnershipLevel.EXHIBITION,
        PartnershipLevel.AUCTION,
        PartnershipLevel.WHITE_LABEL,
        PartnershipLevel.BRICK_MORTRAR,
    ],
    PartnershipLevelGroup.LEVEL_3: [
        PartnershipLevel.DESIGN_COLLABORATION,
        PartnershipLevel.STORYTELLING,
        PartnershipLevel.WAREHOUSE,
        PartnershipLevel.PACKAGING,
    ],
    PartnershipLevelGroup.LEVEL_4: [
        PartnershipLevel.LOGISTICS,
        PartnershipLevel.MUSEUM_INSTITUTIONAL,
        PartnershipLevel.NGO_GOVERNMENT,
        PartnershipLevel.TECHNOLOGY_PARTNERSHIP,
    ],
}

def get_partnership_level_group(partnership: PartnershipLevel) -> PartnershipLevelGroup:
    """Get the level group for a partnership"""
    return PARTNERSHIP_TO_LEVEL.get(partnership)

def get_partnerships_in_level(level_group: PartnershipLevelGroup) -> list[PartnershipLevel]:
    """Get all partnerships in a level group"""
    return LEVEL_PARTNERSHIPS.get(level_group, [])

def are_in_same_level(partnership1: PartnershipLevel, partnership2: PartnershipLevel) -> bool:
    """Check if two partnerships are in the same level"""
    return get_partnership_level_group(partnership1) == get_partnership_level_group(partnership2)

def get_level_number(level_group: PartnershipLevelGroup) -> int:
    """Get the numeric level (1, 2, 3, or 4)"""
    level_map = {
        PartnershipLevelGroup.LEVEL_1: 1,
        PartnershipLevelGroup.LEVEL_2: 2,
        PartnershipLevelGroup.LEVEL_3: 3,
        PartnershipLevelGroup.LEVEL_4: 4,
    }
    return level_map.get(level_group, 0)

def is_upward_movement(from_partnership: PartnershipLevel, to_partnership: PartnershipLevel) -> bool:
    """Check if moving from one partnership to another is an upward movement (to higher level)"""
    from_level = get_level_number(get_partnership_level_group(from_partnership))
    to_level = get_level_number(get_partnership_level_group(to_partnership))
    return to_level > from_level

