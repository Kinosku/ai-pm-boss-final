from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from database import init_db

from routers import (
    auth,
    projects,
    tasks,
    sprints,
    pull_requests,
    risk_alerts,
    standups,
    reports,
    team,
    notifications,
    integrations,
    settings as settings_router,
    dashboard,
    agents,
)
from webhooks import github, slack, jira


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous AI Project Manager for Software Teams",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router,           prefix="/api/auth",          tags=["Auth"])
app.include_router(projects.router,       prefix="/api/projects",      tags=["Projects"])
app.include_router(tasks.router,          prefix="/api/tasks",         tags=["Tasks"])
app.include_router(sprints.router,        prefix="/api/sprints",       tags=["Sprints"])
app.include_router(pull_requests.router,  prefix="/api/pull-requests", tags=["Pull Requests"])
app.include_router(risk_alerts.router,    prefix="/api/risks",         tags=["Risk Alerts"])
app.include_router(standups.router,       prefix="/api/standups",      tags=["Standups"])
app.include_router(reports.router,        prefix="/api/reports",       tags=["Reports"])
app.include_router(team.router,           prefix="/api/team",          tags=["Team"])
app.include_router(notifications.router,  prefix="/api/notifications", tags=["Notifications"])
app.include_router(integrations.router,   prefix="/api/integrations",  tags=["Integrations"])
app.include_router(settings_router.router,prefix="/api/settings",      tags=["Settings"])
app.include_router(dashboard.router,      prefix="/api/dashboard",     tags=["Dashboard"])
app.include_router(agents.router,         prefix="/api/agents",        tags=["Agents"])

# ─── Webhooks ────────────────────────────────────────────────────────────────
app.include_router(github.router, prefix="/webhooks/github", tags=["Webhooks"])
app.include_router(slack.router,  prefix="/webhooks/slack",  tags=["Webhooks"])
app.include_router(jira.router,   prefix="/webhooks/jira",   tags=["Webhooks"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
