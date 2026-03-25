"""Health check endpoints."""

from fastapi import APIRouter

from zaisaku.api.dependencies import ConfigDep
from zaisaku.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: ConfigDep):
    """Simple health check returning the active environment."""
    return HealthResponse(status="ok", env=settings.env)
