# NEXUS - Phase 1 Foundation

NEXUS is an evidence-driven engineering intelligence platform designed for engineering students.

**Phase 1 Goal:** Establish the production-quality FastAPI and PostgreSQL foundation with secure authentication, session rotation, and a clean frontend shell.

## Architecture & Tech Stack
- **Backend Framework:** FastAPI
- **Database:** PostgreSQL via SQLAlchemy + psycopg v3
- **Migrations:** Alembic
- **Authentication:** Short-lived JWTs and hashed Refresh Tokens using HTTP-Only Secure Cookies.
- **Frontend:** Server-side rendered Jinja2 templates (HTML/CSS/Vanilla JS).

## Local Setup

### Option A: Docker PostgreSQL (Recommended)
1. Ensure Docker is installed and running.
2. Run `docker compose up -d` to spin up local `dev` and `test` PostgreSQL instances.
3. The default configuration in `.env.example` points to these instances.

### Option B: Existing PostgreSQL / Supabase
1. Create a `dev` database and a `test` database.
2. Copy `.env.example` to `.env` and update `DATABASE_URL` and `TEST_DATABASE_URL` accordingly.
**Never commit credentials to version control.**

## Running the Application

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Set up the environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to match your setup
   ```
3. Run Alembic migrations to create the schema:
   ```bash
   alembic upgrade head
   ```
4. Seed the initial Target Roles and Skills taxonomy (Idempotent):
   ```bash
   python -m app.db.seed
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Running Tests

Tests use an isolated test database (`TEST_DATABASE_URL`). Do NOT run tests against a production Supabase instance.
```bash
python -m pytest
```

## Security Features (Phase 1)
- **CSRF Protection:** Implemented via a combination of double-submit cookies/headers on all state-changing endpoints (POST/PUT/DELETE).
- **HTTP-Only Cookies:** Tokens are strictly transmitted via `HttpOnly`, `SameSite=Lax` cookies. Frontend JavaScript cannot access authentication tokens.
- **Refresh Token Rotation:** Every refresh action revokes the previous refresh session in the database and issues a new token pair.
- **Rate Limiting:** A lightweight in-memory rate limiter protects authentication endpoints from brute force.

## Scope Boundaries
**Phase 1 Scope:** Database foundation, secure authentication, API routers, frontend shell.
**Future Phases (Not yet implemented):** 
- Evidence Engine and skill-state calculations
- Gap Engine and Next Best Action Engine

## Phase 2: GitHub Evidence Collection

Phase 2 focuses on discovering and collecting evidence from a student's actual GitHub repositories.

### Features Included
* **GitHub Integration**: Links to public repositories associated with a user's GitHub username.
* **Manual Synchronization**: Analyzes the latest commit of the default branch on demand.
* **Repository Snapshots**: Permanent historical records of a repository's state at synchronization time.
* **Artifact Discovery**: Detects useful engineering files (e.g., Python, Docker, CI/CD, SQL). Excludes vendor/generated directories deterministically.
* **Raw Observations**: Generates objective technical facts (e.g., "FastAPI import detected", "Test file detected") using a deterministic rule engine based on file content.
* **Source-code Privacy**: Code is pulled temporarily in memory for analysis, but is **never** persisted to the database, logs, or snapshots.
* **Rate-limit Handling**: Graceful degradation and user-facing messages on GitHub API limit exhaustion.

### Limitations & Non-Goals
* **No AI evaluation** or complex parsing is performed. Observations are purely heuristic and text-based.
* **No background processing** or webhooks; synchronization is entirely manual and synchronous.
* **No private repositories** or GitHub OAuth are required (unless `GITHUB_TOKEN` is supplied for the backend).

## Phase 3: Evidence Engine

Phase 3 transforms raw observations into structured evidence and maps them to the skill taxonomy.

### Features Included
* **Deterministic Rule Engine**: Maps specific observation texts (e.g., "FastAPI import detected") to `EvidenceType` and baseline quality scores.
* **Skill Mapping**: Resolves evidence to existing `Skill` entities in the taxonomy. Unknown skills are strictly ignored.
* **Freshness Weighting**: Calculates a time-decay weight (1.0 to 0.1) based on the repository snapshot's capture date.
* **Rebuildable Engine**: Evidence can be deterministically deleted and regenerated from immutable `RawObservations` as rules evolve.
* **Strict Ownership Isolation**: Evidence API endpoints enforce that users can only view evidence for their own projects.

### Limitations & Non-Goals
* **Skill State, Gaps, and Next Best Actions are NOT implemented yet.** Evidence is collected and mapped, but aggregate proficiency scores are not calculated.
* **No automated taxonomy creation**. If a rule maps to a skill that doesn't exist in the database, it is ignored rather than created.
* **Zero LLMs used** for evidence generation. The engine relies purely on deterministic python-based dictionary lookups.
# NEXUS
