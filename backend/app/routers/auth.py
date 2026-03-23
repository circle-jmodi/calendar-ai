import logging
from datetime import datetime, timezone
from urllib.parse import urlencode
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from app.database import get_db
from app.models.user import User
from app.models.oauth_token import OAuthToken
from app.services.google_calendar import SCOPES
from app.utils.crypto import encrypt_token
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def get_google_flow() -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


@router.get("/google/login")
async def google_login(request: Request):
    flow = get_google_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["oauth_state"] = state
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Missing authorization code")

    flow = get_google_flow()
    flow.fetch_token(code=code)
    creds: Credentials = flow.credentials

    # Get user info
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {creds.token}"},
        )
        resp.raise_for_status()
        user_info = resp.json()

    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", email)

    # Upsert user
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()
    if user:
        user.last_login = datetime.now(timezone.utc)
        user.name = name
    else:
        user = User(google_id=google_id, email=email, name=name)
        db.add(user)
    await db.flush()  # get user.id

    # Upsert OAuth token (encrypted)
    token_expiry = None
    if creds.expiry:
        import pytz
        token_expiry = pytz.utc.localize(creds.expiry) if creds.expiry.tzinfo is None else creds.expiry

    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == "google")
    )
    token_row = result.scalar_one_or_none()
    if token_row:
        token_row.access_token_enc = encrypt_token(creds.token)
        if creds.refresh_token:
            token_row.refresh_token_enc = encrypt_token(creds.refresh_token)
        token_row.token_expiry = token_expiry
        token_row.scopes = " ".join(creds.scopes or SCOPES)
    else:
        token_row = OAuthToken(
            user_id=user.id,
            provider="google",
            access_token_enc=encrypt_token(creds.token),
            refresh_token_enc=encrypt_token(creds.refresh_token) if creds.refresh_token else None,
            token_expiry=token_expiry,
            scopes=" ".join(creds.scopes or SCOPES),
        )
        db.add(token_row)

    await db.commit()

    # Store user_id in session
    request.session["user_id"] = user.id
    return RedirectResponse(f"{settings.frontend_url}/dashboard")


@router.get("/slack/login")
async def slack_login(request: Request):
    params = {
        "client_id": settings.slack_client_id,
        "scope": "users.profile:write,users.profile:read",
        "user_scope": "users.profile:write,users.profile:read",
        "redirect_uri": settings.slack_redirect_uri,
        "state": request.session.get("user_id", ""),
    }
    url = "https://slack.com/oauth/v2/authorize?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/slack/callback")
async def slack_callback(request: Request, db: AsyncSession = Depends(get_db)):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Missing Slack auth code")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": code,
                "redirect_uri": settings.slack_redirect_uri,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        raise HTTPException(400, f"Slack OAuth error: {data.get('error')}")

    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "Not authenticated — complete Google login first")

    # authed_user token is the user token (for profile.set)
    authed_user = data.get("authed_user", {})
    access_token = authed_user.get("access_token") or data.get("access_token")

    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "slack")
    )
    token_row = result.scalar_one_or_none()
    if token_row:
        token_row.access_token_enc = encrypt_token(access_token)
        token_row.scopes = authed_user.get("scope", "")
    else:
        db.add(OAuthToken(
            user_id=user_id,
            provider="slack",
            access_token_enc=encrypt_token(access_token),
            scopes=authed_user.get("scope", ""),
        ))
    await db.commit()

    return RedirectResponse(f"{settings.frontend_url}/dashboard?slack=connected")


@router.get("/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "Not authenticated")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    # Check which OAuth connections exist
    tokens = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
    providers = {t.provider for t in tokens.scalars().all()}

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "google_connected": "google" in providers,
        "slack_connected": "slack" in providers,
    }


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}
