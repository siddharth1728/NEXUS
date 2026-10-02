# NEXUS Backend Engine

> **Phase 01A** — Backend Engineering Foundation  
> FastAPI · Python 3.12 · SQLAlchemy 2.0 · Pydantic v2 · Async PostgreSQL

---

## Architecture

```
app/
├── __init__.py          # DISABLE_SQLALCHEMY_CEXT=1 for Application Control compat
├── core/
│   ├── config.py        # Pydantic Settings - typed, env-driven, cached singleton
│   ├── errors.py        # Domain exception hierarchy with HTTP status mapping
│   ├── logging.py       # Structured JSON/text logging + correlation ID + secret masking
│   └── middleware.py    # X-Request-ID injection + X-Process-Time-Ms tracking
├── db/
│   └── session.py       # AsyncEngine singleton, session factory, health probe
├── domain/
│   └── base.py          # DomainEntity (identity equality), ValueObject, DomainEvent
├── models/
│   └── base.py          # SQLAlchemy 2.0 Base + UUIDPrimaryKeyMixin + TimestampMixin
├── repositories/
│   └── base.py          # Generic async CRUD BaseRepository[T]
├── schemas/
│   ├── common.py        # APIResponse, ErrorEnvelope, PaginatedResponse envelopes
│   └── health.py        # HealthStatus (StrEnum), HealthResponse, ReadinessResponse
├── services/
│   └── base.py          # BaseService stub
├── api/
│   ├── deps.py          # FastAPI dependency injection (settings, db session)
│   └── v1/
│       ├── router.py
│       └── endpoints/
│           └── health.py    # GET /health (liveness), GET /ready (readiness)
└── main.py              # Application factory: create_app(), exception handlers, ASGI app
```

### Documentation
- [Phase 01D - AI Provider Gateway](../docs/13_AI_PROVIDER_GATEWAY.md): Overview of AI Gateway, Provider configuration, Mocking, and adding new Providers.

---

## Quick Start

### 1. Prerequisites

- Python 3.12+ (**managed by `uv`**)
- Docker Desktop (for local PostgreSQL + Redis)

### 2. Set up virtual environment

```powershell
# From the NEXUS root directory:
python -m uv venv backend/.venv --python 3.12
python -m uv pip install --python backend/.venv -e ".[dev]"
```

### 3. Configure environment

```powershell
Copy-Item .env.example .env
# Edit .env and fill in DATABASE_URL, REDIS_URL, GEMINI_API_KEY, etc.
```

### 4. Start infrastructure (PostgreSQL + Redis)

```powershell
# From NEXUS root:
docker compose up -d
```

### 5. Run the API

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

---

## Running Tests

```powershell
# Full suite with coverage
backend\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing

# Unit tests only
backend\.venv\Scripts\python.exe -m pytest tests/unit/ -v

# Integration tests only
backend\.venv\Scripts\python.exe -m pytest tests/integration/ -v
```

---

## Quality Gates

```powershell
# Linting (must be clean before any merge)
backend\.venv\Scripts\python.exe -m ruff check .

# Formatting check
backend\.venv\Scripts\python.exe -m ruff format --check .

# Type check (app/ only, strict)
backend\.venv\Scripts\python.exe -m mypy app
```

---

## Running Alembic Migrations

```powershell
cd backend

# Generate a new migration (after defining models in Phase 01B)
backend\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "initial_schema"

# Apply migrations
backend\.venv\Scripts\python.exe -m alembic upgrade head
```

---

## Environment Variables

See [`../.env.example`](../.env.example) for the full contract. Key variables:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection URI | `postgresql+asyncpg://nexus:nexus_password@localhost:5432/nexus_db` |
| `APP_ENV` | `development`, `staging`, `production`, `testing` | `development` |
| `DEFAULT_LLM_PROVIDER` | `gemini`, `ollama`, `huggingface`, `mock` | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key (required for live AI calls) | — |
| `DISABLE_SQLALCHEMY_CEXT` | Set to `1` if Application Control blocks C extensions | `1` |

---

## Known Environment Notes

- **Windows Application Control Policy:** The `SQLAlchemy` C-extension DLL (`_immutabledict_cy`) is blocked by Windows Application Control on some managed machines. `DISABLE_SQLALCHEMY_CEXT=1` is set in `app/__init__.py` as a pure-Python fallback. This does **not** affect correctness or production Docker deployments.
- **uv not on PATH:** `uv` is installed as a Python package (`pip install uv`) and must be invoked via `python -m uv`. Run `python -m uv python update-shell` to add `~/.local/bin` to your PATH permanently.
