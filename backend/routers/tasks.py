from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from database import get_db
from models.task import Task, TaskStatus
from models.user import User
from schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskSummary, PRDParseRequest
from routers.auth import get_current_user, require_boss
from services.prd_parser import prd_parser

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[int]     = Query(None),
    sprint_id:  Optional[int]     = Query(None),
    status:     Optional[TaskStatus] = Query(None),
    assigned_to:Optional[int]     = Query(None),
    db: AsyncSession               = Depends(get_db),
    current_user: User             = Depends(get_current_user),
):
    q = select(Task)
    if project_id:  q = q.where(Task.project_id == project_id)
    if sprint_id:   q = q.where(Task.sprint_id  == sprint_id)
    if status:      q = q.where(Task.status     == status)
    if assigned_to: q = q.where(Task.assigned_to == assigned_to)
    result = await db.execute(q.order_by(Task.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession      = Depends(get_db),
    current_user: User    = Depends(require_boss),
):
    task = Task(**payload.model_dump())
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@router.post("/parse-prd", response_model=List[TaskResponse])
async def parse_prd_and_create_tasks(
    payload: PRDParseRequest,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    """Parse a PRD with AI and bulk-create tasks."""
    extracted = await prd_parser.parse(payload.prd_text, payload.project_id, payload.source)
    if not extracted:
        raise HTTPException(status_code=422, detail="No tasks could be extracted from the PRD")

    created_tasks = []
    for item in extracted:
        task = Task(
            title               = item.get("title", "Untitled Task"),
            description         = item.get("description"),
            priority            = item.get("priority", "medium"),
            story_points        = item.get("story_points"),
            suggested_role      = item.get("suggested_role"),
            labels              = item.get("labels", []),
            acceptance_criteria = item.get("acceptance_criteria", []),
            source              = payload.source,
            project_id          = payload.project_id,
            sprint_id           = payload.sprint_id,
        )
        db.add(task)
        created_tasks.append(task)

    await db.flush()
    for t in created_tasks:
        await db.refresh(t)
    return created_tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_or_404(db, task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_or_404(db, task_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    await db.flush()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    task = await _get_or_404(db, task_id)
    await db.delete(task)
    await db.flush()


# ─── Helper ──────────────────────────────────────────────────────────────────
async def _get_or_404(db: AsyncSession, task_id: int) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task   = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
