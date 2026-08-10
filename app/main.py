from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
import os

from app.routers import auth, profile, github, projects, snapshots, evidence, skills, gaps

app = FastAPI(title="NEXUS Phase 1")

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

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def index(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"csrf_token": ""})

@app.get("/login", response_class=HTMLResponse, tags=["Frontend"])
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"csrf_token": ""})

@app.get("/register", response_class=HTMLResponse, tags=["Frontend"])
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"csrf_token": ""})

@app.get("/onboarding", response_class=HTMLResponse, tags=["Frontend"])
def onboarding_page(request: Request):
    return templates.TemplateResponse(request, "onboarding.html", {"csrf_token": ""})
