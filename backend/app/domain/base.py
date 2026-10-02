"""NEXUS Core Domain Base Classes and Value Objects."""

import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ValueObject:
    """Immutable Value Object base class."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DomainEntity:
    """Base Domain Entity with identity-based equality semantics."""

    def __init__(self, id: uuid.UUID) -> None:
        self.id = id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DomainEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


@dataclass(frozen=True)
class DomainEvent:
    """Immutable Domain Event."""

    event_id: uuid.UUID = uuid.uuid4()
    occurred_at: datetime = datetime.now(UTC)

    @property
    def event_name(self) -> str:
        return self.__class__.__name__
