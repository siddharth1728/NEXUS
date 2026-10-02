"""NEXUS Health & Readiness Endpoints."""

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_app_settings
from app.core.config import Settings
from app.db.session import check_database_connection
from app.schemas.health import (
    ComponentHealth,
    HealthResponse,
    HealthStatus,
    ReadinessResponse,
)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness Check",
    description="Returns 200 OK if the FastAPI process is running and able to handle HTTP requests.",
)
async def health_check(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    """Check process liveness."""
    return HealthResponse(
        status=HealthStatus.HEALTHY,
        app_name=settings.app_name,
        app_version=settings.app_version,
        environment=settings.env.value,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Check",
    description="Verifies all required underlying services (e.g. PostgreSQL) before declaring readiness.",
    responses={
        status.HTTP_200_OK: {
            "description": "All dependencies are healthy and ready to accept traffic"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "One or more dependencies are unavailable"
        },
    },
)
async def readiness_check(
    response: Response,
    settings: Settings = Depends(get_app_settings),
) -> ReadinessResponse:
    """Check critical dependency readiness."""
    components: dict[str, ComponentHealth] = {}
    overall_status = HealthStatus.HEALTHY

    # Probe PostgreSQL
    db_ok, db_latency, db_err = await check_database_connection()
    if db_ok:
        components["database"] = ComponentHealth(
            status=HealthStatus.HEALTHY,
            latency_ms=round(db_latency, 2),
            message="PostgreSQL connection verified",
        )
    else:
        overall_status = HealthStatus.UNHEALTHY
        components["database"] = ComponentHealth(
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(db_latency, 2),
            message="PostgreSQL connection failed",
            details={"error": db_err},
        )

    # In testing mode without live DB, or in unhealthy state, set appropriate HTTP status code
    if overall_status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status=overall_status,
        app_name=settings.app_name,
        app_version=settings.app_version,
        components=components,
    )
