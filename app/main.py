from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from app.routers import auth, profile, github, projects, snapshots, evidence, skills, gaps, nba, identity, lab, copilot, nexus_id, ecosystem

app = FastAPI(title="NEXUS")

# Ensure static and templates dirs exist if filesystem is writable
try:
    (BASE_DIR / "static").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "templates").mkdir(parents=True, exist_ok=True)
except Exception:
    pass

@app.on_event("startup")
def on_startup():
    try:
        from app.database.database import Base, engine
        import app.models  # register all models
        Base.metadata.create_all(bind=engine)
        from app.db.seed import seed_taxonomy
        seed_taxonomy()
    except Exception as e:
        print(f"Startup notice: {e}")


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(github.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(snapshots.router, prefix="/api")
app.include_router(evidence.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(gaps.router, prefix="/api")
app.include_router(nba.router, prefix="/api")
app.include_router(identity.router, prefix="/api")
app.include_router(lab.router, prefix="/api")
app.include_router(copilot.router)
app.include_router(nexus_id.router)
app.include_router(ecosystem.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

from app.core.csrf import generate_csrf_token, set_csrf_cookie

def render_with_csrf(request: Request, template_name: str, extra_context: dict = None):
    token = generate_csrf_token()
    ctx = {"csrf_token": token}
    if extra_context:
        ctx.update(extra_context)
    response = templates.TemplateResponse(request, template_name, ctx)
    set_csrf_cookie(response, token)
    return response

# ── Frontend Routes ──────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def index(request: Request):
    return render_with_csrf(request, "dashboard.html")

@app.get("/login", response_class=HTMLResponse, tags=["Frontend"])
def login_page(request: Request):
    return render_with_csrf(request, "login.html")

@app.get("/forgot-password", response_class=HTMLResponse, tags=["Frontend"])
def forgot_password_page(request: Request):
    return render_with_csrf(request, "forgot_password.html")

@app.get("/reset-password", response_class=HTMLResponse, tags=["Frontend"])
def reset_password_page(request: Request):
    return render_with_csrf(request, "reset_password.html")

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

@app.get("/projects/{project_id}", response_class=HTMLResponse, tags=["Frontend"])
def project_detail_page(request: Request, project_id: int):
    return render_with_csrf(request, "project_detail.html")

@app.get("/lab", response_class=HTMLResponse, tags=["Frontend"])
def lab_page(request: Request):
    return render_with_csrf(request, "lab.html")

@app.get("/lab/{concept_key}", response_class=HTMLResponse, tags=["Frontend"])
def lab_detail_page(request: Request, concept_key: str):
    return render_with_csrf(request, "lab_detail.html")

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
    return render_with_csrf(request, "settings.html")

@app.get("/journey", response_class=HTMLResponse, tags=["Frontend"])
def journey_page(request: Request):
    return render_with_csrf(request, "journey.html")

@app.get("/defend/{project_id}", response_class=HTMLResponse, tags=["Frontend"])
def defend_project_page(request: Request, project_id: int):
    return render_with_csrf(request, "defend.html")

@app.get("/copilot", response_class=HTMLResponse, tags=["Frontend"])
def copilot_console_page(request: Request):
    return render_with_csrf(request, "copilot.html")

@app.get("/id", response_class=HTMLResponse, tags=["Frontend"])
def my_nexus_id_page(request: Request):
    return render_with_csrf(request, "nexus_id_private.html")

@app.get("/u/{public_slug}", response_class=HTMLResponse, tags=["Frontend"])
def public_profile_page(request: Request, public_slug: str):
    return render_with_csrf(request, "nexus_id_public.html", {"public_slug": public_slug})

@app.get("/u/{public_slug}/atlas", response_class=HTMLResponse, tags=["Frontend"])
def public_atlas_page(request: Request, public_slug: str):
    return render_with_csrf(request, "atlas_public.html", {"public_slug": public_slug})

@app.get("/sharing", response_class=HTMLResponse, tags=["Frontend"])
def sharing_center_page(request: Request):
    return render_with_csrf(request, "sharing.html")

@app.get("/mentor", response_class=HTMLResponse, tags=["Frontend"])
def mentor_dashboard_page(request: Request):
    return render_with_csrf(request, "mentor_dashboard.html")

@app.get("/educator", response_class=HTMLResponse, tags=["Frontend"])
def educator_observatory_page(request: Request):
    return render_with_csrf(request, "educator_observatory.html")

@app.get("/teams", response_class=HTMLResponse, tags=["Frontend"])
def teams_page(request: Request):
    return render_with_csrf(request, "teams.html")

@app.get("/review/{token}", response_class=HTMLResponse, tags=["Frontend"])
def project_review_page(request: Request, token: str):
    return render_with_csrf(request, "reviewer.html", {"token": token})




