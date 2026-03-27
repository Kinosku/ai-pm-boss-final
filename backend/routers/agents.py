from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.user import User
from ai.orchestrator import orchestrator, OrchestratorEvent
from ai.memory import AgentName, get_history, load_memory
from routers.auth import get_current_user, require_boss

router = APIRouter()


# ─── Request schemas ──────────────────────────────────────────────────────────
class AgentTriggerRequest(BaseModel):
    project_id:  int
    agent:       str
    prd_text:    Optional[str] = None
    pr_id:       Optional[int] = None
    sprint_id:   Optional[int] = None
    channel_id:  Optional[str] = None
    report_type: Optional[str] = "weekly"


# ─── Agent status snapshot ────────────────────────────────────────────────────
AGENT_REGISTRY = [
    {
        "name":        AgentName.TASK_CREATOR,
        "display":     "Task Creator Agent",
        "description": "Reads PRDs and Slack messages → auto-creates Jira tasks",
        "icon":        "task_alt",
    },
    {
        "name":        AgentName.PR_MAPPER,
        "display":     "PR Mapping Agent",
        "description": "Links GitHub PRs → Jira tasks automatically based on title tags",
        "icon":        "merge_type",
    },
    {
        "name":        AgentName.DELAY_PREDICTOR,
        "display":     "Delay Prediction Agent",
        "description": "Monitors velocity and predicts potential delays 1–2 weeks early",
        "icon":        "trending_down",
    },
    {
        "name":        AgentName.REPORT_GENERATOR,
        "display":     "Report Generator Agent",
        "description": "Generates weekly status reports → sends to Slack/email automatically",
        "icon":        "analytics",
    },
    {
        "name":        AgentName.STANDUP_BOT,
        "display":     "Standup Bot",
        "description": "Collects async standup updates → posts daily summary to Slack",
        "icon":        "record_voice_over",
    },
]


@router.get("/")
async def list_agents(
    project_id:  Optional[int] = None,
    current_user: User          = Depends(get_current_user),
):
    """AI Agents page — list all agents with status."""
    return {"agents": AGENT_REGISTRY}


@router.get("/{agent_name}/status")
async def get_agent_status(
    agent_name: str,
    project_id: int,
    current_user: User = Depends(get_current_user),
):
    """Get memory + recent history for a specific agent."""
    memory  = await load_memory(project_id, agent_name)
    history = await get_history(project_id, agent_name, limit=5)

    agent_info = next((a for a in AGENT_REGISTRY if a["name"] == agent_name), None)
    if not agent_info:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent":   agent_info,
        "memory":  memory,
        "history": history,
    }


@router.post("/trigger")
async def trigger_agent(
    payload: AgentTriggerRequest,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(require_boss),
):
    """
    Manual trigger from the AI Agents page.
    Maps to the "Run" buttons on each agent card.
    """
    agent_payloads = {
        AgentName.TASK_CREATOR:    {"agent": AgentName.TASK_CREATOR,    "prd_text":    payload.prd_text or ""},
        AgentName.PR_MAPPER:       {"agent": AgentName.PR_MAPPER,       "pr_id":       payload.pr_id},
        AgentName.DELAY_PREDICTOR: {"agent": AgentName.DELAY_PREDICTOR, "sprint_id":   payload.sprint_id},
        AgentName.REPORT_GENERATOR:{"agent": AgentName.REPORT_GENERATOR,"report_type": payload.report_type},
        AgentName.STANDUP_BOT:     {"agent": AgentName.STANDUP_BOT,     "channel_id":  payload.channel_id or ""},
    }

    if payload.agent not in agent_payloads:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {payload.agent}")

    result = await orchestrator.handle_event(
        event      = OrchestratorEvent.MANUAL_TRIGGER,
        project_id = payload.project_id,
        payload    = agent_payloads[payload.agent],
    )
    return {"status": "dispatched", "result": result}


@router.post("/run-standup")
async def run_standup(
    project_id: int,
    channel_id: str,
    current_user: User = Depends(require_boss),
):
    """Shortcut for the 'Run Standup Bot' button on the Boss Dashboard."""
    result = await orchestrator.handle_event(
        event      = OrchestratorEvent.DAILY_STANDUP_TIME,
        project_id = project_id,
        payload    = {"channel_id": channel_id},
    )
    return {"status": "dispatched", "result": result}


@router.post("/generate-report")
async def generate_report(
    project_id:  int,
    report_type: str = "weekly",
    current_user: User = Depends(require_boss),
):
    """Shortcut for the 'Generate Report' button on the Boss Dashboard."""
    result = await orchestrator.handle_event(
        event      = OrchestratorEvent.WEEKLY_REPORT_TIME,
        project_id = project_id,
        payload    = {"report_type": report_type},
    )
    return {"status": "dispatched", "result": result}
