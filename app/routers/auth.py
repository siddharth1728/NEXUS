from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services import auth_service
from app.dependencies.auth import get_current_user
from app.dependencies.rate_limit import rate_limit
from app.core.csrf import verify_csrf_token, set_csrf_cookie, generate_csrf_token
from app.core.config import settings

router = APIRouter()

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    secure_cookie = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

@router.get("/csrf")
def get_csrf(response: Response):
    # Endpoint to issue a new CSRF token for the frontend shell
    token = generate_csrf_token()
    set_csrf_cookie(response, token, secure=settings.ENVIRONMENT == "production")
    return {"message": "CSRF token set"}

@router.post("/register", response_model=UserResponse, dependencies=[Depends(rate_limit), Depends(verify_csrf_token)])
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return auth_service.register_user(db, user_data)

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit), Depends(verify_csrf_token)])
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, user_data)
    
    access_token = auth_service.create_access_token(subject=str(user.id))
    refresh_token = auth_service.create_refresh_session(db, user.id)
    
    set_auth_cookies(response, access_token, refresh_token)
    return {"message": "Login successful", "user": user}

@router.post("/refresh", dependencies=[Depends(rate_limit), Depends(verify_csrf_token)])
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
        
    new_access_token, new_refresh_token = auth_service.refresh_access_token(db, refresh_token)
    set_auth_cookies(response, new_access_token, new_refresh_token)
    return {"message": "Token refreshed"}

from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services.email_service import send_password_reset_email
from app.models.user import User

@router.post("/forgot-password", dependencies=[Depends(rate_limit), Depends(verify_csrf_token)])
def forgot_password(request_data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request_data.email).first()
    
    if user:
        raw_token = auth_service.create_password_reset_token(db, user.id)
        reset_url = f"{settings.APP_BASE_URL}/reset-password?token={raw_token}"
        send_password_reset_email(user.email, reset_url)
        
    # ALWAYS return the generic success response to prevent enumeration
    return {"message": "If an account exists for this email, you'll receive a password reset link."}

@router.post("/reset-password", dependencies=[Depends(rate_limit), Depends(verify_csrf_token)])
def reset_password(request_data: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password(db, request_data.token, request_data.new_password)
    return {"message": "Password has been successfully reset."}

@router.post("/logout", dependencies=[Depends(verify_csrf_token)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        auth_service.revoke_refresh_session_by_token(db, refresh_token)
        
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user
