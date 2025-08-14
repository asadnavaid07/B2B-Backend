import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.teams import Team, TeamMember
from app.schema.teams import TeamCreate, TeamUpdate, TeamResponse, TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse
from app.services.auth.jwt import role_required
from app.schema.user import UserResponse
import logging
from datetime import datetime
import shutil
import uuid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

team_router = APIRouter(prefix="/teams", tags=["teams"])

# Directory for storing team member images
UPLOAD_DIR = "uploads/team_members"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@team_router.get("", response_model=List[TeamResponse])
async def get_teams(db: AsyncSession = Depends(get_db)):
    logger.debug("Fetching all teams with members and sub-teams")
    result = await db.execute(
        select(Team)
        .filter(Team.parent_id == None)  # Only top-level teams
        .options(selectinload(Team.members), selectinload(Team.sub_teams).selectinload(Team.members))
    )
    teams = result.scalars().all()
    if not teams:
        logger.info("No teams found")
        return []
    return teams

@team_router.post("", response_model=TeamResponse)
async def create_team(
    team: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin", "sub_admin"))
):
    logger.debug(f"Creating team: {team.dict()}")
    if team.parent_id:
        result = await db.execute(select(Team).filter(Team.id == team.parent_id))
        parent_team = result.scalar_one_or_none()
        if not parent_team:
            logger.error(f"Parent team ID {team.parent_id} not found")
            raise HTTPException(status_code=404, detail="Parent team not found")
    
    db_team = Team(**team.dict())
    db.add(db_team)
    try:
        await db.commit()
        await db.refresh(db_team)
        logger.info(f"Team {db_team.name} created successfully")
        return db_team
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating team: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")

@team_router.post("/update", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin", "sub_admin"))
):
    logger.debug(f"Updating team ID {team_id}: {team_update.dict()}")
    result = await db.execute(select(Team).filter(Team.id == team_id))
    db_team = result.scalar_one_or_none()
    if not db_team:
        logger.error(f"Team ID {team_id} not found")
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team_update.parent_id:
        result = await db.execute(select(Team).filter(Team.id == team_update.parent_id))
        parent_team = result.scalar_one_or_none()
        if not parent_team:
            logger.error(f"Parent team ID {team_update.parent_id} not found")
            raise HTTPException(status_code=404, detail="Parent team not found")
    
    update_data = team_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_team, key, value)
    db_team.updated_at = datetime.utcnow()
    
    try:
        db.add(db_team)
        await db.commit()
        await db.refresh(db_team)
        logger.info(f"Team ID {team_id} updated successfully")
        return db_team
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating team ID {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")

@team_router.post("/members/add", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: int,
    member: TeamMemberCreate,
    image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin", "sub_admin"))
):
    logger.debug(f"Adding member to team ID {team_id}: {member.dict()}")
    result = await db.execute(select(Team).filter(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        logger.error(f"Team ID {team_id} not found")
        raise HTTPException(status_code=404, detail="Team not found")
    ALLOWED_TYPES = {"jpeg", "png", "gif", "webp"}
    image_path = None
    if image:
        file_extension = image.filename.split(".")[-1]
        if file_extension not in ALLOWED_TYPES:
         raise HTTPException(400, "Invalid or unsupported image format")

        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        image_path = os.path.join(UPLOAD_DIR, unique_filename)
        try:
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            logger.debug(f"Image saved at {image_path}")
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
    
    db_member = TeamMember(
        team_id=team_id,
        name=member.name,
        role=member.role,
        bio=member.bio,
        image=image_path
    )
    db.add(db_member)
    try:
        await db.commit()
        await db.refresh(db_member)
        logger.info(f"Team member {db_member.name} added to team ID {team_id}")
        return db_member
    except Exception as e:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        await db.rollback()
        logger.error(f"Error adding team member: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add team member: {str(e)}")

@team_router.post("/members/update", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: int,
    member_update: TeamMemberUpdate,
    image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin", "sub_admin"))
):
    logger.debug(f"Updating team member ID {member_id}: {member_update.dict()}")
    result = await db.execute(select(TeamMember).filter(TeamMember.id == member_id))
    db_member = result.scalar_one_or_none()
    if not db_member:
        logger.error(f"Team member ID {member_id} not found")
        raise HTTPException(status_code=404, detail="Team member not found")
    
    image_path = db_member.image
    if image:
        file_extension = image.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        image_path = os.path.join(UPLOAD_DIR, unique_filename)
        try:
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            logger.debug(f"New image saved at {image_path}")
            if db_member.image and os.path.exists(db_member.image):
                os.remove(db_member.image)
                logger.debug(f"Old image {db_member.image} deleted")
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
    
    update_data = member_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_member, key, value)
    if image_path:
        db_member.image = image_path
    db_member.updated_at = datetime.utcnow()
    
    try:
        db.add(db_member)
        await db.commit()
        await db.refresh(db_member)
        logger.info(f"Team member ID {member_id} updated successfully")
        return db_member
    except Exception as e:
        if image_path and image_path != db_member.image and os.path.exists(image_path):
            os.remove(image_path)
        await db.rollback()
        logger.error(f"Error updating team member ID {member_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update team member: {str(e)}")

@team_router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin", "sub_admin"))
):
    logger.debug(f"Deleting team member ID {member_id}")
    result = await db.execute(select(TeamMember).filter(TeamMember.id == member_id))
    db_member = result.scalar_one_or_none()
    if not db_member:
        logger.error(f"Team member ID {member_id} not found")
        raise HTTPException(status_code=404, detail="Team member not found")
    
    if db_member.image and os.path.exists(db_member.image):
        try:
            os.remove(db_member.image)
            logger.debug(f"Image {db_member.image} deleted")
        except Exception as e:
            logger.warning(f"Failed to delete image {db_member.image}: {str(e)}")
    
    try:
        await db.delete(db_member)
        await db.commit()
        logger.info(f"Team member ID {member_id} deleted successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting team member ID {member_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete team member: {str(e)}")