from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.models.preferences import UserPreferences

router = APIRouter(prefix="/preferences", tags=["preferences"])


def require_user(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    return user_id


class PreferencesUpdate(BaseModel):
    focus_hours_per_day: Optional[int] = None
    focus_days_per_week: Optional[int] = None
    focus_preferred_time: Optional[str] = None
    focus_min_block_minutes: Optional[int] = None
    focus_max_block_minutes: Optional[int] = None
    work_start_hour: Optional[int] = None
    work_end_hour: Optional[int] = None
    work_timezone: Optional[str] = None
    work_days: Optional[List[int]] = None
    meeting_buffer_minutes: Optional[int] = None
    allow_auto_move_meetings: Optional[bool] = None
    no_meeting_days: Optional[List[int]] = None
    slack_status_sync_enabled: Optional[bool] = None
    slack_focus_status_text: Optional[str] = None
    slack_focus_status_emoji: Optional[str] = None
    gong_auto_record_enabled: Optional[bool] = None


@router.get("")
async def get_preferences(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = require_user(request)
    result = await db.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        # Return defaults
        prefs = UserPreferences(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return prefs


@router.put("")
async def update_preferences(
    request: Request,
    body: PreferencesUpdate,
    db: AsyncSession = Depends(get_db),
):
    user_id = require_user(request)
    result = await db.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        db.add(prefs)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)
    return prefs
