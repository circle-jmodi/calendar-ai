import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.database import get_db
from app.models.user import User
from app.models.oauth_token import OAuthToken
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/slack", tags=["slack"])


def verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    """Verify that the request came from Slack."""
    if abs(time.time() - float(timestamp)) > 300:
        return False  # Replay attack protection

    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    expected = "v0=" + hmac.new(
        key=settings.slack_signing_secret.encode(),
        msg=sig_basestring.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def get_user_by_slack_id(slack_user_id: str, db: AsyncSession) -> User | None:
    """Find a DB user by their Slack user ID (stored in token scopes/metadata)."""
    # We look up by matching Slack token — for simplicity store slack_user_id in OAuthToken.scopes
    # A better approach: add slack_user_id column to OAuthToken
    # For now we use Slack API to get email and match
    result = await db.execute(select(OAuthToken).where(OAuthToken.provider == "slack"))
    for token_row in result.scalars().all():
        from app.utils.crypto import decrypt_token
        try:
            token = decrypt_token(token_row.access_token_enc)
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {token}"},
                )
                data = resp.json()
                if data.get("ok") and data.get("user_id") == slack_user_id:
                    user_result = await db.execute(select(User).where(User.id == token_row.user_id))
                    return user_result.scalar_one_or_none()
        except Exception:
            continue
    return None


async def send_delayed_response(response_url: str, message: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(response_url, json={"text": message, "response_type": "ephemeral"})


@router.post("/commands")
async def handle_slash_command(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body_bytes = await request.body()

    # Verify Slack signature
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if settings.slack_signing_secret and not verify_slack_signature(body_bytes, timestamp, signature):
        raise HTTPException(403, "Invalid Slack signature")

    # Parse form data
    from urllib.parse import parse_qs
    params = {k: v[0] for k, v in parse_qs(body_bytes.decode()).items()}
    command = params.get("command", "")
    text = params.get("text", "").strip()
    slack_user_id = params.get("user_id", "")
    response_url = params.get("response_url", "")

    # Find matching DB user
    user = await get_user_by_slack_id(slack_user_id, db)
    if not user:
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"Connect your calendar first: {settings.frontend_url}/",
        })

    if command == "/focus-time":
        minutes = int(text) if text.isdigit() else 90
        from app.services.google_calendar import get_valid_google_credentials, GoogleCalendarService
        creds = await get_valid_google_credentials(user.id, db)
        if not creds:
            return JSONResponse({"response_type": "ephemeral", "text": "Google Calendar not connected."})

        now = datetime.now(timezone.utc)
        cal = GoogleCalendarService(creds)
        block = cal.create_focus_block(now, now + timedelta(minutes=minutes))
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"Focus block created: {minutes} minutes starting now :dart:",
        })

    elif command == "/optimize":
        # Respond immediately, run async
        import asyncio
        async def _run():
            async with __import__("app.database", fromlist=["AsyncSessionLocal"]).AsyncSessionLocal() as new_db:
                from app.services.optimization_job import run_optimization_for_user
                result = await run_optimization_for_user(user.id, new_db)
                await send_delayed_response(
                    response_url,
                    f"Optimization complete! {result.get('summary', '')}\n"
                    f"Focus blocks created: {result.get('focus_blocks_created', 0)}, "
                    f"removed: {result.get('focus_blocks_removed', 0)}",
                )
        asyncio.create_task(_run())
        return JSONResponse({
            "response_type": "ephemeral",
            "text": "Running calendar optimization... I'll update you shortly :hourglass_flowing_sand:",
        })

    elif command == "/schedule":
        from sqlalchemy import select as sa_select
        from app.models.scheduling_link import SchedulingLink
        result = await db.execute(
            sa_select(SchedulingLink).where(SchedulingLink.user_id == user.id, SchedulingLink.active == True).limit(1)
        )
        link = result.scalar_one_or_none()
        if not link:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": f"No scheduling link found. Create one at {settings.frontend_url}/scheduling",
            })
        base = settings.cloud_run_service_url or "http://localhost:8000"
        return JSONResponse({
            "response_type": "in_channel",
            "text": f"Book time with me: {base}/schedule/{link.slug}",
        })

    elif command == "/calendar":
        from app.services.google_calendar import get_valid_google_credentials, GoogleCalendarService
        creds = await get_valid_google_credentials(user.id, db)
        if not creds:
            return JSONResponse({"response_type": "ephemeral", "text": "Google Calendar not connected."})

        cal = GoogleCalendarService(creds)
        now = datetime.now(timezone.utc)
        events = cal.list_events(now.replace(hour=0, minute=0), now.replace(hour=23, minute=59))

        if not events:
            return JSONResponse({"response_type": "ephemeral", "text": "No events today :tada:"})

        lines = ["*Today's events:*"]
        for e in events[:10]:
            start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
            title = e.get("summary", "Busy")
            lines.append(f"• {start[:16].replace('T', ' ')} — {title}")
        return JSONResponse({"response_type": "ephemeral", "text": "\n".join(lines)})

    elif command == "/connect-calendar":
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"Connect your calendar here: {settings.frontend_url}/",
        })

    return JSONResponse({"response_type": "ephemeral", "text": "Unknown command."})
