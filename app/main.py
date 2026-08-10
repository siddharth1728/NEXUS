from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
import os

from app.routers import auth, profile, github, projects, snapshots, evidence, skills, gaps, nba

app = FastAPI(title="NEXUS")

# Ensure static and templates dirs exist
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(github.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(snapshots.router, prefix="/api")
app.include_router(evidence.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(gaps.router, prefix="/api")
app.include_router(nba.router, prefix="/api")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

from app.core.csrf import generate_csrf_token, set_csrf_cookie

def render_with_csrf(request: Request, template_name: str):
    token = generate_csrf_token()
    response = templates.TemplateResponse(request, template_name, {"csrf_token": token})
    set_csrf_cookie(response, token)
    return response

# ── Frontend Routes ──────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def index(request: Request):
    return render_with_csrf(request, "dashboard.html")

@app.get("/login", response_class=HTMLResponse, tags=["Frontend"])
def login_page(request: Request):
    return render_with_csrf(request, "login.html")

@app.get("/register", response_class=HTMLResponse, tags=["Frontend"])
def register_page(request: Request):
    return render_with_csrf(request, "register.html")

@app.get("/onboarding", response_class=HTMLResponse, tags=["Frontend"])
def onboarding_page(request: Request):
    return render_with_csrf(request, "onboarding.html")

@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend"])
def dashboard_page(request: Request):
    return render_with_csrf(request, "dashboard.html")

@app.get("/projects", response_class=HTMLResponse, tags=["Frontend"])
def projects_page(request: Request):
    return render_with_csrf(request, "projects.html")

@app.get("/skills", response_class=HTMLResponse, tags=["Frontend"])
def skills_page(request: Request):
    return render_with_csrf(request, "skills.html")

@app.get("/evidence", response_class=HTMLResponse, tags=["Frontend"])
def evidence_page(request: Request):
    return render_with_csrf(request, "evidence.html")

@app.get("/gaps", response_class=HTMLResponse, tags=["Frontend"])
def gaps_page(request: Request):
    return render_with_csrf(request, "gaps.html")

@app.get("/profile", response_class=HTMLResponse, tags=["Frontend"])
def profile_page(request: Request):
    return render_with_csrf(request, "profile.html")

@app.get("/settings", response_class=HTMLResponse, tags=["Frontend"])
def settings_page(request: Request):
    return render_with_csrf(request, "profile.html")
