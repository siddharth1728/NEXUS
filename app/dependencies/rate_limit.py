from fastapi import Request, HTTPException, status
from collections import defaultdict
import time

# Lightweight in-memory rate limiter for V1
# Structure: { ip_address: [timestamp1, timestamp2, ...] }
RATE_LIMIT_STORE = defaultdict(list)
MAX_REQUESTS = 5
WINDOW_SECONDS = 60

def rate_limit(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    
    # Filter old requests
    RATE_LIMIT_STORE[client_ip] = [ts for ts in RATE_LIMIT_STORE[client_ip] if now - ts < WINDOW_SECONDS]
    
    if len(RATE_LIMIT_STORE[client_ip]) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
    
    RATE_LIMIT_STORE[client_ip].append(now)
