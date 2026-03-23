from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.preferences import UserPreferences
from app.services.google_calendar import GoogleCalendarService, get_valid_google_credentials
from app.services.gong import sync_gong_for_user

router = APIRouter(prefix="/calendar", tags=["calendar"])


def require_user(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    return user_id


@router.get("/events")
async def get_events(
    request: Request,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    user_id = require_user(request)
    creds = await get_valid_google_credentials(user_id, db)
    if not creds:
        raise HTTPException(400, "Google Calendar not connected")

    cal = GoogleCalendarService(creds)
    now = datetime.now(timezone.utc)
    events = cal.list_events(now, now + timedelta(days=days))
    return {"events": events}


@router.get("/focus-blocks")
async def get_focus_blocks(
    request: Request,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    user_id = require_user(request)
    creds = await get_valid_google_credentials(user_id, db)
    if not creds:
        raise HTTPException(400, "Google Calendar not connected")

    cal = GoogleCalendarService(creds)
    now = datetime.now(timezone.utc)
    blocks = cal.list_focus_blocks(now, now + timedelta(days=days))
    return {"focus_blocks": blocks}


@router.post("/focus-blocks/generate")
async def generate_focus_blocks(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger optimization / focus block generation."""
    user_id = require_user(request)
    from app.services.optimization_job import run_optimization_for_user
    result = await run_optimization_for_user(user_id, db)
    return result


@router.get("/suggestions")
async def get_suggestions(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Return meeting move suggestions from the last optimization run.
    Currently stored in-memory per session; a production implementation
    would persist these in DB.
    """
    # For now, trigger a fresh analysis and return suggestions without applying
    user_id = require_user(request)
    creds = await get_valid_google_credentials(user_id, db)
    if not creds:
        raise HTTPException(400, "Google Calendar not connected")

    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    preferences = result.scalar_one_or_none()
    if not preferences:
        preferences = UserPreferences(user_id=user_id)

    from datetime import timedelta
    cal = GoogleCalendarService(creds)
    now = datetime.now(timezone.utc)
    events = cal.list_events(now, now + timedelta(days=7))
    existing_blocks = cal.list_focus_blocks(now, now + timedelta(days=7))

    from app.services.claude import get_optimization_plan
    plan = await get_optimization_plan(preferences, events, existing_blocks, now)

    return {"suggestions": plan.get("meeting_move_suggestions", []), "summary": plan.get("summary", "")}


@router.post("/suggestions/{event_id}/accept")
async def accept_suggestion(
    request: Request,
    event_id: str,
    suggested_start: str,
    db: AsyncSession = Depends(get_db),
):
    user_id = require_user(request)
    creds = await get_valid_google_credentials(user_id, db)
    if not creds:
        raise HTTPException(400, "Google Calendar not connected")

    cal = GoogleCalendarService(creds)
    event = cal.get_event(event_id)

    from app.utils.time_utils import parse_iso
    new_start = parse_iso(suggested_start)
    current_start = parse_iso(event["start"]["dateTime"])
    current_end = parse_iso(event["end"]["dateTime"])
    duration = current_end - current_start
    new_end = new_start + duration

    updated = cal.patch_event(
        event_id,
        {
            "start": {"dateTime": new_start.isoformat()},
            "end": {"dateTime": new_end.isoformat()},
        },
        send_updates="all",
    )
    return {"event": updated}


@router.post("/sync-gong")
async def sync_gong(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = require_user(request)
    creds = await get_valid_google_credentials(user_id, db)
    if not creds:
        raise HTTPException(400, "Google Calendar not connected")

    cal = GoogleCalendarService(creds)
    result = await sync_gong_for_user(user_id, db, cal)
    return result
