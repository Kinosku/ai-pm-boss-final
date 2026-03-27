from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date

from database import get_db
from models.standup import Standup, StandupStatus
from models.user import User
from schemas.standup import (
    StandupCreate, StandupUpdate, StandupResponse,
    StandupSlackUpdate, StandupSummaryResponse, StandupTriggerRequest,
)
from routers.auth import get_current_user, require_boss
from services.slack_parser import slack_parser
from ai.llm import invoke_llm_json, load_prompt

router = APIRouter()


@router.get("/", response_model=List[StandupResponse])
async def list_standups(
    project_id:  Optional[int]  = Query(None),
    sprint_id:   Optional[int]  = Query(None),
    developer_id:Optional[int]  = Query(None),
    is_summary:  Optional[bool] = Query(None),
    db: AsyncSession             = Depends(get_db),
    current_user: User           = Depends(get_current_user),
):
    q = select(Standup)
    if project_id:   q = q.where(Standup.project_id   == project_id)
    if sprint_id:    q = q.where(Standup.sprint_id    == sprint_id)
    if developer_id: q = q.where(Standup.developer_id == developer_id)
    if is_summary is not None: q = q.where(Standup.is_summary == is_summary)
    result = await db.execute(q.order_by(Standup.standup_date.desc()))
    return result.scalars().all()


@router.post("/", response_model=StandupResponse, status_code=status.HTTP_201_CREATED)
async def submit_standup(
    payload: StandupCreate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Developer submits their daily standup update."""
    standup = Standup(**payload.model_dump(), status=StandupStatus.COLLECTED)
    db.add(standup)
    await db.flush()
    await db.refresh(standup)
    return standup


@router.post("/slack-update", response_model=StandupResponse)
async def submit_standup_from_slack(
    payload: StandupSlackUpdate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Parse a raw Slack message into a standup update."""
    parsed = slack_parser._parse_standup_message(payload.raw_message, payload.slack_user_id)

    standup = Standup(
        project_id   = payload.project_id,
        developer_id = payload.developer_id,
        standup_date = datetime.utcnow(),
        done         = parsed.get("done", []),
        doing        = parsed.get("doing", []),
        blocked      = parsed.get("blocked", []),
        raw_message  = payload.raw_message,
        slack_channel= payload.channel_id,
        status       = StandupStatus.COLLECTED,
    )
    db.add(standup)
    await db.flush()
    await db.refresh(standup)
    return standup


@router.post("/generate-summary", response_model=StandupSummaryResponse)
async def generate_standup_summary(
    payload: StandupTriggerRequest,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    """AI: collect today's standup updates and generate a Slack summary."""
    today_start = datetime.combine(date.today(), datetime.min.time())

    result = await db.execute(
        select(Standup).where(
            Standup.project_id   == payload.project_id,
            Standup.standup_date >= today_start,
            Standup.is_summary   == False,
        )
    )
    updates = result.scalars().all()

    if not updates:
        raise HTTPException(status_code=404, detail="No standup updates found for today")

    # Format dev updates for the prompt
    dev_updates_text = "\n\n".join([
        f"Developer ID {u.developer_id}:\n"
        f"  Done: {', '.join(u.done) or 'N/A'}\n"
        f"  Doing: {', '.join(u.doing) or 'N/A'}\n"
        f"  Blocked: {', '.join(u.blocked) or 'None'}"
        for u in updates
    ])

    system_prompt = load_prompt("standup_prompt.txt").format(
        project_name      = "Project",
        standup_date      = str(date.today()),
        sprint_name       = f"Sprint (ID {payload.sprint_id})" if payload.sprint_id else "Current Sprint",
        sprint_day        = "N/A",
        sprint_total_days = "N/A",
        sprint_health_score = "N/A",
        developer_updates = dev_updates_text,
    )

    summary_data = await invoke_llm_json(system_prompt, "Generate the standup summary.")

    # Persist summary row
    summary = Standup(
        project_id    = payload.project_id,
        sprint_id     = payload.sprint_id,
        standup_date  = datetime.utcnow(),
        is_summary    = True,
        summary_text  = summary_data.get("summary_text", ""),
        blockers_json = summary_data.get("blockers", []),
        slack_channel = payload.channel_id,
        status        = StandupStatus.POSTED,
    )
    db.add(summary)
    await db.flush()

    return StandupSummaryResponse(**summary_data, slack_channel=payload.channel_id)


@router.get("/{standup_id}", response_model=StandupResponse)
async def get_standup(
    standup_id: int,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Standup).where(Standup.id == standup_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Standup not found")
    return s
