from fastapi import APIRouter

from app.schemas import HealthStatus

router = APIRouter()


@router.get("/health")
def get_health() -> HealthStatus:
    return HealthStatus(status="ok")
