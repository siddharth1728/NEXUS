"""Unit tests for API response and request schemas."""

from app.schemas.common import (
    APIResponse,
    ErrorDetail,
    ErrorEnvelope,
    PaginatedResponse,
    PaginationParams,
)
from app.schemas.health import ComponentHealth, HealthResponse, HealthStatus, ReadinessResponse


def test_api_response_envelope():
    resp = APIResponse(data={"key": "value"}, request_id="req-123")
    assert resp.data == {"key": "value"}
    assert resp.request_id == "req-123"
    assert resp.timestamp is not None


def test_error_envelope():
    env = ErrorEnvelope(
        error=ErrorDetail(
            code="INVALID_PARAM",
            message="Param x is invalid",
            details={"param": "x"},
            request_id="req-456",
        )
    )
    assert env.error.code == "INVALID_PARAM"
    assert env.error.request_id == "req-456"


def test_pagination_params_and_response():
    params = PaginationParams(page=2, page_size=10)
    assert params.offset == 10
    assert params.limit == 10

    items = ["item1", "item2", "item3"]
    paginated = PaginatedResponse.create(items=items, total_count=25, params=params)
    assert paginated.page == 2
    assert paginated.page_size == 10
    assert paginated.total_count == 25
    assert paginated.total_pages == 3
    assert paginated.items == items


def test_health_schemas():
    health = HealthResponse(
        status=HealthStatus.HEALTHY,
        app_name="NEXUS",
        app_version="0.1.0",
        environment="testing",
    )
    assert health.status == HealthStatus.HEALTHY

    readiness = ReadinessResponse(
        status=HealthStatus.HEALTHY,
        app_name="NEXUS",
        app_version="0.1.0",
        components={
            "database": ComponentHealth(
                status=HealthStatus.HEALTHY,
                latency_ms=1.5,
                message="Connected",
            )
        },
    )
    assert readiness.components["database"].status == HealthStatus.HEALTHY
    assert readiness.components["database"].latency_ms == 1.5
