from typing import Any

import httpx

from app.core.errors import AppError, UnauthorizedError
from app.core.execution.connectors.base import BaseConnector
from app.core.secrets import secret_store
from app.models.enums import Capability
from app.schemas.connection import Connection, ConnectionStatus, ConnectorHealth


class GoogleCalendarConnector(BaseConnector):
    """Google Calendar Connector."""

    @property
    def provider(self) -> str:
        return "google_calendar"

    @property
    def supported_capabilities(self) -> list[Capability]:
        return [Capability.CALENDAR_READ]

    async def _make_request(self, method: str, url: str, connection: Connection, params: dict[str, Any] | None = None) -> Any:
        token = secret_store.get_secret(self.get_credential_key(connection))
        if not token:
            raise UnauthorizedError(message="Missing Google Calendar API token")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.request(method, url, headers=headers, params=params)

                if response.status_code == 401:
                    raise UnauthorizedError("Google API token invalid or expired")
                elif response.status_code == 403:
                    raise AppError("Google API rate limited or forbidden", error_code="GOOGLE_API_ERROR", status_code=403)
                elif response.status_code == 404:
                    raise AppError("Resource not found", error_code="NOT_FOUND", status_code=404)

                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                raise AppError(f"Connection to Google API failed: {str(e)}", error_code="CONNECTION_ERROR", status_code=502)

    async def check_health(self, connection: Connection) -> ConnectorHealth:
        """Check if the connection is healthy by making a minimal request."""
        try:
            # A minimal, read-only request to verify token validity
            # For Calendar API, reading the current user's profile or calendar list works well.
            await self._make_request("GET", "https://www.googleapis.com/calendar/v3/users/me/calendarList", connection, params={"maxResults": 1})
            return ConnectorHealth(
                status=ConnectionStatus.AVAILABLE,
                provider=self.provider,
                message="Healthy",
                last_checked=connection.updated_at
            )
        except UnauthorizedError as e:
            return ConnectorHealth(
                status=ConnectionStatus.AUTHENTICATION_REQUIRED,
                provider=self.provider,
                message=str(e),
                last_checked=connection.updated_at
            )
        except Exception as e:
            return ConnectorHealth(
                status=ConnectionStatus.UNAVAILABLE,
                provider=self.provider,
                message=str(e),
                last_checked=connection.updated_at
            )

    async def list_events(self, connection: Connection, calendar_id: str = "primary", max_results: int = 10, time_min: str | None = None) -> dict[str, Any]:
        """Fetch events from a specific calendar."""
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        params = {"maxResults": max_results, "singleEvents": "true", "orderBy": "startTime"}
        if time_min:
            params["timeMin"] = time_min

        response_data = await self._make_request("GET", url, connection, params)

        # Normalize the response
        normalized_events = []
        for item in response_data.get("items", []):
            normalized_events.append({
                "id": item.get("id"),
                "summary": item.get("summary", ""),
                "description": item.get("description", ""),
                "start": item.get("start", {}).get("dateTime") or item.get("start", {}).get("date"),
                "end": item.get("end", {}).get("dateTime") or item.get("end", {}).get("date"),
                "htmlLink": item.get("htmlLink", "")
            })

        return {
            "calendar_id": calendar_id,
            "events": normalized_events
        }
