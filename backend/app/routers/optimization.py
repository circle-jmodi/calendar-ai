import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/optimize", tags=["optimization"])


def require_user(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    return user_id


@router.post("/run")
async def run_optimization(request: Request, db: AsyncSession = Depends(get_db)):
    """Manually trigger Claude optimization for the current user."""
    user_id = require_user(request)
    from app.services.optimization_job import run_optimization_for_user
    result = await run_optimization_for_user(user_id, db)
    return result


@router.post("/run-all")
async def run_all_optimizations(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by Cloud Scheduler with OIDC auth. Runs optimization for all users.
    In development, no auth check is performed.
    """
    if settings.environment == "production":
        # Verify OIDC token (Cloud Scheduler provides Bearer token)
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Missing authorization")

    from app.services.optimization_job import run_optimization_for_all_users
    await run_optimization_for_all_users()
    return {"ok": True, "message": "Optimization completed for all users"}


@router.get("/status")
async def optimization_status(request: Request):
    """Placeholder — in production this would return last-run info from DB."""
    require_user(request)
    return {"status": "No run history stored yet. Trigger /optimize/run to start."}
