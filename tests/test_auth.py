import pytest
from app.models.user import User

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_register_user(client, csrf_token):
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data
    assert "password_hash" not in data

def test_register_duplicate_email(client, csrf_token):
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response.status_code == 409

def test_login_success_and_httponly_cookies(client, csrf_token):
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response.status_code == 200
    
    # Check that HTTP-Only cookies are set
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies

def test_missing_csrf_token(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]

def test_protected_route_without_auth(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_refresh_token_rotation(client, csrf_token):
    # First login to get tokens
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    old_access = login_resp.cookies.get("access_token")
    old_refresh = login_resp.cookies.get("refresh_token")
    
    # Refresh
    refresh_resp = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token, "refresh_token": old_refresh}
    )
    assert refresh_resp.status_code == 200
    new_access = refresh_resp.cookies.get("access_token")
    new_refresh = refresh_resp.cookies.get("refresh_token")
    
    assert new_access != old_access
    assert new_refresh != old_refresh

    # Try reusing old refresh token (should fail)
    fail_resp = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token, "refresh_token": old_refresh}
    )
    assert fail_resp.status_code == 401
