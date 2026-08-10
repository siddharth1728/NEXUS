import pytest
from unittest.mock import patch, MagicMock
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, SnapshotStatus

def test_project_creation(client, csrf_token):
    # Register & Login first
    client.post(
        "/api/auth/register",
        json={"email": "project1@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "project1@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    access_cookie = login_resp.cookies.get("access_token")

    # Create project
    resp = client.post(
        "/api/projects/",
        json={"github_repo_id": 12345, "name": "test-repo"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token, "access_token": access_cookie}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "test-repo"
    assert data["github_repo_id"] == 12345

def test_project_ownership_isolation(client, csrf_token):
    # User 1
    client.post(
        "/api/auth/register",
        json={"email": "user1@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    login1 = client.post(
        "/api/auth/login",
        json={"email": "user1@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    access1 = login1.cookies.get("access_token")

    # User 1 creates project
    p1 = client.post(
        "/api/projects/",
        json={"github_repo_id": 111, "name": "repo1"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token, "access_token": access1}
    ).json()

    # User 2
    client.post(
        "/api/auth/register",
        json={"email": "user2@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    login2 = client.post(
        "/api/auth/login",
        json={"email": "user2@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    access2 = login2.cookies.get("access_token")

    # User 2 tries to access User 1's project
    resp = client.get(
        f"/api/projects/{p1['id']}",
        cookies={"access_token": access2}
    )
    assert resp.status_code == 404

@patch("app.services.project_service.github_service.get_repository_metadata")
@patch("app.services.project_service.github_service.get_repository_branch_head")
@patch("app.services.project_service.github_service.get_repository_tree")
@patch("app.services.project_service.github_service.get_file_content")
def test_project_sync(mock_file, mock_tree, mock_head, mock_meta, client, csrf_token):
    # Setup mock returns
    mock_meta.return_value = {"default_branch": "main"}
    mock_head.return_value = "commit123"
    mock_tree.return_value = {
        "tree": [
            {"path": "app/main.py", "type": "blob", "size": 100},
            {"path": "node_modules/test.js", "type": "blob", "size": 100}
        ],
        "truncated": False
    }
    mock_file.return_value = "from fastapi import FastAPI\n"

    # User setup
    client.post("/api/auth/register", json={"email": "sync@example.com", "password": "securepassword123"}, headers={"X-CSRF-Token": csrf_token}, cookies={"csrf_token": csrf_token})
    login = client.post("/api/auth/login", json={"email": "sync@example.com", "password": "securepassword123"}, headers={"X-CSRF-Token": csrf_token}, cookies={"csrf_token": csrf_token})
    access = login.cookies.get("access_token")

    # Must set github_username to sync
    client.put("/api/profile", json={"github_username": "syncuser"}, headers={"X-CSRF-Token": csrf_token}, cookies={"csrf_token": csrf_token, "access_token": access})

    # Create project
    p = client.post("/api/projects/", json={"github_repo_id": 999, "name": "sync-repo"}, headers={"X-CSRF-Token": csrf_token}, cookies={"csrf_token": csrf_token, "access_token": access}).json()

    # Sync
    resp = client.post(f"/api/projects/{p['id']}/sync", headers={"X-CSRF-Token": csrf_token}, cookies={"csrf_token": csrf_token, "access_token": access})
    assert resp.status_code == 200
    snapshot = resp.json()
    
    assert snapshot["status"] == "COMPLETED"
    assert snapshot["artifact_count"] == 1
    assert snapshot["observation_count"] == 1

    # Check observations
    obs_resp = client.get(f"/api/snapshots/{snapshot['id']}/observations", cookies={"access_token": access})
    observations = obs_resp.json()
    assert len(observations) == 1
    assert observations[0]["observation_text"] == "FastAPI import detected"

    # Double sync protection - mock one active
    # We can just verify snapshot history contains 1
    hist = client.get(f"/api/projects/{p['id']}/snapshots", cookies={"access_token": access})
    assert len(hist.json()) == 1

    # Sync again -> should create snapshot 2
    mock_head.return_value = "commit456"
    resp2 = client.post(f"/api/projects/{p['id']}/sync", headers={"X-CSRF-Token": csrf_token}, cookies={"csrf_token": csrf_token, "access_token": access})
    assert resp2.status_code == 200
    
    hist2 = client.get(f"/api/projects/{p['id']}/snapshots", cookies={"access_token": access})
    assert len(hist2.json()) == 2
