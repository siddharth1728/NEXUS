import secrets
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from typing import Optional

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

def generate_csrf_token() -> str:
    return secrets.token_hex(32)

def set_csrf_cookie(response: Response, token: str, secure: bool = False):
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,  # Needs to be readable by JS to include in the header
        secure=secure,
        samesite="lax"
    )

def verify_csrf_token(request: Request):
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)

    if not cookie_token or not header_token or cookie_token != header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token verification failed"
        )
