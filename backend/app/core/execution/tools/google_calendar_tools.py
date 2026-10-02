"""Google Calendar Tools — capability-specific wrappers over GoogleCalendarConnector."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.execution.connectors.google_calendar import GoogleCalendarConnector
from app.core.execution.tool import BaseTool, ExecutionContext
from app.models.enums import Capability
from app.schemas.connection import Connection, ConnectionStatus


# ─── Strict Input Schemas ────────────────────────────────────────────────────

class GoogleCalendarListEventsInput(BaseModel):
    calendar_id: str = Field(default="primary", description="The ID of the calendar to fetch events from")
    max_results: int = Field(default=10, description="The maximum number of events to return")
    time_min: str | None = Field(default=None, description="Lower bound for an event's end time to filter by")


# ─── Base Calendar Tool ─────────────────────────────────────────────────────────

class BaseGoogleCalendarTool(BaseTool):
    """Base class for all Google Calendar tools."""

    def __init__(self, connector: GoogleCalendarConnector) -> None:
        self.connector = connector

    def _build_connection(self, context: ExecutionContext) -> Connection:
        now = datetime.now(UTC)
        return Connection(
            id="runtime-connection",
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            provider=self.connector.provider,
            status=ConnectionStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
        )

    async def _execute_impl(self, connection: Connection, parameters: BaseModel) -> dict[str, Any]:
        raise NotImplementedError

    async def _dry_run_impl(self, parameters: BaseModel) -> dict[str, Any]:
        """Show what would happen without calling Google."""
        return {
            "status": "dry_run",
            "provider": self.connector.provider,
            "capability": self.capability,
            "target": parameters.model_dump(),
            "approval_required": False,
            "message": "Dry run succeeded. No external request made.",
        }

    async def execute(self, parameters: BaseModel, context: ExecutionContext) -> dict[str, Any]:
        connection = self._build_connection(context)
        if context.dry_run:
            return await self._dry_run_impl(parameters)
        return await self._execute_impl(connection, parameters)


# ─── Concrete Calendar Tools ────────────────────────────────────────────────────

class GoogleCalendarListEventsTool(BaseGoogleCalendarTool):
    """Read events from Google Calendar."""

    @property
    def tool_id(self) -> str:
        return "google_calendar_list_events_v1"

    @property
    def capability(self) -> Capability:
        return Capability.CALENDAR_READ

    def get_input_schema(self) -> type[BaseModel]:
        return GoogleCalendarListEventsInput

    async def _execute_impl(self, connection: Connection, parameters: BaseModel) -> dict[str, Any]:
        if not isinstance(parameters, GoogleCalendarListEventsInput):
            raise TypeError("Invalid parameters type.")
        return await self.connector.list_events(
            connection, 
            calendar_id=parameters.calendar_id, 
            max_results=parameters.max_results, 
            time_min=parameters.time_min
        )
