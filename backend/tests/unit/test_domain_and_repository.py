"""Unit tests for domain abstractions and BaseRepository."""

import uuid
from dataclasses import dataclass

import pytest
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import DomainEntity, DomainEvent, ValueObject
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.repositories.base import BaseRepository


# Dummy domain model for testing base abstractions
class SampleModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "test_samples"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)


@dataclass(frozen=True)
class SampleValueObject(ValueObject):
    code: str
    amount: float


class SampleEntity(DomainEntity):
    def __init__(self, id: uuid.UUID, name: str) -> None:
        super().__init__(id)
        self.name = name


@pytest.mark.asyncio
async def test_domain_entity_and_value_object():
    uid = uuid.uuid4()
    e1 = SampleEntity(id=uid, name="Alpha")
    e2 = SampleEntity(id=uid, name="Alpha Copy")
    e3 = SampleEntity(id=uuid.uuid4(), name="Beta")

    assert e1 == e2
    assert e1 != e3
    assert e1 != "not-an-entity"
    assert hash(e1) == hash(e2)
    assert repr(e1) == f"SampleEntity(id={uid})"

    vo = SampleValueObject(code="USD", amount=100.0)
    assert vo.to_dict() == {"code": "USD", "amount": 100.0}

    event = DomainEvent()
    assert event.event_name == "DomainEvent"
    assert event.event_id is not None


@pytest.mark.asyncio
async def test_base_repository_crud(in_memory_db_session: AsyncSession):
    repo = BaseRepository(SampleModel, in_memory_db_session)

    # 1. Create
    item1 = SampleModel(name="Sample One", status="active")
    item2 = SampleModel(name="Sample Two", status="pending")
    item3 = SampleModel(name="Sample Three", status="active")

    await repo.create(item1)
    await repo.create(item2)
    await repo.create(item3)
    await in_memory_db_session.commit()

    # 2. Get by ID
    fetched = await repo.get_by_id(item1.id)
    assert fetched is not None
    assert fetched.name == "Sample One"
    assert fetched.created_at is not None
    assert fetched.updated_at is not None
    assert "SampleModel(" in repr(fetched)

    # 3. Count
    total = await repo.count()
    assert total == 3

    active_count = await repo.count(filters={"status": "active"})
    assert active_count == 2

    # 4. List with pagination & filters
    items = await repo.list(offset=0, limit=2)
    assert len(items) == 2

    active_items = await repo.list(filters={"status": "active"})
    assert len(active_items) == 2

    # 5. Delete by ID
    deleted = await repo.delete_by_id(item2.id)
    assert deleted is True
    await in_memory_db_session.commit()

    after_delete = await repo.get_by_id(item2.id)
    assert after_delete is None
    assert await repo.count() == 2
