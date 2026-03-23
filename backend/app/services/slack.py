import logging
from datetime import datetime, timezone
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.oauth_token import OAuthToken
from app.models.preferences import UserPreferences
from app.utils.crypto import decrypt_token

logger = logging.getLogger(__name__)


async def get_slack_client(user_id: int, db: AsyncSession) -> WebClient | None:
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "slack")
    )
    token_row = result.scalar_one_or_none()
    if not token_row:
        return None
    token = decrypt_token(token_row.access_token_enc)
    return WebClient(token=token)


def set_slack_status(client: WebClient, text: str, emoji: str, expiration: int = 0) -> None:
    """Set user's Slack status. expiration is Unix timestamp (0 = no expiry)."""
    try:
        client.users_profile_set(
            profile={
                "status_text": text,
                "status_emoji": emoji,
                "status_expiration": expiration,
            }
        )
    except SlackApiError as e:
        logger.error(f"Failed to set Slack status: {e}")


def clear_slack_status(client: WebClient) -> None:
    try:
        client.users_profile_set(
            profile={
                "status_text": "",
                "status_emoji": "",
                "status_expiration": 0,
            }
        )
    except SlackApiError as e:
        logger.error(f"Failed to clear Slack status: {e}")


async def sync_slack_status_for_user(
    user_id: int,
    db: AsyncSession,
    cal_service,  # GoogleCalendarService
    preferences: UserPreferences,
) -> None:
    """Determine current event and update Slack status accordingly."""
    if not preferences or not preferences.slack_status_sync_enabled:
        return

    client = await get_slack_client(user_id, db)
    if not client:
        return

    now = datetime.now(timezone.utc)
    from datetime import timedelta
    events = cal_service.list_events(now - timedelta(minutes=1), now + timedelta(minutes=1))

    # Filter events currently happening
    current_events = []
    for e in events:
        start_str = e.get("start", {}).get("dateTime")
        end_str = e.get("end", {}).get("dateTime")
        if not start_str or not end_str:
            continue
        from app.utils.time_utils import parse_iso
        start = parse_iso(start_str)
        end = parse_iso(end_str)
        if start <= now <= end:
            current_events.append((e, start, end))

    if not current_events:
        clear_slack_status(client)
        return

    # Check for focus block first
    for event, start, end in current_events:
        if event.get("extendedProperties", {}).get("private", {}).get("type") == "focus-block":
            set_slack_status(
                client,
                preferences.slack_focus_status_text,
                preferences.slack_focus_status_emoji,
                expiration=int(end.timestamp()),
            )
            return

    # Otherwise: in a meeting
    _, _, end = current_events[0]
    set_slack_status(
        client,
        "In a meeting",
        ":calendar:",
        expiration=int(end.timestamp()),
    )
