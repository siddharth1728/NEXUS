"""NEXUS Error & Exception Hierarchy.

Defines domain and operational exceptions with standardized HTTP status mapping,
error codes, and structured details.
"""

from typing import Any


class AppError(Exception):
    """Base application exception for all NEXUS domain and operational errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured error dictionary."""
        return {
            "code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class NotFoundError(AppError):
    """Resource was not found."""

    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"

    def __init__(
        self,
        resource_type: str,
        resource_id: str | None = None,
        message: str | None = None,
    ) -> None:
        msg = message or f"{resource_type} with ID '{resource_id}' was not found."
        details = {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(msg, details=details)


class ValidationError(AppError):
    """Input payload or business validation failed."""

    status_code = 422
    error_code = "VALIDATION_FAILED"

    def __init__(
        self,
        message: str = "Validation failed for the supplied input.",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class ConflictError(AppError):
    """State conflict or concurrent modification error."""

    status_code = 409
    error_code = "STATE_CONFLICT"


class GraphCycleError(AppError):
    """Circular dependency detected in Action Graph."""

    status_code = 400
    error_code = "DEPENDENCY_CYCLE_DETECTED"

    def __init__(
        self,
        cycle_path: list[str],
        message: str = "Proposed relationship creates a cycle in the Action Graph.",
    ) -> None:
        super().__init__(message, details={"cycle_path": cycle_path})


class UnauthorizedError(AppError):
    """Authentication required or token invalid."""

    status_code = 401
    error_code = "UNAUTHORIZED"

    def __init__(
        self, message: str = "Authentication credentials were invalid or missing."
    ) -> None:
        super().__init__(message)


class ForbiddenError(AppError):
    """Authenticated user lacks permission for this resource."""

    status_code = 403
    error_code = "FORBIDDEN"

    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(message)


class DependencyUnavailableError(AppError):
    """External dependency (e.g. database, redis, AI service) is unavailable."""

    status_code = 503
    error_code = "DEPENDENCY_UNAVAILABLE"

    def __init__(
        self,
        service_name: str,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        msg = message or f"Underlying service '{service_name}' is currently unavailable."
        det = {"service_name": service_name, **(details or {})}
        super().__init__(msg, details=det)


class InternalError(AppError):
    """Unexpected internal server error."""

    status_code = 500
    error_code = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected internal error occurred.") -> None:
        super().__init__(message)
