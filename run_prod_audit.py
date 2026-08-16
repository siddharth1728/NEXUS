import httpx
import uuid
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_URL = "https://nexus-nchn.onrender.com"
client = httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=30.0)

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def run():
    print_header("4. HEALTH CHECK")
    r = client.get("/health")
    if r.status_code == 200:
        print("✅ PASS: /health HTTP 200")
    else:
        print(f"⚠️ WARNING: /health returned {r.status_code}")

    print_header("5. BASIC PUBLIC AVAILABILITY")
    paths = ["/", "/login", "/register"]
    for p in paths:
        r = client.get(p)
        if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
            print(f"✅ PASS: {p} loads successfully (HTTP 200)")
        else:
            print(f"❌ FAIL: {p} returned {r.status_code}")

    print_header("6. PRODUCTION AUTHENTICATION")
    test_id = str(uuid.uuid4())[:8]
    email = f"audit_{test_id}@example.com"
    password = "AuditPassword123!"

    # Register
    r = client.post("/register", data={"full_name": "Audit User", "email": email, "password": password})
    if r.status_code == 200 and "dashboard" in str(r.url) or "onboarding" in str(r.url):
        print("✅ PASS: Registration successful, redirected correctly.")
    else:
        print(f"❌ FAIL: Registration returned {r.status_code} - {r.url}")

    # Logout
    r = client.get("/logout")
    if r.status_code == 200 and "login" in str(r.url):
        print("✅ PASS: Logout successful.")
    
    # Login again
    r = client.post("/login", data={"username": email, "password": password})
    if r.status_code == 200 and ("dashboard" in str(r.url) or "onboarding" in str(r.url)):
        print("✅ PASS: Login successful.")
    else:
        print(f"❌ FAIL: Login returned {r.status_code} - {r.url}")
        
    print_header("21. AUTH COOKIE / SESSION TEST")
    access_token = client.cookies.get("access_token")
    if access_token:
        print("✅ PASS: Cookie 'access_token' is present.")
    else:
        print("❌ FAIL: Cookie 'access_token' missing.")
        
    print_header("7. PASSWORD RESET (API Check)")
    r = client.post("/api/auth/forgot-password", json={"email": email})
    if r.status_code in [200, 202]:
        print(f"✅ PASS: Forgot password accepted for {email}.")
    else:
        print(f"❌ FAIL: Forgot password returned {r.status_code}")
        
    # IDOR Check (Try to access a random project)
    print_header("20. CROSS-USER IDOR TEST")
    r = client.get("/api/projects/999999")
    if r.status_code in [403, 404]:
        print(f"✅ PASS: Unauthorized project access blocked (HTTP {r.status_code})")
    else:
        print(f"❌ FAIL: IDOR vulnerability! Returned {r.status_code}")
        
    print_header("14. NEXUS ID PRODUCTION TEST")
    r_public = httpx.get(f"{BASE_URL}/id/audit_user")
    if r_public.status_code in [404, 403]:
        print(f"✅ PASS: Public profile not exposed by default (HTTP {r_public.status_code})")
        
    print("Audit checks completed.")

if __name__ == "__main__":
    run()
