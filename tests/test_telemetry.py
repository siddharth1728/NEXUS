import pytest
from sqlalchemy.orm import Session
from app.models.telemetry import ProductEvent, ProductFeedback
from app.services.telemetry_service import record_event, record_feedback
from app.models.user import User

def test_record_event(db_session: Session, test_user: User):
    event = record_event(db_session, "ATLAS_VIEWED", test_user.id, {"source": "test"})
    assert event is not None
    assert event.event_type == "ATLAS_VIEWED"
    assert event.user_id == test_user.id
    assert event.context_data == {"source": "test"}

def test_record_feedback(db_session: Session, test_user: User):
    feedback = record_feedback(db_session, test_user.id, "copilot", True, "Great!")
    assert feedback is not None
    assert feedback.feature_context == "copilot"
    assert feedback.is_helpful is True
    assert feedback.reason == "Great!"

def test_invalid_event_type(db_session: Session, test_user: User):
    with pytest.raises(ValueError):
        record_event(db_session, "INVALID_EVENT", test_user.id)

def test_api_post_event(client, test_user: User, auth_headers):
    response = client.post(
        "/api/telemetry/event",
        headers=auth_headers,
        json={"event_type": "PROJECT_INTELLIGENCE_VIEWED", "context": {"project_id": 1}}
    )
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"

def test_api_internal_health_denied_for_regular_user(client, db_session: Session, test_user: User, auth_headers):
    # test_user is not internal by default
    test_user.is_internal = False
    db_session.commit()
    
    response = client.get(
        "/api/telemetry/internal/health",
        headers=auth_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access forbidden: Internal role required"

def test_config_flags(client):
    response = client.get("/api/telemetry/config/flags")
    assert response.status_code == 200
    flags = response.json()
    assert "ai_copilot" in flags
    assert "proof_quests" in flags
