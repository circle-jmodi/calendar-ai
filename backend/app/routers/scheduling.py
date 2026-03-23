import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.database import get_db
from app.models.scheduling_link import SchedulingLink
from app.models.preferences import UserPreferences
from app.services.google_calendar import GoogleCalendarService, get_valid_google_credentials
from app.services.scheduling_link import compute_available_slots, book_slot
from app.utils.time_utils import parse_iso

router = APIRouter(prefix="/schedule", tags=["scheduling"])


def require_user(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    return user_id


class LinkCreate(BaseModel):
    title: str
    duration_minutes: int = 30
    buffer_before: int = 0
    buffer_after: int = 0
    rolling_days_available: int = 14
    custom_availability: Optional[dict] = None
    questions: Optional[List[dict]] = None
    slug: Optional[str] = None


class BookingRequest(BaseModel):
    slot_start: str  # ISO8601
    slot_end: str
    name: str
    email: str
    answers: Optional[dict] = None


@router.get("/links")
async def list_links(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = require_user(request)
    result = await db.execute(select(SchedulingLink).where(SchedulingLink.user_id == user_id))
    return {"links": result.scalars().all()}


@router.post("/links")
async def create_link(request: Request, body: LinkCreate, db: AsyncSession = Depends(get_db)):
    user_id = require_user(request)
    slug = body.slug or secrets.token_urlsafe(8)

    # Ensure slug is unique
    existing = await db.execute(select(SchedulingLink).where(SchedulingLink.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Slug '{slug}' already taken")

    link = SchedulingLink(
        user_id=user_id,
        slug=slug,
        title=body.title,
        duration_minutes=body.duration_minutes,
        buffer_before=body.buffer_before,
        buffer_after=body.buffer_after,
        rolling_days_available=body.rolling_days_available,
        custom_availability=body.custom_availability,
        questions=body.questions or [],
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


@router.put("/links/{link_id}")
async def update_link(
    request: Request,
    link_id: int,
    body: LinkCreate,
    db: AsyncSession = Depends(get_db),
):
    user_id = require_user(request)
    result = await db.execute(select(SchedulingLink).where(SchedulingLink.id == link_id, SchedulingLink.user_id == user_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "Link not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(link, field, value)
    await db.commit()
    await db.refresh(link)
    return link


@router.delete("/links/{link_id}")
async def delete_link(request: Request, link_id: int, db: AsyncSession = Depends(get_db)):
    user_id = require_user(request)
    result = await db.execute(select(SchedulingLink).where(SchedulingLink.id == link_id, SchedulingLink.user_id == user_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "Link not found")
    await db.delete(link)
    await db.commit()
    return {"ok": True}


# --- Public booking endpoints (no auth required) ---

async def _get_link_and_prefs(slug: str, db: AsyncSession):
    result = await db.execute(select(SchedulingLink).where(SchedulingLink.slug == slug, SchedulingLink.active == True))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "Scheduling link not found or inactive")

    result2 = await db.execute(select(UserPreferences).where(UserPreferences.user_id == link.user_id))
    prefs = result2.scalar_one_or_none()
    if not prefs:
        prefs = UserPreferences(user_id=link.user_id)

    return link, prefs


@router.get("/{slug}")
async def get_public_link(slug: str, db: AsyncSession = Depends(get_db)):
    link, _ = await _get_link_and_prefs(slug, db)
    return {
        "slug": link.slug,
        "title": link.title,
        "duration_minutes": link.duration_minutes,
        "questions": link.questions,
    }


@router.get("/{slug}/availability")
async def get_availability(slug: str, db: AsyncSession = Depends(get_db)):
    link, prefs = await _get_link_and_prefs(slug, db)
    creds = await get_valid_google_credentials(link.user_id, db)
    if not creds:
        raise HTTPException(503, "Host's calendar is temporarily unavailable")

    cal = GoogleCalendarService(creds)
    slots = compute_available_slots(link, prefs, cal)
    return {"slots": slots}


@router.post("/{slug}/book")
async def book(slug: str, body: BookingRequest, db: AsyncSession = Depends(get_db)):
    link, prefs = await _get_link_and_prefs(slug, db)
    creds = await get_valid_google_credentials(link.user_id, db)
    if not creds:
        raise HTTPException(503, "Host's calendar is temporarily unavailable")

    cal = GoogleCalendarService(creds)

    # Race-condition guard: re-check availability
    slot_start = parse_iso(body.slot_start)
    slot_end = parse_iso(body.slot_end)
    available_slots = compute_available_slots(link, prefs, cal)
    slot_starts = {s["start"] for s in available_slots}
    if body.slot_start not in slot_starts:
        raise HTTPException(409, "This slot is no longer available. Please choose another time.")

    event = book_slot(link, prefs, cal, slot_start, slot_end, body.name, body.email, body.answers)
    return {"event_id": event.get("id"), "message": "Booking confirmed!"}
