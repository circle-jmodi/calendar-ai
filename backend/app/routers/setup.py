import secrets
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/setup", tags=["setup"])

REQUIRED_FIELDS = ["google_client_id", "google_client_secret", "anthropic_api_key"]
OPTIONAL_FIELDS = ["slack_client_id", "slack_client_secret", "slack_signing_secret", "slack_bot_token"]


def _missing_fields() -> list[str]:
    missing = []
    for field in REQUIRED_FIELDS:
        if not getattr(settings, field, ""):
            missing.append(field)
    return missing


@router.get("/status")
async def setup_status():
    missing = _missing_fields()
    return {"complete": len(missing) == 0, "missing": missing}


class ConfigureRequest(BaseModel):
    google_client_id: str
    google_client_secret: str
    anthropic_api_key: str
    slack_client_id: str = ""
    slack_client_secret: str = ""
    slack_signing_secret: str = ""
    slack_bot_token: str = ""


def _write_env(updates: dict) -> None:
    env_path = Path(".env")
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    existing: dict[str, str] = {}
    for line in lines:
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            existing[k.strip()] = v.strip()
    existing.update(updates)
    with env_path.open("w") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")


@router.post("/configure", status_code=200)
async def configure(req: ConfigureRequest):
    # Self-lock: if already configured, reject
    if settings.google_client_id:
        raise HTTPException(status_code=403, detail="Setup already complete. Edit .env to reconfigure.")

    updates: dict[str, str] = {
        "GOOGLE_CLIENT_ID": req.google_client_id,
        "GOOGLE_CLIENT_SECRET": req.google_client_secret,
        "ANTHROPIC_API_KEY": req.anthropic_api_key,
        # Auto-generate secrets so user never needs to run CLI commands
        "SECRET_KEY": secrets.token_hex(32),
        "ENCRYPTION_KEY": Fernet.generate_key().decode(),
    }

    if req.slack_client_id:
        updates["SLACK_CLIENT_ID"] = req.slack_client_id
    if req.slack_client_secret:
        updates["SLACK_CLIENT_SECRET"] = req.slack_client_secret
    if req.slack_signing_secret:
        updates["SLACK_SIGNING_SECRET"] = req.slack_signing_secret
    if req.slack_bot_token:
        updates["SLACK_BOT_TOKEN"] = req.slack_bot_token

    _write_env(updates)
    return {"ok": True}
