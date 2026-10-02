"""Integration tests for Domain Models and Action Graph."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.errors import GraphCycleError
from app.domain.action_graph import check_for_cycles
from app.models.action import Action, ActionEdge
from app.models.document import Document, ExtractionJob
from app.models.enums import ActionStatus, EdgeRelationType, ExtractionJobStatus
from app.models.tenant import Tenant
from app.models.user import User


@pytest.fixture
async def tenant(in_memory_db_session: AsyncSession) -> Tenant:
    tenant = Tenant(name="Test Tenant")
    in_memory_db_session.add(tenant)
    await in_memory_db_session.commit()
    return tenant


@pytest.fixture
async def user(in_memory_db_session: AsyncSession, tenant: Tenant) -> User:
    user = User(tenant_id=tenant.id, email=f"{uuid.uuid4()}@example.com", full_name="Test User")
    in_memory_db_session.add(user)
    await in_memory_db_session.commit()
    return user


@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_creation_and_constraints(
    in_memory_db_session: AsyncSession, tenant: Tenant, user: User
) -> None:
    # Test read
    stmt = select(User).where(User.id == user.id)
    result = await in_memory_db_session.execute(stmt)
    fetched_user = result.scalar_one_or_none()
    assert fetched_user is not None
    assert fetched_user.email == user.email

    # Test uniqueness constraint
    duplicate_user = User(tenant_id=tenant.id, email=user.email, full_name="Duplicate")
    in_memory_db_session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        await in_memory_db_session.commit()
    await in_memory_db_session.rollback()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_document_and_extraction_job(
    in_memory_db_session: AsyncSession, tenant: Tenant, user: User
) -> None:
    # Create document
    doc = Document(
        tenant_id=tenant.id,
        owner_id=user.id,
        title="Test Doc",
        source_type="pdf",
        sha256_hash="hash123",
        processing_status="PROCESSING",
    )
    in_memory_db_session.add(doc)
    await in_memory_db_session.commit()

    # Create extraction job
    job = ExtractionJob(document_id=doc.id, status=ExtractionJobStatus.RUNNING, retry_count=1)
    in_memory_db_session.add(job)
    await in_memory_db_session.commit()

    # Verify relationships
    stmt = select(ExtractionJob).where(ExtractionJob.id == job.id)
    result = await in_memory_db_session.execute(stmt)
    fetched_job = result.scalar_one()
    assert fetched_job.document_id == doc.id
    assert fetched_job.status == ExtractionJobStatus.RUNNING


@pytest.mark.asyncio
@pytest.mark.integration
async def test_action_and_edge_persistence(
    in_memory_db_session: AsyncSession, tenant: Tenant, user: User
) -> None:
    action_a = Action(
        tenant_id=tenant.id,
        title="Action A",
        description="Desc A",
        assignee_id=user.id,
        status=ActionStatus.READY,
    )
    action_b = Action(
        tenant_id=tenant.id, title="Action B", description="Desc B", status=ActionStatus.BLOCKED
    )
    in_memory_db_session.add_all([action_a, action_b])
    await in_memory_db_session.commit()

    edge = ActionEdge(
        tenant_id=tenant.id,
        source_id=action_a.id,
        target_id=action_b.id,
        relation_type=EdgeRelationType.DEPENDS_ON,
    )
    in_memory_db_session.add(edge)
    await in_memory_db_session.commit()

    # Fetch edge and check foreign keys
    stmt = select(ActionEdge).where(ActionEdge.id == edge.id)
    result = await in_memory_db_session.execute(stmt)
    fetched_edge = result.scalar_one()
    assert fetched_edge.source_id == action_a.id
    assert fetched_edge.target_id == action_b.id

    # Duplicate edge prevention
    dup_edge = ActionEdge(
        tenant_id=tenant.id,
        source_id=action_a.id,
        target_id=action_b.id,
        relation_type=EdgeRelationType.DEPENDS_ON,
    )
    in_memory_db_session.add(dup_edge)
    with pytest.raises(IntegrityError):
        await in_memory_db_session.commit()
    await in_memory_db_session.rollback()


@pytest.mark.unit
def test_graph_cycle_detection() -> None:
    # A -> B -> C is valid
    a_id = uuid.uuid4()
    b_id = uuid.uuid4()
    c_id = uuid.uuid4()

    edges = [
        ActionEdge(source_id=a_id, target_id=b_id, relation_type=EdgeRelationType.DEPENDS_ON),
        ActionEdge(source_id=b_id, target_id=c_id, relation_type=EdgeRelationType.DEPENDS_ON),
    ]

    # Should not raise
    new_edge = ActionEdge(source_id=a_id, target_id=c_id, relation_type=EdgeRelationType.DEPENDS_ON)
    check_for_cycles(new_edge, edges)

    # A -> A (self ref) should fail
    self_edge = ActionEdge(
        source_id=a_id, target_id=a_id, relation_type=EdgeRelationType.DEPENDS_ON
    )
    with pytest.raises(GraphCycleError, match="Self-referencing edges"):
        check_for_cycles(self_edge, edges)

    # C -> A (cycle) should fail
    cycle_edge = ActionEdge(
        source_id=c_id, target_id=a_id, relation_type=EdgeRelationType.DEPENDS_ON
    )
    with pytest.raises(GraphCycleError, match="creates a cycle"):
        check_for_cycles(cycle_edge, edges)
