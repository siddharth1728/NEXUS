import pytest
from app.models.taxonomy import TargetRole, Skill, TargetRoleSkill
from app.models.profile import StudentProfile
from app.models.user import User, Gap

def test_unauthenticated_access_rejected(client):
    response = client.get("/api/gaps")
    assert response.status_code == 401

def test_get_gaps(auth_client, db_session, test_user):
    # Setup TargetRole, Profile, Skills, Gap
    import uuid
    role = TargetRole(name=f"Data Engineer_{uuid.uuid4()}")
    db_session.add(role)
    db_session.commit()
    
    profile = StudentProfile(user_id=test_user.id, target_role_id=role.id)
    db_session.add(profile)
    db_session.commit()
    
    import uuid
    skill1 = Skill(name=f"Python_{uuid.uuid4()}", category="Language")
    skill2 = Skill(name=f"SQL_{uuid.uuid4()}", category="Database")
    db_session.add(skill1)
    db_session.add(skill2)
    db_session.commit()
    
    gap1 = Gap(
        user_id=test_user.id,
        skill_id=skill1.id,
        actual_state="MISSING",
        required_state="DEVELOPING",
        state_distance=2,
        importance_weight=1.0,
        severity=2.0,
        calculation_version="gap_v1"
    )
    gap2 = Gap(
        user_id=test_user.id,
        skill_id=skill2.id,
        actual_state="WEAK",
        required_state="STRONG",
        state_distance=2,
        importance_weight=2.0,
        severity=4.0,
        calculation_version="gap_v1"
    )
    db_session.add(gap1)
    db_session.add(gap2)
    db_session.commit()
    
    response = auth_client.get("/api/gaps")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Sorting test: Severity DESC
    assert data[0]["severity"] == 4.0
    assert data[0]["skill"].startswith("SQL")
    
    assert data[1]["severity"] == 2.0
    assert data[1]["skill"].startswith("Python")
    
    # Assert factual response, no recommendations
    assert "recommendation" not in data[0]
    assert "build" not in str(data[0]).lower()

def test_cross_user_access_isolated(auth_client, db_session, test_user):
    # Setup another user's gap
    import uuid
    other_user = User(email=f"other_{uuid.uuid4()}@example.com", password_hash="pw")
    db_session.add(other_user)
    db_session.commit()
    
    skill = Skill(name=f"Rust_{uuid.uuid4()}", category="Language")
    db_session.add(skill)
    db_session.commit()
    
    gap = Gap(
        user_id=other_user.id,
        skill_id=skill.id,
        actual_state="MISSING",
        required_state="STRONG",
        state_distance=3,
        importance_weight=1.0,
        severity=3.0,
        calculation_version="gap_v1"
    )
    db_session.add(gap)
    db_session.commit()
    
    # auth_client is test_user. They should not see other_user's gap
    response = auth_client.get("/api/gaps")
    assert response.status_code == 200
    data = response.json()
    
    # Assuming test_user might have gaps from previous tests, just ensure they don't see other_user's gap
    rust_gaps = [g for g in data if g["skill"].startswith("Rust")]
    assert len(rust_gaps) == 0
