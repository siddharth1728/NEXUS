import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, RefreshSession
from app.schemas.auth import UserCreate, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

def register_user(db: Session, user_data: UserCreate) -> User:
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, user_data: UserLogin) -> User:
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

def create_refresh_session(db: Session, user_id: int) -> str:
    raw_token = secrets.token_hex(32)
    token_hash = get_password_hash(raw_token)
    
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_session = RefreshSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(new_session)
    db.commit()
    return raw_token

def revoke_refresh_session(db: Session, user_id: int, raw_token: str):
    # Find active session
    sessions = db.query(RefreshSession).filter(
        RefreshSession.user_id == user_id,
        RefreshSession.revoked_at == None
    ).all()
    
    for session in sessions:
        if verify_password(raw_token, session.token_hash):
            session.revoked_at = datetime.utcnow()
            db.commit()
            return
            
    # If we get here, token was not found or already revoked
    pass

def refresh_access_token(db: Session, raw_token: str) -> tuple[str, str]:
    # Need to scan all non-revoked sessions for this token hash
    # In a real app we might store the session ID in the token, but for now we iterate (or use a better lookup)
    sessions = db.query(RefreshSession).filter(
        RefreshSession.revoked_at == None,
        RefreshSession.expires_at > datetime.utcnow()
    ).all()
    
    valid_session = None
    for session in sessions:
        if verify_password(raw_token, session.token_hash):
            valid_session = session
            break
            
    if not valid_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
        
    # Token rotation: revoke old session, create new one
    valid_session.revoked_at = datetime.utcnow()
    db.commit()
    
    user_id = valid_session.user_id
    new_refresh_token = create_refresh_session(db, user_id)
    new_access_token = create_access_token(subject=str(user_id))
    
    return new_access_token, new_refresh_token
