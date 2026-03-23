import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.preferences import UserPreferences
from app.services.google_calendar import GoogleCalendarService, get_valid_google_credentials
from app.services.focus_blocks import run_optimization
from app.services.slack import sync_slack_status_for_user
from app.services.gong import sync_gong_for_user

logger = logging.getLogger(__name__)


async def run_optimization_for_all_users() -> None:
    """Called by APScheduler or Cloud Scheduler at 6 AM daily."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

    for user in users:
        try:
            async with AsyncSessionLocal() as db:
                await run_optimization_for_user(user.id, db)
        except Exception as e:
            logger.error(f"Optimization failed for user {user.id}: {e}", exc_info=True)


async def run_optimization_for_user(user_id: int, db: AsyncSession) -> dict:
    creds = await get_valid_google_credentials(user_id, db)
    if not creds:
        logger.warning(f"No Google credentials for user {user_id}, skipping optimization")
        return {"error": "No Google credentials"}

    cal_service = GoogleCalendarService(creds)

    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    preferences = result.scalar_one_or_none()
    if not preferences:
        # Create defaults
        preferences = UserPreferences(user_id=user_id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)

    plan_result = await run_optimization(user_id, db, cal_service, preferences)

    # Sync Gong for Teams meetings
    if preferences.gong_auto_record_enabled:
        await sync_gong_for_user(user_id, db, cal_service)

    return plan_result


async def sync_all_slack_statuses() -> None:
    """Called every 5 minutes by APScheduler."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

    for user in users:
        try:
            async with AsyncSessionLocal() as db:
                creds = await get_valid_google_credentials(user.id, db)
                if not creds:
                    continue
                cal_service = GoogleCalendarService(creds)
                result = await db.execute(
                    select(UserPreferences).where(UserPreferences.user_id == user.id)
                )
                prefs = result.scalar_one_or_none()
                if prefs:
                    await sync_slack_status_for_user(user.id, db, cal_service, prefs)
        except Exception as e:
            logger.error(f"Slack sync failed for user {user.id}: {e}", exc_info=True)
