import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ConnectionStatus(enum.StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"

class ConnectorHealth(BaseModel):
    status: ConnectionStatus
    provider: str
    message: str | None = None
    last_checked: datetime

class ConnectionBase(BaseModel):
    provider: str
    tenant_id: str
    user_id: str | None = None
    status: ConnectionStatus = ConnectionStatus.AUTHENTICATION_REQUIRED
    connection_metadata: dict[str, Any] = {}

class ConnectionCreate(ConnectionBase):
    pass

class ConnectionUpdate(BaseModel):
    status: ConnectionStatus | None = None
    connection_metadata: dict[str, Any] | None = None

class ConnectionInDBBase(ConnectionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Connection(ConnectionInDBBase):
    pass
