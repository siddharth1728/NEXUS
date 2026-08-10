import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.database import Base, get_db
from app.core.config import settings

# Test database uses a separate test URL
engine = create_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

from app.dependencies.rate_limit import RATE_LIMIT_STORE
@pytest.fixture(autouse=True)
def clear_rate_limit():
    RATE_LIMIT_STORE.clear()

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def csrf_token(client):
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    token = response.cookies.get("csrf_token")
    return token

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db_session):
    from app.models.user import User
    from app.core.security import get_password_hash
    user = db_session.query(User).filter(User.email == "test_fixture@example.com").first()
    if not user:
        user = User(
            email="test_fixture@example.com",
            password_hash=get_password_hash("password123")
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, csrf_token, test_user):
    resp = client.post(
        "/api/auth/login",
        json={"email": "test_fixture@example.com", "password": "password123"},
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token}
    )
    assert resp.status_code == 200
    access = resp.cookies.get("access_token")
    # For testing routes that depend on cookie auth, we can just use client with cookies
    # But for headers, we can yield cookies dictionary
    return {"access_token": access}

# Override client to use cookies automatically
@pytest.fixture
def auth_client(client, auth_headers, csrf_token):
    client.cookies.set("access_token", auth_headers["access_token"])
    client.cookies.set("csrf_token", csrf_token)
    client.headers.update({"X-CSRF-Token": csrf_token})
    return client
