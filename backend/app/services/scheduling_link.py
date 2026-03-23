from datetime import datetime, timedelta, date, time
from typing import Any
import pytz
from app.models.scheduling_link import SchedulingLink
from app.models.preferences import UserPreferences
from app.services.google_calendar import GoogleCalendarService
from app.utils.time_utils import combine_local, parse_iso


def compute_available_slots(
    link: SchedulingLink,
    prefs: UserPreferences,
    cal_service: GoogleCalendarService,
) -> list[dict[str, str]]:
    """Return [{start, end}] ISO8601 UTC strings of available booking slots."""
    tz = pytz.timezone(prefs.work_timezone)
    now = datetime.now(pytz.utc)
    end_date = now + timedelta(days=link.rolling_days_available)

    # Fetch all busy events
    events = cal_service.list_events(now, end_date)
    busy: list[tuple[datetime, datetime]] = []
    for e in events:
        start_str = e.get("start", {}).get("dateTime")
        end_str = e.get("end", {}).get("dateTime")
        if not start_str or not end_str:
            continue
        s = parse_iso(start_str)
        en = parse_iso(end_str)
        # Expand by buffers
        busy.append((
            s - timedelta(minutes=link.buffer_before),
            en + timedelta(minutes=link.buffer_after),
        ))

    slots = []
    current_date = now.date()

    while current_date < end_date.date():
        weekday = current_date.weekday()  # 0=Mon

        # Check work days
        work_days = prefs.work_days if prefs.work_days else [0, 1, 2, 3, 4]
        if weekday not in work_days:
            current_date += timedelta(days=1)
            continue

        # Use custom availability if set for this weekday
        if link.custom_availability and str(weekday) in link.custom_availability:
            day_avail = link.custom_availability[str(weekday)]
            day_start_h = day_avail.get("start", prefs.work_start_hour)
            day_end_h = day_avail.get("end", prefs.work_end_hour)
        else:
            day_start_h = prefs.work_start_hour
            day_end_h = prefs.work_end_hour

        day_start = combine_local(current_date, day_start_h, 0, prefs.work_timezone)
        day_end = combine_local(current_date, day_end_h, 0, prefs.work_timezone)

        # Enumerate 30-minute-stepped candidate slots
        slot_start = day_start
        step = timedelta(minutes=30)
        duration = timedelta(minutes=link.duration_minutes)

        while slot_start + duration <= day_end:
            if slot_start < now:
                slot_start += step
                continue
            slot_end = slot_start + duration

            # Check no overlap with busy intervals
            overlap = any(
                not (slot_end <= b_start or slot_start >= b_end)
                for b_start, b_end in busy
            )
            if not overlap:
                slots.append({
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat(),
                })
            slot_start += step

        current_date += timedelta(days=1)

    return slots


def book_slot(
    link: SchedulingLink,
    prefs: UserPreferences,
    cal_service: GoogleCalendarService,
    slot_start: datetime,
    slot_end: datetime,
    booker_name: str,
    booker_email: str,
    answers: dict | None = None,
) -> dict[str, Any]:
    """Create a Google Calendar event for a booked slot."""
    description_parts = [f"Booked via scheduling link: {link.title}"]
    if answers:
        for q, a in answers.items():
            description_parts.append(f"\n{q}: {a}")

    event = {
        "summary": f"{link.title} — {booker_name}",
        "description": "\n".join(description_parts),
        "start": {"dateTime": slot_start.isoformat()},
        "end": {"dateTime": slot_end.isoformat()},
        "attendees": [{"email": booker_email}],
        "sendUpdates": "all",
    }
    return cal_service.create_event(event)
