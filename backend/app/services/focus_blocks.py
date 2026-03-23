import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.preferences import UserPreferences
from app.services.google_calendar import GoogleCalendarService
from app.services.claude import get_optimization_plan
from app.utils.time_utils import parse_iso

logger = logging.getLogger(__name__)


async def run_optimization(
    user_id: int,
    db: AsyncSession,
    cal_service: GoogleCalendarService,
    preferences: UserPreferences,
) -> dict:
    """
    1. Fetch next-7-days events from Google Calendar
    2. Ask Claude for a plan
    3. Execute the plan (create/delete focus blocks, optionally move meetings)
    4. Return summary
    """
    now = datetime.now(timezone.utc)
    week_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    week_end = now + timedelta(days=7)

    events = cal_service.list_events(now, week_end)
    existing_focus_blocks = cal_service.list_focus_blocks(now, week_end)

    plan = await get_optimization_plan(preferences, events, existing_focus_blocks, now)
    logger.info(f"Claude plan for user {user_id}: {plan.get('summary', '')}")

    created_blocks = []
    removed_blocks = []
    suggestions = []

    # Remove stale focus blocks
    for removal in plan.get("focus_blocks_to_remove", []):
        try:
            cal_service.delete_event(removal["event_id"])
            removed_blocks.append(removal["event_id"])
            logger.info(f"Deleted focus block {removal['event_id']}: {removal.get('reasoning')}")
        except Exception as e:
            logger.warning(f"Failed to delete focus block {removal['event_id']}: {e}")

    # Create new focus blocks
    for block in plan.get("focus_blocks_to_create", []):
        try:
            start = parse_iso(block["start"])
            end = parse_iso(block["end"])
            created = cal_service.create_focus_block(start, end)
            created_blocks.append(created.get("id"))
            logger.info(f"Created focus block {created.get('id')}: {block.get('reasoning')}")
        except Exception as e:
            logger.warning(f"Failed to create focus block: {e}")

    # Handle meeting move suggestions
    if preferences.allow_auto_move_meetings:
        for suggestion in plan.get("meeting_move_suggestions", []):
            try:
                new_start = parse_iso(suggestion["suggested_start"])
                # Calculate duration from current event
                event = cal_service.get_event(suggestion["event_id"])
                current_start = parse_iso(event["start"]["dateTime"])
                current_end = parse_iso(event["end"]["dateTime"])
                duration = current_end - current_start
                new_end = new_start + duration

                cal_service.patch_event(
                    suggestion["event_id"],
                    {
                        "start": {"dateTime": new_start.isoformat()},
                        "end": {"dateTime": new_end.isoformat()},
                    },
                    send_updates="all",
                )
                logger.info(f"Moved meeting {suggestion['event_id']}: {suggestion.get('reasoning')}")
            except Exception as e:
                logger.warning(f"Failed to move meeting {suggestion.get('event_id')}: {e}")
    else:
        # Store suggestions for dashboard review
        suggestions = plan.get("meeting_move_suggestions", [])

    return {
        "summary": plan.get("summary", ""),
        "focus_blocks_created": len(created_blocks),
        "focus_blocks_removed": len(removed_blocks),
        "meeting_suggestions": suggestions,
    }
