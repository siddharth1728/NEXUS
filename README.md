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

## Production Deployment

### Architecture
NEXUS runs on a FastAPI application backend, backed by PostgreSQL, with schema migrations managed by Alembic. Production environments also require an external email provider for authentication flows.

### Environment Variables
The following environment variables are **required** for production:
- `SECRET_KEY` (must be a secure 32+ character string)
- `DATABASE_URL`
- `APP_BASE_URL`
- `ENVIRONMENT` (must be set to `production`)
- `EMAIL_PROVIDER` (must be `sendgrid` or `smtp` in production)
- `EMAIL_FROM`
- `EMAIL_API_KEY` (or equivalent SMTP credentials)

**Security Warning:** Never commit your `.env` file to version control. Production secrets must be injected securely via your deployment platform's environment variable manager.

### Password Reset Flow
In production, the password reset flow requires a fully configured email provider. The development `stub` provider is strictly rejected in production.

### Detailed Readiness Checklist
For a comprehensive breakdown of the production security boundaries and configuration options, please refer to the [NEXUS Production Readiness Report](C:/Users/siddu/.gemini/antigravity-ide/brain/3834f55a-417d-4535-a8a5-ff611fed72c5/NEXUS_PRODUCTION_READINESS.md).

### Deployment Steps
1. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
2. Start the production server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
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

## Phase 4: Skill State Engine

Phase 4 introduces a deterministic engine that maps raw engineering evidence to four explicit states: MISSING, WEAK, DEVELOPING, and STRONG.

### Algorithm and Anti-Inflation
The engine uses strict algorithmic aggregation to prevent inflation:
* **Base Contribution**: `quality_score * freshness_weight`. Older evidence contributes less.
* **EvidenceType Diversity Cap**: Total contribution from any single evidence type (e.g., API, TESTING) is capped at `1.5`.
* **Artifact Diversity Cap**: Total contribution from any single artifact (e.g., `app.py`) is capped at `2.0`.

### State Thresholds
* **MISSING**: Contribution < 0.5 or no meaningful evidence.
* **WEAK**: Contribution >= 0.5, 1+ meaningful evidence, 1+ unique EvidenceType, 1+ unique Artifact.
* **DEVELOPING**: Contribution >= 1.5, 2+ meaningful evidence, 1+ unique EvidenceType, 2+ unique Artifacts.
* **STRONG**: Contribution >= 3.0, 4+ meaningful evidence, 2+ unique EvidenceTypes, 3+ unique Artifacts.

### Evidence Explorer & Privacy
The API and UI provide an Evidence Explorer that answers "Why this state?" by displaying the metadata (type, quality, freshness, safe source reference) used in the classification. 
* **Privacy Boundary**: It strictly enforces privacy by never exposing actual source code snippets, GitHub tokens, or credentials. Raw observation text is kept as strictly factual metadata.

> **Note**: Skill State is an evidence-derived classification and is not a measurement of a student's absolute engineering ability.

## Phase 5: Gap Engine

Phase 5 introduces a deterministic engine to identify skill deficiencies by comparing a student's actual `UserSkill` states against the required skills of their chosen `TargetRole` (via `TargetRoleSkill`).

### Features Included
* **Ordinal State Comparison**: States are mapped to strict ordinal values (`MISSING = 0`, `WEAK = 1`, `DEVELOPING = 2`, `STRONG = 3`). Missing UserSkills are implicitly treated as `MISSING`.
* **State Distance**: The engine calculates the gap by subtracting the actual state from the required state. If actual >= required, there is no gap.
* **Deterministic Severity**: The raw distance is multiplied by the `TargetRoleSkill.importance_weight` to calculate a prioritization `severity`.
* **Deterministic Sorting**: Gaps are strictly sorted by severity DESC, importance_weight DESC, required state DESC, and skill ID ASC.
* **Derived and Rebuildable**: Gaps are completely derived data. Obsolete gaps automatically disappear as evidence improves a student's Skill State.

### Limitations & Non-Goals
* **No Next Best Actions**: The Gap Engine strictly identifies "What is missing?". It does NOT fabricate recommendations, learning resources, or say "Build X". That is strictly reserved for Phase 6.
* **No AI/LLMs**: Everything is deterministic math.
* **No Readiness Percentages**: The severity score is a sorting priority, NOT a completion percentage or readiness score.
* **No Vanity Metrics**: GitHub stars, forks, or raw commit counts are entirely excluded from gap analysis.

> **Note**: The Gap Engine identifies evidence-derived skill deficiencies. It does not determine absolute engineering ability and does not generate recommendations.
# NEXUS
