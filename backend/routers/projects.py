from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models.project import Project
from models.user import User
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSummary
from routers.auth import get_current_user, require_boss

router = APIRouter()


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.is_active == True).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    project = Project(**payload.model_dump(), owner_id=current_user.id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_or_404(db, project_id)
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    project = await _get_or_404(db, project_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    project = await _get_or_404(db, project_id)
    project.is_active = False
    await db.flush()


@router.get("/summary/all", response_model=List[ProjectSummary])
async def list_project_summaries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project.id, Project.name, Project.status).where(Project.is_active == True)
    )
    return result.mappings().all()


# ─── Helper ──────────────────────────────────────────────────────────────────
async def _get_or_404(db: AsyncSession, project_id: int) -> Project:
    result  = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
