"""
Celery Application
Configures the Celery worker that processes AI agent jobs
from the Redis queue asynchronously.
"""
from celery import Celery
from celery.schedules import crontab

from core.config import settings

# ─── App ──────────────────────────────────────────────────────────────────────
celery_app = Celery(
    "ai_pm_boss",
    broker  = settings.CELERY_BROKER_URL,
    backend = settings.CELERY_RESULT_BACKEND,
    include = ["workers.tasks"],
)

# ─── Config ───────────────────────────────────────────────────────────────────
celery_app.conf.update(
    task_serializer        = "json",
    result_serializer      = "json",
    accept_content         = ["json"],
    timezone               = "UTC",
    enable_utc             = True,
    task_track_started     = True,
    task_acks_late         = True,          # re-queue on worker crash
    worker_prefetch_multiplier = 1,         # one task at a time per worker
    task_routes = {
        "workers.tasks.run_task_creator":    {"queue": "task_creation"},
        "workers.tasks.run_pr_mapper":       {"queue": "pr_mapping"},
        "workers.tasks.run_delay_predictor": {"queue": "risk_detection"},
        "workers.tasks.run_report_generator":{"queue": "report_generation"},
        "workers.tasks.run_standup_bot":     {"queue": "standup_bot"},
        "workers.tasks.send_notification":   {"queue": "notifications"},
    },
)

# ─── Beat schedule (periodic tasks) ──────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Daily standup bot — 9:00 AM UTC every weekday
    "daily-standup": {
        "task":     "workers.tasks.scheduled_standup",
        "schedule": crontab(hour=9, minute=0, day_of_week="mon-fri"),
    },
    # Weekly report — Friday 5:00 PM UTC
    "weekly-report": {
        "task":     "workers.tasks.scheduled_weekly_report",
        "schedule": crontab(hour=17, minute=0, day_of_week="fri"),
    },
    # Risk detection — every 4 hours on weekdays
    "periodic-risk-check": {
        "task":     "workers.tasks.scheduled_risk_check",
        "schedule": crontab(hour="*/4", day_of_week="mon-fri"),
    },
    # Mark stale PRs — every 6 hours
    "mark-stale-prs": {
        "task":     "workers.tasks.mark_stale_pull_requests",
        "schedule": crontab(hour="*/6"),
    },
}
