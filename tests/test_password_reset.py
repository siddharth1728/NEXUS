import pytest
import time
from datetime import datetime, timedelta
from app.models.user import User, PasswordResetToken, RefreshSession
from app.core.security import get_password_hash, verify_password
import secrets
import hashlib

@pytest.fixture
def pw_test_user(db_session):
    user = User(
        email=f"pw_reset_{secrets.token_hex(4)}@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_forgot_password_valid_email(client, csrf_token, pw_test_user, db_session):
    response = client.post(
        "/api/auth/forgot-password",
        json={"email": pw_test_user.email},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response.status_code == 200
    assert "If an account exists" in response.json()["message"]
    
    # Verify token was created
    token = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == pw_test_user.id).first()
    assert token is not None
    assert token.used_at is None
    # Token hash should not be in the response
    assert str(token.token_hash) not in response.text

def test_forgot_password_invalid_email(client, csrf_token):
    response = client.post(
        "/api/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    # The response should be EXACTLY the same as for a valid email
    assert response.status_code == 200
    assert "If an account exists" in response.json()["message"]

def test_forgot_password_no_token_leak(client, csrf_token, pw_test_user):
    response = client.post(
        "/api/auth/forgot-password",
        json={"email": pw_test_user.email},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert "token=" not in response.text

def test_reset_password_success_and_invalidates_sessions(client, csrf_token, db_session, pw_test_user):
    # Setup: Create a refresh session
    client.post(
        "/api/auth/login",
        json={"email": pw_test_user.email, "password": "password123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    active_sessions = db_session.query(RefreshSession).filter(RefreshSession.user_id == pw_test_user.id, RefreshSession.revoked_at == None).count()
    assert active_sessions > 0
    
    # Generate token directly
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    reset_token = PasswordResetToken(
        user_id=pw_test_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db_session.add(reset_token)
    db_session.commit()
    
    # Attempt reset
    new_password = "newsecurepassword456"
    response = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": new_password},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response.status_code == 200
    
    # Verify password changed
    db_session.refresh(pw_test_user)
    assert verify_password(new_password, pw_test_user.password_hash)
    
    # Verify token used
    db_session.refresh(reset_token)
    assert reset_token.used_at is not None
    
    # Verify ALL refresh sessions are revoked
    active_sessions = db_session.query(RefreshSession).filter(RefreshSession.user_id == pw_test_user.id, RefreshSession.revoked_at == None).count()
    assert active_sessions == 0
    
    # Verify old password fails
    login_response = client.post(
        "/api/auth/login",
        json={"email": pw_test_user.email, "password": "password123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert login_response.status_code == 401

def test_reset_password_single_use(client, csrf_token, db_session, pw_test_user):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    reset_token = PasswordResetToken(
        user_id=pw_test_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db_session.add(reset_token)
    db_session.commit()
    
    # First use
    response1 = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "newsecurepassword1"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response1.status_code == 200
    
    # Second use
    response2 = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "newsecurepassword2"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response2.status_code == 400
    assert "already used" in response2.json()["detail"].lower()

def test_reset_password_expired(client, csrf_token, db_session, pw_test_user):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Set expiration in the past
    reset_token = PasswordResetToken(
        user_id=pw_test_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() - timedelta(minutes=1)
    )
    db_session.add(reset_token)
    db_session.commit()
    
    response = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "newsecurepassword1"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

def test_reset_password_invalidates_other_outstanding(client, csrf_token, db_session, pw_test_user):
    # Token 1
    raw1 = secrets.token_urlsafe(32)
    t1 = PasswordResetToken(user_id=pw_test_user.id, token_hash=hashlib.sha256(raw1.encode()).hexdigest(), expires_at=datetime.utcnow() + timedelta(minutes=30))
    # Token 2
    raw2 = secrets.token_urlsafe(32)
    t2 = PasswordResetToken(user_id=pw_test_user.id, token_hash=hashlib.sha256(raw2.encode()).hexdigest(), expires_at=datetime.utcnow() + timedelta(minutes=30))
    
    db_session.add_all([t1, t2])
    db_session.commit()
    
    # Use Token 2
    client.post(
        "/api/auth/reset-password",
        json={"token": raw2, "new_password": "newsecurepassword1"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    
    db_session.refresh(t1)
    db_session.refresh(t2)
    
    assert t2.used_at is not None
    assert t1.used_at is not None  # Should be invalidated

def test_anonymous_csrf(client):
    # Ensure CSRF token is issued on GET pages, including forgot password
    resp = client.get("/forgot-password")
    assert resp.status_code == 200
    assert "csrf_token" in resp.cookies
    
    token = resp.cookies.get("csrf_token")
    
    # Now use this token in a POST request
    post_resp = client.post(
        "/api/auth/forgot-password",
        json={"email": "anonymous_test@example.com"},
        headers={"X-CSRF-Token": token},
        cookies={"csrf_token": token}
    )
    assert post_resp.status_code == 200

def test_reset_password_short_password(client, csrf_token, db_session, pw_test_user):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    reset_token = PasswordResetToken(
        user_id=pw_test_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db_session.add(reset_token)
    db_session.commit()
    
    response = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "short"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert response.status_code == 422 # FastAPI validation error for length
