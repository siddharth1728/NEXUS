"""Unit tests for application error and exception models."""

from app.core.errors import (
    AppError,
    ConflictError,
    DependencyUnavailableError,
    ForbiddenError,
    GraphCycleError,
    InternalError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


def test_base_app_error():
    err = AppError(
        "Something went wrong", error_code="CUSTOM_ERR", status_code=400, details={"k": "v"}
    )
    assert err.status_code == 400
    assert err.error_code == "CUSTOM_ERR"
    assert err.to_dict() == {
        "code": "CUSTOM_ERR",
        "message": "Something went wrong",
        "details": {"k": "v"},
    }


def test_not_found_error():
    err = NotFoundError(resource_type="Task", resource_id="123")
    assert err.status_code == 404
    assert err.error_code == "RESOURCE_NOT_FOUND"
    assert "Task" in err.message
    assert err.details == {"resource_type": "Task", "resource_id": "123"}


def test_validation_error():
    err = ValidationError("Bad input", details={"field": "missing"})
    assert err.status_code == 422
    assert err.error_code == "VALIDATION_FAILED"


def test_conflict_error():
    err = ConflictError("Task already completed")
    assert err.status_code == 409
    assert err.error_code == "STATE_CONFLICT"


def test_graph_cycle_error():
    err = GraphCycleError(cycle_path=["task-1", "task-2", "task-1"])
    assert err.status_code == 400
    assert err.error_code == "DEPENDENCY_CYCLE_DETECTED"
    assert err.details == {"cycle_path": ["task-1", "task-2", "task-1"]}


def test_auth_errors():
    unauth = UnauthorizedError()
    assert unauth.status_code == 401
    assert unauth.error_code == "UNAUTHORIZED"

    forbidden = ForbiddenError()
    assert forbidden.status_code == 403
    assert forbidden.error_code == "FORBIDDEN"


def test_dependency_unavailable_error():
    err = DependencyUnavailableError(service_name="PostgreSQL", message="Connection refused")
    assert err.status_code == 503
    assert err.error_code == "DEPENDENCY_UNAVAILABLE"
    assert err.details["service_name"] == "PostgreSQL"


def test_internal_error():
    err = InternalError()
    assert err.status_code == 500
    assert err.error_code == "INTERNAL_ERROR"
