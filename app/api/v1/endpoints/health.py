from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.core.database import engine

router = APIRouter(prefix="/health", tags=["Health"])


async def get_health_status(settings: Settings) -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.get("", summary="Health Check", description="Kiểm tra trạng thái của ứng dụng.")
async def check_database_connection(request: Request) -> dict[str, str]:
    return await get_health_status(request.app.state.settings)