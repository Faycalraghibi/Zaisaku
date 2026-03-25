
from fastapi import APIRouter

from zaisaku.api.dependencies import ConfigDep
from zaisaku.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: ConfigDep):
    return HealthResponse(status="ok", env=settings.env)
