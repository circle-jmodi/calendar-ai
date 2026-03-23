import json
import logging
from datetime import datetime
from anthropic import AsyncAnthropic
from app.config import settings
from app.models.preferences import UserPreferences

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are a calendar optimization assistant. Your job is to analyze a user's calendar and create an optimal schedule.

You MUST respond with ONLY valid JSON — no markdown, no explanation, no code blocks. Just raw JSON.

Return exactly this structure:
{
  "focus_blocks_to_create": [
    {"start": "<ISO8601 UTC datetime>", "end": "<ISO8601 UTC datetime>", "reasoning": "<why>"}
  ],
  "focus_blocks_to_remove": [
    {"event_id": "<google event id>", "reasoning": "<why>"}
  ],
  "meeting_move_suggestions": [
    {
      "event_id": "<google event id>",
      "current_start": "<ISO8601>",
      "suggested_start": "<ISO8601>",
      "reasoning": "<why this move reduces fragmentation>"
    }
  ],
  "summary": "<2-3 sentence plain English explanation of the plan>"
}

Rules:
- Only create focus blocks during work hours on work days
- Do not create focus blocks during existing meetings
- Respect no-meeting days — suggest moving meetings away from those days
- Try to consolidate meetings together to create larger contiguous focus blocks
- Respect the user's focus_preferred_time (morning = before noon, afternoon = after noon)
- Focus blocks should be between focus_min_block_minutes and focus_max_block_minutes long
- Total focus block time per day should not exceed focus_hours_per_day
- Leave at least meeting_buffer_minutes before/after each meeting
- If allow_auto_move_meetings is false, only suggest moves, don't assume they'll be applied
"""


async def get_optimization_plan(
    preferences: UserPreferences,
    events: list[dict],
    existing_focus_blocks: list[dict],
    current_datetime: datetime,
) -> dict:
    """Call Claude to get an optimization plan. Returns parsed JSON dict."""

    events_summary = []
    for e in events:
        start = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date", "")
        end = e.get("end", {}).get("dateTime") or e.get("end", {}).get("date", "")
        is_focus = e.get("extendedProperties", {}).get("private", {}).get("type") == "focus-block"
        attendee_count = len(e.get("attendees", []))
        events_summary.append({
            "id": e.get("id"),
            "title": e.get("summary", "No title"),
            "start": start,
            "end": end,
            "is_focus_block": is_focus,
            "attendee_count": attendee_count,
            "is_recurring": bool(e.get("recurringEventId")),
        })

    focus_blocks_summary = [
        {
            "id": b.get("id"),
            "start": b.get("start", {}).get("dateTime"),
            "end": b.get("end", {}).get("dateTime"),
        }
        for b in existing_focus_blocks
    ]

    user_message = f"""Current date/time (UTC): {current_datetime.isoformat()}

User preferences:
- Work hours: {preferences.work_start_hour}:00 - {preferences.work_end_hour}:00 {preferences.work_timezone}
- Work days (0=Mon, 6=Sun): {preferences.work_days}
- No-meeting days: {preferences.no_meeting_days}
- Focus goal: {preferences.focus_hours_per_day} hours/day, {preferences.focus_days_per_week} days/week
- Preferred focus time: {preferences.focus_preferred_time}
- Min focus block: {preferences.focus_min_block_minutes} min, Max: {preferences.focus_max_block_minutes} min
- Meeting buffer: {preferences.meeting_buffer_minutes} min
- Auto-move meetings: {preferences.allow_auto_move_meetings}

Calendar events for next 7 days:
{json.dumps(events_summary, indent=2)}

Existing app-managed focus blocks:
{json.dumps(focus_blocks_summary, indent=2)}

Please optimize this calendar. Return ONLY JSON."""

    logger.info("Sending optimization request to Claude")
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    logger.info(f"Claude response: {raw[:500]}...")

    plan = json.loads(raw)
    return plan
