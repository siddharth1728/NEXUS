"""NEXUS Core Middleware.

Provides request correlation ID injection, latency tracking, and request context lifecycle.
"""

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import correlation_id_ctx, get_logger

logger = get_logger("middleware")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware ensuring every request has a unique correlation ID."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Extract existing header or generate fresh UUID
        corr_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = correlation_id_ctx.set(corr_id)

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            response.headers["X-Request-ID"] = corr_id
            response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
            return response
        finally:
            correlation_id_ctx.reset(token)
