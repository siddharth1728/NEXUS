"""NEXUS API v1 Router Registration."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    actions,
    connectors,
    documents,
    execution,
    extraction,
    health,
    synthesis,
    autonomous,
)

api_v1_router = APIRouter()

# Health & Readiness
api_v1_router.include_router(health.router, tags=["System Health"])

# Core Domain
api_v1_router.include_router(actions.router, prefix="/actions", tags=["Actions"])
api_v1_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_v1_router.include_router(extraction.router, prefix="/extraction", tags=["Extraction"])
api_v1_router.include_router(synthesis.router, prefix="/synthesis", tags=["Synthesis"])
api_v1_router.include_router(execution.router, prefix="/execution", tags=["Execution"])
api_v1_router.include_router(connectors.router, prefix="/connectors", tags=["Connectors"])
api_v1_router.include_router(autonomous.router, prefix="/autonomous", tags=["Autonomous"])
