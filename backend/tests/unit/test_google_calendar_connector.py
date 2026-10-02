"""Unit tests for Google Calendar Connector and Tools."""

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import BaseModel

from app.core.errors import AppError
from app.core.execution.connectors.google_calendar import GoogleCalendarConnector
from app.core.execution.tool import ExecutionContext
from app.core.execution.tools.google_calendar_tools import (
    GoogleCalendarListEventsInput,
    GoogleCalendarListEventsTool,
)
from app.models.enums import Capability
from app.schemas.connection import Connection, ConnectionStatus


@pytest.fixture
def connector() -> GoogleCalendarConnector:
    return GoogleCalendarConnector()


@pytest.fixture
def mock_connection() -> Connection:
    return Connection(
        id="test-conn-1",
        tenant_id="00000000-0000-4000-8000-000000000001",
        provider="google_calendar",
        status=ConnectionStatus.AVAILABLE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def execution_context() -> ExecutionContext:
    return ExecutionContext(
        tenant_id="00000000-0000-4000-8000-000000000001",
        user_id="user1",
        execution_id=str(uuid.uuid4()),
    )


def test_connector_properties(connector: GoogleCalendarConnector) -> None:
    assert connector.provider == "google_calendar"
    assert Capability.CALENDAR_READ in connector.supported_capabilities


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_health_check_success(mock_get_secret: Any, connector: GoogleCalendarConnector, mock_connection: Connection) -> None:
    mock_get_secret.return_value = "valid_token"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}

    with patch("httpx.AsyncClient.request", return_value=mock_response):
        health = await connector.check_health(mock_connection)
        assert health.status == ConnectionStatus.AVAILABLE
        assert health.provider == "google_calendar"


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_health_check_missing_token(mock_get_secret: Any, connector: GoogleCalendarConnector, mock_connection: Connection) -> None:
    mock_get_secret.return_value = None

    health = await connector.check_health(mock_connection)
    assert health.status == ConnectionStatus.AUTHENTICATION_REQUIRED
    assert "Missing Google Calendar API token" in health.message


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_health_check_invalid_token(mock_get_secret: Any, connector: GoogleCalendarConnector, mock_connection: Connection) -> None:
    mock_get_secret.return_value = "invalid_token"

    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch("httpx.AsyncClient.request", return_value=mock_response):
        health = await connector.check_health(mock_connection)
        assert health.status == ConnectionStatus.AUTHENTICATION_REQUIRED
        assert "invalid or expired" in health.message


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_health_check_connection_error(mock_get_secret: Any, connector: GoogleCalendarConnector, mock_connection: Connection) -> None:
    mock_get_secret.return_value = "valid_token"

    with patch("httpx.AsyncClient.request", side_effect=httpx.RequestError("Failed to connect")):
        health = await connector.check_health(mock_connection)
        assert health.status == ConnectionStatus.UNAVAILABLE
        assert "Connection to Google API failed" in health.message


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_list_events_success(mock_get_secret: Any, connector: GoogleCalendarConnector, mock_connection: Connection) -> None:
    mock_get_secret.return_value = "valid_token"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Meeting",
                "start": {"dateTime": "2026-10-02T10:00:00Z"},
                "end": {"dateTime": "2026-10-02T11:00:00Z"}
            }
        ]
    }

    with patch("httpx.AsyncClient.request", return_value=mock_response):
        result = await connector.list_events(mock_connection, "primary", 10)
        assert result["calendar_id"] == "primary"
        assert len(result["events"]) == 1
        assert result["events"][0]["id"] == "event1"


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_list_events_403(mock_get_secret: Any, connector: GoogleCalendarConnector, mock_connection: Connection) -> None:
    mock_get_secret.return_value = "valid_token"

    mock_response = MagicMock()
    mock_response.status_code = 403

    with patch("httpx.AsyncClient.request", return_value=mock_response):
        with pytest.raises(AppError) as exc:
            await connector.list_events(mock_connection, "primary", 10)
        assert exc.value.status_code == 403


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_list_events_404(mock_get_secret: Any, connector: GoogleCalendarConnector, mock_connection: Connection) -> None:
    mock_get_secret.return_value = "valid_token"

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient.request", return_value=mock_response):
        with pytest.raises(AppError) as exc:
            await connector.list_events(mock_connection, "primary", 10)
        assert exc.value.status_code == 404


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_tool_execute(mock_get_secret: Any, connector: GoogleCalendarConnector, execution_context: ExecutionContext) -> None:
    mock_get_secret.return_value = "valid_token"
    tool = GoogleCalendarListEventsTool(connector)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}

    with patch("httpx.AsyncClient.request", return_value=mock_response):
        result = await tool.execute(GoogleCalendarListEventsInput(calendar_id="primary"), execution_context)
        assert result["calendar_id"] == "primary"


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_tool_dry_run(mock_get_secret: Any, connector: GoogleCalendarConnector, execution_context: ExecutionContext) -> None:
    tool = GoogleCalendarListEventsTool(connector)
    execution_context.dry_run = True

    result = await tool.execute(GoogleCalendarListEventsInput(calendar_id="primary"), execution_context)
    assert result["status"] == "dry_run"
    assert result["capability"] == Capability.CALENDAR_READ
    assert result["approval_required"] is False


@patch("app.core.execution.connectors.google_calendar.secret_store.get_secret")
@pytest.mark.asyncio
async def test_tool_invalid_params(mock_get_secret: Any, connector: GoogleCalendarConnector, execution_context: ExecutionContext) -> None:
    tool = GoogleCalendarListEventsTool(connector)

    # Pass invalid parameters type
    class WrongInput(BaseModel):
        pass

    with pytest.raises(TypeError):
        await tool.execute(WrongInput(), execution_context)
