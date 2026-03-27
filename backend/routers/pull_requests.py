from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from database import get_db
from models.pull_request import PullRequest, PRStatus
from models.user import User
from schemas.pull_request import (
    PullRequestCreate, PullRequestUpdate,
    PullRequestResponse, PullRequestSummary,
)
from routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[PullRequestResponse])
async def list_pull_requests(
    project_id: Optional[int]   = Query(None),
    status:     Optional[PRStatus] = Query(None),
    author_id:  Optional[int]   = Query(None),
    is_stale:   Optional[bool]  = Query(None),
    db: AsyncSession             = Depends(get_db),
    current_user: User           = Depends(get_current_user),
):
    q = select(PullRequest)
    if project_id: q = q.where(PullRequest.project_id == project_id)
    if status:     q = q.where(PullRequest.status     == status)
    if author_id:  q = q.where(PullRequest.author_id  == author_id)
    if is_stale is not None: q = q.where(PullRequest.is_stale == is_stale)
    result = await db.execute(q.order_by(PullRequest.opened_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=PullRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_pull_request(
    payload: PullRequestCreate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pr = PullRequest(**payload.model_dump())
    db.add(pr)
    await db.flush()
    await db.refresh(pr)
    return pr


@router.get("/my", response_model=List[PullRequestSummary])
async def my_pull_requests(
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employee: fetch my own PRs."""
    from models.developer import Developer
    dev_result = await db.execute(
        select(Developer).where(Developer.user_id == current_user.id)
    )
    dev = dev_result.scalar_one_or_none()
    if not dev:
        return []

    result = await db.execute(
        select(PullRequest)
        .where(PullRequest.author_id == dev.id)
        .order_by(PullRequest.opened_at.desc())
    )
    return result.scalars().all()


@router.get("/{pr_id}", response_model=PullRequestResponse)
async def get_pull_request(
    pr_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_or_404(db, pr_id)


@router.patch("/{pr_id}", response_model=PullRequestResponse)
async def update_pull_request(
    pr_id: int,
    payload: PullRequestUpdate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pr = await _get_or_404(db, pr_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(pr, field, value)
    await db.flush()
    await db.refresh(pr)
    return pr


@router.get("/stale/list", response_model=List[PullRequestSummary])
async def get_stale_prs(
    project_id: Optional[int] = Query(None),
    db: AsyncSession           = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """Return PRs open > 48 hours — used by risk engine."""
    q = select(PullRequest).where(
        PullRequest.is_stale == True,
        PullRequest.status   == PRStatus.OPEN,
    )
    if project_id:
        q = q.where(PullRequest.project_id == project_id)
    result = await db.execute(q.order_by(PullRequest.opened_at.asc()))
    return result.scalars().all()


# ─── Helper ──────────────────────────────────────────────────────────────────
async def _get_or_404(db: AsyncSession, pr_id: int) -> PullRequest:
    result = await db.execute(select(PullRequest).where(PullRequest.id == pr_id))
    pr     = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return pr
