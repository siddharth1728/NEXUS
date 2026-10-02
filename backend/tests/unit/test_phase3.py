"""Tests for Phase 03 - Personalization, Dependency Inference, Conflict Resolution."""

import uuid

from app.domain.conflict_resolution import detect_contradictory_actions
from app.domain.dependency_inference import infer_dependencies
from app.domain.personalization import score_action_relevance
from app.models.action import Action, ActionEdge
from app.models.enums import ConfidenceLevel, EdgeRelationType
from app.models.user import User


def test_personalization_engine() -> None:
    tenant_id = uuid.uuid4()

    user_admin = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        role="admin",
        email="admin@test.com",
        full_name="Admin",
    )
    user_eng = User(
        id=uuid.uuid4(), tenant_id=tenant_id, role="engineer", email="eng@test.com", full_name="Eng"
    )

    action1 = Action(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="Deploy code to production",
        description="Fix the bug and deploy to production server.",
        priority="P1",
    )

    action2 = Action(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="Approve budget",
        description="Review and approve the Q4 budget.",
        priority="P2",
    )

    # Engineer should have high score for deploy action
    score_eng = score_action_relevance(action1, user_eng)
    assert score_eng > 0.5  # Code, deploy, fix, bug keywords

    # Admin should have high score for approve action
    score_admin = score_action_relevance(action2, user_admin)
    assert score_admin > 0.5

    # Direct assignment gives 1.0
    action2.assignee_id = user_eng.id
    assert score_action_relevance(action2, user_eng) == 1.0


def test_dependency_inference() -> None:
    tenant_id = uuid.uuid4()

    a1 = Action(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="Setup Database",
        description="Initialize the schema",
    )
    a2 = Action(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="Start Server",
        description="Requires Setup Database to be done",
    )

    edges = infer_dependencies([a1, a2], tenant_id)

    assert len(edges) == 1
    assert edges[0].source_id == a1.id
    assert edges[0].target_id == a2.id
    assert edges[0].relation_type == EdgeRelationType.DEPENDS_ON


def test_conflict_resolution() -> None:
    tenant_id = uuid.uuid4()

    a1 = Action(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="Payment Policy",
        description="We should approve all payment refunds.",
    )
    a2 = Action(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="Payment Policy Updates",
        description="We must reject all payment refunds immediately.",
    )

    reports = detect_contradictory_actions([a1, a2])

    assert len(reports) == 1
    assert reports[0].action_ids == [a1.id, a2.id]

    # Assert flags are set
    assert a1.confidence == ConfidenceLevel.CONFLICT
    assert a2.confidence == ConfidenceLevel.CONFLICT


def test_complex_graph_cycle_resolution() -> None:
    from app.domain.action_graph import resolve_cycles

    tenant_id = uuid.uuid4()

    # Create actions first
    action_list = [
        Action(id=uuid.uuid4(), tenant_id=tenant_id, title=f"Action {i}", description="")
        for i in range(5)
    ]
    # Create map by ID
    actions = {a.id: a for a in action_list}

    # Complex 5-task DAG: 0 -> 1 -> 2 -> 3 -> 4
    edges = [
        ActionEdge(
            source_id=action_list[0].id,
            target_id=action_list[1].id,
            relation_type=EdgeRelationType.DEPENDS_ON,
        ),
        ActionEdge(
            source_id=action_list[1].id,
            target_id=action_list[2].id,
            relation_type=EdgeRelationType.DEPENDS_ON,
        ),
        ActionEdge(
            source_id=action_list[2].id,
            target_id=action_list[3].id,
            relation_type=EdgeRelationType.DEPENDS_ON,
        ),
        ActionEdge(
            source_id=action_list[3].id,
            target_id=action_list[4].id,
            relation_type=EdgeRelationType.DEPENDS_ON,
        ),
    ]

    # Check valid edge (no cycle)
    valid_edge = ActionEdge(
        source_id=action_list[1].id,
        target_id=action_list[4].id,
        relation_type=EdgeRelationType.DEPENDS_ON,
    )
    assert resolve_cycles(valid_edge, edges, actions) is False

    # Add a cyclic edge: 4 -> 0
    cyclic_edge = ActionEdge(
        source_id=action_list[4].id,
        target_id=action_list[0].id,
        relation_type=EdgeRelationType.DEPENDS_ON,
    )
    assert resolve_cycles(cyclic_edge, edges, actions) is True

    # Check that they are flagged
    assert actions[action_list[4].id].confidence == ConfidenceLevel.CONFLICT
    assert actions[action_list[0].id].confidence == ConfidenceLevel.CONFLICT
