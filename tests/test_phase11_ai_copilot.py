import pytest
from app.models.user import User, UserSkill, Gap, SkillState
from app.models.profile import StudentProfile
from app.models.taxonomy import TargetRole, Skill, TargetRoleSkill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceType, EvidenceSkill, SnapshotStatus

def clean_state(db, user_id):
    db.query(EvidenceSkill).filter(EvidenceSkill.evidence_id.in_(
        db.query(Evidence.id).filter(Evidence.raw_observation_id.in_(
            db.query(RawObservation.id).filter(RawObservation.artifact_id.in_(
                db.query(Artifact.id).filter(Artifact.snapshot_id.in_(
                    db.query(RepositorySnapshot.id).filter(RepositorySnapshot.project_id.in_(
                        db.query(Project.id).filter(Project.user_id == user_id)
                    ))
                ))
            ))
        ))
    )).delete(synchronize_session=False)
    db.query(Evidence).filter(Evidence.raw_observation_id.in_(
        db.query(RawObservation.id).filter(RawObservation.artifact_id.in_(
            db.query(Artifact.id).filter(Artifact.snapshot_id.in_(
                db.query(RepositorySnapshot.id).filter(RepositorySnapshot.project_id.in_(
                    db.query(Project.id).filter(Project.user_id == user_id)
                ))
            ))
        ))
    )).delete(synchronize_session=False)
    db.query(RawObservation).filter(RawObservation.artifact_id.in_(
        db.query(Artifact.id).filter(Artifact.snapshot_id.in_(
            db.query(RepositorySnapshot.id).filter(RepositorySnapshot.project_id.in_(
                db.query(Project.id).filter(Project.user_id == user_id)
            ))
        ))
    )).delete(synchronize_session=False)
    db.query(Artifact).filter(Artifact.snapshot_id.in_(
        db.query(RepositorySnapshot.id).filter(RepositorySnapshot.project_id.in_(
            db.query(Project.id).filter(Project.user_id == user_id)
        ))
    )).delete(synchronize_session=False)
    db.query(RepositorySnapshot).filter(RepositorySnapshot.project_id.in_(
        db.query(Project.id).filter(Project.user_id == user_id)
    )).delete(synchronize_session=False)
    db.query(Project).filter(Project.user_id == user_id).delete(synchronize_session=False)
    db.query(Gap).filter(Gap.user_id == user_id).delete(synchronize_session=False)
    db.query(UserSkill).filter(UserSkill.user_id == user_id).delete(synchronize_session=False)
    db.commit()

def test_unauthenticated_copilot_rejected(client):
    res = client.post("/api/copilot/ask", json={"query": "Explain my project"})
    assert res.status_code == 401

def test_ask_copilot_grounded_response(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    s_sql = db_session.query(Skill).filter(Skill.name == "SQL").first()
    if not s_sql:
        s_sql = Skill(name="SQL", category="Database", description="SQL queries")
        db_session.add(s_sql)
        db_session.commit()

    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_sql.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.commit()

    res = auth_client.post(
        "/api/copilot/ask",
        json={"query": "Why does NEXUS think I'm weak at testing?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verified_context_used"] is True
    assert "NEXUS evaluates skill signals" in data["response"] or "test" in data["response"].lower()
    assert data["related_lab_concept"] == "AUTOMATED_TESTING"
    assert data["related_proof_quest"] == "ADD_BASIC_TEST_SUITE"

def test_hallucination_rejection_unverified_claim(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    p = Project(user_id=test_user.id, github_repo_id=901, name="NexusAPI")
    db_session.add(p)
    db_session.commit()

    res = auth_client.post(
        "/api/copilot/ask",
        json={"query": "Explain how I used Redis in my project.", "project_id": p.id}
    )
    assert res.status_code == 200
    data = res.json()
    assert "I don't see verified Redis evidence" in data["response"]

def test_defend_your_build_lifecycle(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    p = Project(user_id=test_user.id, github_repo_id=902, name="NexusAPI")
    db_session.add(p)
    db_session.commit()

    snap = RepositorySnapshot(project_id=p.id, commit_sha="abc1234", branch="main", status=SnapshotStatus.COMPLETED)
    db_session.add(snap)
    db_session.commit()

    art = Artifact(snapshot_id=snap.id, file_path="app/db/postgres.py", type="PYTHON_FILE")
    db_session.add(art)
    db_session.commit()

    obs = RawObservation(artifact_id=art.id, observation_text="PostgreSQL connection pool initialized")
    db_session.add(obs)
    db_session.commit()

    ev = Evidence(raw_observation_id=obs.id, type=EvidenceType.DATABASE, quality_score=0.9, freshness_weight=1.0, source_reference="app/db/postgres.py")
    db_session.add(ev)
    db_session.commit()

    # 1. Start Interview
    res_start = auth_client.post(
        "/api/copilot/interview/start",
        json={"project_id": p.id, "difficulty": "INTERMEDIATE"}
    )
    assert res_start.status_code == 200
    session_data = res_start.json()
    session_id = session_data["session_id"]
    assert session_data["project_name"] == "NexusAPI"
    assert session_data["question_index"] == 1

    # 2. Answer Question 1
    res_ans1 = auth_client.post(
        "/api/copilot/interview/answer",
        json={
            "session_id": session_id,
            "answer": "We chose PostgreSQL to ensure ACID transactional guarantees and relational consistency across our core tables."
        }
    )
    assert res_ans1.status_code == 200
    ans1_data = res_ans1.json()
    assert ans1_data["feedback"]["status"] == "STRONG_EXPLANATION"
    assert ans1_data["is_finished"] is False

    # 3. Answer Question 2
    res_ans2 = auth_client.post(
        "/api/copilot/interview/answer",
        json={
            "session_id": session_id,
            "answer": "We write tests with pytest to prevent regressions across endpoints."
        }
    )
    assert res_ans2.status_code == 200
    assert res_ans2.json()["is_finished"] is False

    # 4. Answer Question 3 (Finish)
    res_ans3 = auth_client.post(
        "/api/copilot/interview/answer",
        json={
            "session_id": session_id,
            "answer": "We enforce perimeter schema validation using Pydantic models."
        }
    )
    assert res_ans3.status_code == 200
    ans3_data = res_ans3.json()
    assert ans3_data["is_finished"] is True
    assert ans3_data["summary"] is not None
    assert "topics_discussed" in ans3_data["summary"]
    assert "suggested_lab_concepts" in ans3_data["summary"]

def test_cross_user_isolation_copilot(client, db_session, test_user):
    clean_state(db_session, test_user.id)

    # Project owned by test_user
    p = Project(user_id=test_user.id, github_repo_id=903, name="NexusAPI")
    db_session.add(p)
    db_session.commit()

    # Create User B
    user_b = User(email="hacker@nexus.test", password_hash="pw")
    db_session.add(user_b)
    db_session.commit()

    from app.core.security import create_access_token
    token_b = create_access_token(user_b.id)

    # User B attempts to start an interview on User A's project
    res = client.post(
        "/api/copilot/interview/start",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"project_id": p.id, "difficulty": "INTERMEDIATE"}
    )
    assert res.status_code == 404

def test_critical_truth_contract_preservation(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    s_sql = db_session.query(Skill).filter(Skill.name == "SQL").first()
    if not s_sql:
        s_sql = Skill(name="SQL", category="Database", description="SQL queries")
        db_session.add(s_sql)
        db_session.commit()

    us = UserSkill(user_id=test_user.id, skill_id=s_sql.id, state=SkillState.STRONG, calculation_version="v1")
    gap = Gap(
        user_id=test_user.id,
        skill_id=s_sql.id,
        actual_state="DEVELOPING",
        required_state="STRONG",
        state_distance=1,
        importance_weight=1.0,
        severity=1.0,
        calculation_version="v1"
    )
    p = Project(user_id=test_user.id, github_repo_id=904, name="NexusAPI")
    db_session.add_all([us, gap, p])
    db_session.commit()

    skills_before = [(s.skill_id, s.state.value) for s in db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id).all()]
    gaps_before = [(g.skill_id, g.severity) for g in db_session.query(Gap).filter(Gap.user_id == test_user.id).all()]

    # Ask multiple questions and start interview
    auth_client.post(
        "/api/copilot/ask",
        json={"query": "Explain everything about my skills", "project_id": p.id}
    )

    res_start = auth_client.post(
        "/api/copilot/interview/start",
        json={"project_id": p.id, "difficulty": "ADVANCED"}
    )
    session_id = res_start.json()["session_id"]
    for i in range(3):
        auth_client.post(
            "/api/copilot/interview/answer",
            json={"session_id": session_id, "answer": "Demonstrating expert architecture and database sharding"}
        )

    # Verify ZERO mutations to UserSkill and Gap
    skills_after = [(s.skill_id, s.state.value) for s in db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id).all()]
    gaps_after = [(g.skill_id, g.severity) for g in db_session.query(Gap).filter(Gap.user_id == test_user.id).all()]

    assert skills_before == skills_after
    assert gaps_before == gaps_after
