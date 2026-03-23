from datetime import datetime, timedelta
from typing import Any
import pytz
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.oauth_token import OAuthToken
from app.utils.crypto import encrypt_token, decrypt_token
from app.config import settings


SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar",
]

FOCUS_BLOCK_TAG = "focus-block"
MANAGED_BY_TAG = "calendar-ai"


async def get_valid_google_credentials(user_id: int, db: AsyncSession) -> Credentials | None:
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "google")
    )
    token_row = result.scalar_one_or_none()
    if not token_row:
        return None

    creds = Credentials(
        token=decrypt_token(token_row.access_token_enc),
        refresh_token=decrypt_token(token_row.refresh_token_enc) if token_row.refresh_token_enc else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=token_row.scopes.split(" ") if token_row.scopes else SCOPES,
    )
    if token_row.token_expiry:
        # Make expiry timezone-aware
        expiry = token_row.token_expiry
        if expiry.tzinfo is None:
            expiry = pytz.utc.localize(expiry)
        creds.expiry = expiry.replace(tzinfo=None)  # google-auth expects naive UTC

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Persist refreshed token
        await db.execute(
            update(OAuthToken)
            .where(OAuthToken.user_id == user_id, OAuthToken.provider == "google")
            .values(
                access_token_enc=encrypt_token(creds.token),
                token_expiry=pytz.utc.localize(creds.expiry) if creds.expiry else None,
            )
        )
        await db.commit()

    return creds


class GoogleCalendarService:
    def __init__(self, creds: Credentials):
        self.service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str = "primary",
        max_results: int = 250,
    ) -> list[dict[str, Any]]:
        time_min_str = time_min.isoformat() if time_min.tzinfo else time_min.isoformat() + "Z"
        time_max_str = time_max.isoformat() if time_max.tzinfo else time_max.isoformat() + "Z"

        events = []
        page_token = None
        while True:
            resp = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
                pageToken=page_token,
            ).execute()
            events.extend(resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return events

    def list_focus_blocks(self, time_min: datetime, time_max: datetime) -> list[dict[str, Any]]:
        """Return only events tagged as app-managed focus blocks."""
        all_events = self.list_events(time_min, time_max)
        return [
            e for e in all_events
            if e.get("extendedProperties", {}).get("private", {}).get("type") == FOCUS_BLOCK_TAG
        ]

    def create_focus_block(self, start: datetime, end: datetime, summary: str = "Focus Time") -> dict[str, Any]:
        event = {
            "summary": summary,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            "colorId": "2",  # green
            "extendedProperties": {
                "private": {
                    "type": FOCUS_BLOCK_TAG,
                    "managedBy": MANAGED_BY_TAG,
                }
            },
        }
        return self.service.events().insert(calendarId="primary", body=event).execute()

    def delete_event(self, event_id: str) -> None:
        self.service.events().delete(calendarId="primary", eventId=event_id).execute()

    def patch_event(self, event_id: str, body: dict, send_updates: str = "none") -> dict[str, Any]:
        return self.service.events().patch(
            calendarId="primary",
            eventId=event_id,
            body=body,
            sendUpdates=send_updates,
        ).execute()

    def create_event(self, body: dict) -> dict[str, Any]:
        return self.service.events().insert(calendarId="primary", body=body).execute()

    def get_event(self, event_id: str) -> dict[str, Any]:
        return self.service.events().get(calendarId="primary", eventId=event_id).execute()
