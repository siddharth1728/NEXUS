"""NEXUS FastAPI Application Factory.

Initializes the FastAPI application, registers middleware, custom exception handlers,
and mounts API routers.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.endpoints import health
from app.api.v1.router import api_v1_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import correlation_id_ctx, get_logger, setup_logging
from app.core.middleware import CorrelationIdMiddleware
from app.db.session import close_database_connections
from app.schemas.common import ErrorDetail, ErrorEnvelope

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle context manager."""
    settings: Settings = app.state.settings
    setup_logging(log_level=settings.log_level, use_json=settings.log_json)
    logger.info(f"Starting {settings.app_name} v{settings.app_version} [{settings.env.value}]")

    yield

    logger.info(f"Shutting down {settings.app_name}...")
    await close_database_connections()
    logger.info("Shutdown complete.")


def create_app(settings: Settings | None = None) -> FastAPI:
    """FastAPI Application Factory."""
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        description="NEXUS Context-to-Action Engine Core API",
        docs_url="/docs" if not app_settings.is_production else None,
        redoc_url="/redoc" if not app_settings.is_production else None,
        openapi_url="/openapi.json" if not app_settings.is_production else None,
        lifespan=lifespan,
    )

    app.state.settings = app_settings

    # Middleware
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not app_settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --------------------------------------------------------------------------
    # Exception Handlers
    # --------------------------------------------------------------------------

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        corr_id = correlation_id_ctx.get()
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.message,
                details=exc.details,
                request_id=corr_id,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        corr_id = correlation_id_ctx.get()
        details = [
            {"loc": list(err.get("loc", [])), "msg": err.get("msg"), "type": err.get("type")}
            for err in exc.errors()
        ]
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="The submitted request body or parameters were invalid.",
                details=details,
                request_id=corr_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=envelope.model_dump(mode="json"),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        corr_id = correlation_id_ctx.get()
        code = "HTTP_ERROR"
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "RESOURCE_NOT_FOUND"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "FORBIDDEN"

        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code=code,
                message=str(exc.detail),
                details={},
                request_id=corr_id,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        corr_id = correlation_id_ctx.get()
        logger.exception(f"Unhandled server exception: {exc}")
        message = "An unexpected internal server error occurred."
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message=message,
                details={},
                request_id=corr_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=envelope.model_dump(mode="json"),
        )

    # --------------------------------------------------------------------------
    # Route Mounts
    # --------------------------------------------------------------------------
    # Root health shortcuts
    app.include_router(health.router, tags=["System Health"])
    # API v1 prefix
    app.include_router(api_v1_router, prefix=app_settings.api_v1_prefix)

    return app


# Default app instance for ASGI servers
app = create_app()
