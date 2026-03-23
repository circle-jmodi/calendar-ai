import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.routers import auth, calendar, preferences, optimization, scheduling, slack_bot, setup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start APScheduler (dev mode)
    if settings.environment == "development":
        from app.services.optimization_job import run_optimization_for_all_users, sync_all_slack_statuses

        scheduler.add_job(
            run_optimization_for_all_users,
            CronTrigger(day_of_week="mon-fri", hour=6, minute=0),
            id="daily_optimization",
            replace_existing=True,
        )
        scheduler.add_job(
            sync_all_slack_statuses,
            IntervalTrigger(minutes=5),
            id="slack_status_sync",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler started: daily optimization at 6 AM, Slack sync every 5 min")

    yield

    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title="Calendar AI — Clockwise Replacement",
    version="1.0.0",
    lifespan=lifespan,
)

# Session middleware (cookie-based)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="calai_session",
    https_only=settings.environment == "production",
    same_site="lax",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(setup.router)
app.include_router(auth.router)
app.include_router(calendar.router)
app.include_router(preferences.router)
app.include_router(optimization.router)
app.include_router(scheduling.router)
app.include_router(slack_bot.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
