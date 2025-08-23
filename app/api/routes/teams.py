from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.teams import Team, TeamMember
from app.models.user import User
from app.services.auth.jwt import get_current_user
from app.schema.teams import TeamCreate, TeamUpdate, TeamResponse, TeamFullResponse, TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse
from app.schema.user import UserResponse
from app.schema.user import UserRole
import os
import uuid
import logging
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)
teams_router = APIRouter(prefix="/teams", tags=["teams"])


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

async def save_member_image(file: UploadFile, team_id: int) -> str:
    try:
        upload_dir = f"uploads/team_members/{team_id}"
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid file format. Allowed: {ALLOWED_EXTENSIONS}")
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving team member image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

@teams_router.get("/", response_model=list[TeamResponse])
async def get_teams(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Team).options(selectinload(Team.members))
        )
        teams = result.scalars().all()
        logger.info(f"Fetched {len(teams)} teams")
        return teams
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch teams: {str(e)}")

@teams_router.post("/", status_code=201, response_model=TeamFullResponse)
async def create_team(
    team_data: TeamCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        new_team = Team(**team_data.dict())
        db.add(new_team)
        await db.commit()
        await db.refresh(new_team)
        logger.info(f"Team created: {new_team.name} (team_id={new_team.id}) by user {current_user.email}")
        return new_team
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating team: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")

@teams_router.post("/update", status_code=200, response_model=TeamFullResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.execute(select(Team).filter(Team.id == team_id))
        team = result.scalar_one_or_none()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        for field, value in team_data.dict(exclude_unset=True).items():
            setattr(team, field, value)
        
        db.add(team)
        await db.commit()
        await db.refresh(team)
        
        result = await db.execute(select(TeamMember).filter(TeamMember.team_id == team.id))
        team.members = result.scalars().all()
        logger.info(f"Team updated: {team.name} (team_id={team_id}) by user {current_user.email}")
        return team
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")

from fastapi import Form

@teams_router.post("/members/add", status_code=201, response_model=TeamMemberResponse)
async def add_team_member(
    team_id: int,
    name: str = Form(...),
    role: str = Form(...),
    image: UploadFile = File(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.execute(select(Team).filter(Team.id == team_id))
        team = result.scalar_one_or_none()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        image_path = None
        if image:
            image_path = await save_member_image(image, team_id)
        
        new_member = TeamMember(
            team_id=team_id,
            name=name,
            role=role,
            image_path=image_path
        )
        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)
        logger.info(f"Team member added: {new_member.name} to team_id={team_id} by user {current_user.email}")
        return new_member
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding team member to team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add team member: {str(e)}")
    


@teams_router.post("/members/update", status_code=200, response_model=TeamMemberResponse)
async def update_team_member(
    member_id: int,
    member_data: TeamMemberUpdate,
    image: UploadFile = File(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.execute(select(TeamMember).filter(TeamMember.id == member_id))
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        for field, value in member_data.dict(exclude_unset=True).items():
            setattr(member, field, value)
        
        if image:
            member.image_path = await save_member_image(image, member.team_id)
        
        db.add(member)
        await db.commit()
        await db.refresh(member)
        logger.info(f"Team member updated: {member.name} (member_id={member_id}) by user {current_user.email}")
        return member
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating team member {member_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update team member: {str(e)}")

@teams_router.delete("/members/{id}", status_code=200)
async def delete_team_member(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.execute(select(TeamMember).filter(TeamMember.id == id))
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        await db.delete(member)
        await db.commit()
        logger.info(f"Team member deleted: member_id={id} by user {current_user.email}")
        return {"message": "Team member deleted successfully", "member_id": id}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting team member {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete team member: {str(e)}")