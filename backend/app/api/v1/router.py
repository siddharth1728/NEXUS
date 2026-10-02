"""NEXUS API v1 Router Registration."""

from fastapi import APIRouter

from app.api.v1.endpoints import actions, documents, extraction, health

api_v1_router = APIRouter()

# Health & Readiness
api_v1_router.include_router(health.router, tags=["System Health"])

# Core Domain
api_v1_router.include_router(actions.router, prefix="/actions", tags=["Actions"])
api_v1_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_v1_router.include_router(extraction.router, prefix="/extraction", tags=["Extraction"])
