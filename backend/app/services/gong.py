import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.scheduling_link import GongInvite
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)

GONG_EMAIL = "circle@assistant.gong.io"


def is_teams_meeting(event: dict) -> bool:
    """Detect if a Google Calendar event is a Microsoft Teams meeting."""
    location = event.get("location", "") or ""
    description = event.get("description", "") or ""
    conf_name = (
        event.get("conferenceData", {})
        .get("conferenceSolution", {})
        .get("name", "")
    ) or ""

    if "teams.microsoft.com" in location:
        return True
    if "https://teams.microsoft.com/l/meetup-join/" in description:
        return True
    if conf_name.lower() == "microsoft teams":
        return True
    return False


async def ensure_gong_invited(
    event: dict,
    cal_service: GoogleCalendarService,
    user_id: int,
    db: AsyncSession,
) -> bool:
    """Add Gong as attendee if not already present. Returns True if added."""
    event_id = event.get("id")

    # Check deduplication table
    result = await db.execute(
        select(GongInvite).where(
            GongInvite.user_id == user_id,
            GongInvite.google_event_id == event_id,
        )
    )
    if result.scalar_one_or_none():
        return False  # Already processed

    attendees = list(event.get("attendees", []))
    if any(a.get("email") == GONG_EMAIL for a in attendees):
        # Already invited — record in DB to avoid future checks
        db.add(GongInvite(user_id=user_id, google_event_id=event_id))
        await db.commit()
        return False

    attendees.append({"email": GONG_EMAIL})
    try:
        cal_service.patch_event(
            event_id,
            {"attendees": attendees},
            send_updates="all",
        )
        db.add(GongInvite(user_id=user_id, google_event_id=event_id))
        await db.commit()
        logger.info(f"Added Gong to event {event_id} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to add Gong to event {event_id}: {e}")
        return False


async def sync_gong_for_user(
    user_id: int,
    db: AsyncSession,
    cal_service: GoogleCalendarService,
) -> dict:
    """Scan upcoming calendar for Teams meetings and auto-invite Gong."""
    now = datetime.now(timezone.utc)
    look_ahead = now + timedelta(days=14)

    events = cal_service.list_events(now, look_ahead)
    teams_meetings = [e for e in events if is_teams_meeting(e)]

    added = 0
    for event in teams_meetings:
        was_added = await ensure_gong_invited(event, cal_service, user_id, db)
        if was_added:
            added += 1

    return {
        "teams_meetings_found": len(teams_meetings),
        "gong_invites_added": added,
    }
