import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_public_routes_render_correctly():
    client = TestClient(app)
    
    public_routes = [
        "/login",
        "/register",
        "/forgot-password",
        "/reset-password?token=dummy",
    ]
    
    for route in public_routes:
        resp = client.get(route)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        # Basic check to ensure the atlas UI string is present (we added "ENGINEERING ATLAS" to auth pages)
        assert "ENGINEERING ATLAS" in resp.text

def test_protected_routes_render_authenticated(auth_client, db_session, test_user):
    # Setup minimal data for dynamic routes
    from app.models.taxonomy import Skill
    from app.models.project import Project
    
    skill = Skill(name="TestSkill", category="TestCat")
    project = Project(user_id=test_user.id, github_repo_id=1, name="TestProject")
    
    db_session.add(skill)
    db_session.add(project)
    db_session.commit()
    
    protected_routes = [
        "/",
        "/journey",
        "/projects",
        "/skills",
        "/gaps",
        "/profile",
        "/settings",
        "/onboarding"
    ]
    
    for route in protected_routes:
        resp = auth_client.get(route)
        assert resp.status_code == 200, f"Route {route} failed with status {resp.status_code}"
        assert "text/html" in resp.headers["content-type"]
        # Basic check for new Atlas base.html header
        if route != "/onboarding":
            assert "NEXUS" in resp.text
            assert "Atlas" in resp.text or "ATLAS" in resp.text

def test_api_identity_has_new_fields(auth_client):
    resp = auth_client.get("/api/identity")
    assert resp.status_code == 200
    data = resp.json()
    assert "github_username" in data
    assert "last_synced" in data
    assert "atlas_territories" in data
    assert "engineering_journey" in data
