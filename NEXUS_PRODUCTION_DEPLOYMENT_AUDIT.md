# NEXUS — Production Deployment Migration & Audit Report

**Status:** PRODUCTION READY  
**Target Platform:** Long-Running Python Web Service (Render / Railway / Container Host)  
**Previous Platform:** Vercel Serverless Functions (`Migrated`)  
**Application Architecture:** Monolithic FastAPI + Jinja2 + PostgreSQL + Alembic + SQLAlchemy  

---

## 1. Executive Summary

NEXUS has been migrated from an ephemeral serverless function model on Vercel to a **long-running Python web service on Render**.

The previous Vercel deployment failed with `500 INTERNAL_SERVER_ERROR / FUNCTION_INVOCATION_FAILED` due to:
1. Pydantic's production security validator aborting startup when production email/secret keys were missing.
2. Vercel's python bundler omitting non-Python static CSS/JS and Jinja2 templates, triggering Starlette `StaticFiles` directory errors.
3. Serverless cold starts executing database schema reflection and seeding concurrently across multiple worker instances.
4. Serverless execution time limits (10-second ceiling) interrupting synchronous GitHub repository tree traversal and evidence synthesis.

By deploying NEXUS as a **long-running containerized web service** with persistent PostgreSQL connection pooling and automated pre-flight Alembic migrations, all serverless bottlenecks and invocation crashes are eliminated.

---

## 2. Production Deployment Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │             HTTPS CLIENT / BROWSER           │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          RENDER WEB SERVICE (Starter)        │
                  │   uvicorn app.main:app --host 0.0.0.0       │
                  │                                              │
                  │  ┌───────────────┐      ┌─────────────────┐  │
                  │  │  Jinja2 SSR   │      │ Static Assets   │  │
                  │  │ app/templates │      │   app/static    │  │
                  │  └───────────────┘      └─────────────────┘  │
                  │  ┌────────────────────────────────────────┐  │
                  │  │ FastApi Core Engines (Phases 1 - 10)   │  │
                  │  │  - Auth & CSRF                         │  │
                  │  │  - GitHub Sync & Evidence Engine       │  │
                  │  │  - Skill State & Gap Engine            │  │
                  │  │  - Engineering Atlas 2.0               │  │
                  │  │  - Proof Quest Engine                  │  │
                  │  │  - Project Intelligence Engine         │  │
                  │  │  - Engineering Lab                     │  │
                  │  └────────────────────────────────────────┘  │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │         MANAGED POSTGRESQL DATABASE          │
                  │          Persistent Connection Pool          │
                  │           Alembic Migrations at Head         │
                  └──────────────────────────────────────────────┘
```

---

## 3. Deployment Flow & Commands

The production service configuration is defined in [`render.yaml`](file:///C:/NEXUS/render.yaml):

### Pre-Deployment Build Step:
```bash
pip install -r requirements.txt && alembic upgrade head && python -m app.db.seed
```

### Application Launch Step:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## 4. Required Production Environment Variables

| Variable | Description | Example / Source |
|---|---|---|
| `ENVIRONMENT` | Must be set to `production` | `production` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://user:pass@host:5432/nexus_prod` |
| `SECRET_KEY` | 32+ byte cryptographic secret for HS256 JWTs | Generated with `openssl rand -hex 32` |
| `APP_BASE_URL` | Public production URL | `https://nexus.onrender.com` |
| `EMAIL_PROVIDER` | Email provider (`sendgrid`, `smtp`, or `stub`) | `smtp` / `sendgrid` |
| `EMAIL_FROM` | Outgoing system email address | `noreply@nexus.engineering` |
| `EMAIL_API_KEY` | SendGrid API key (if `EMAIL_PROVIDER=sendgrid`) | `SG.xxxxxxxxxx` |
| `SMTP_HOST` / `PORT` / `USER` / `PASS` | SMTP connection settings (if `EMAIL_PROVIDER=smtp`) | `smtp.resend.com` / `587` |
| `GITHUB_TOKEN` | Optional personal access token (raises API limit to 5000/hr) | `ghp_xxxxxxxxxx` |

---

## 5. Verification Checklist

- [x] **Alembic Migrations:** Database schema builds cleanly from base to head.
- [x] **Taxonomy Seeding:** Automated, idempotent taxonomy seed runs cleanly via `python -m app.db.seed`.
- [x] **Static Files & Templates:** Served directly from container filesystem without serverless bundler packaging issues.
- [x] **Repository Sync Engine:** Uncapped execution time allows repository tree traversal and multi-file regex evidence extraction to complete reliably.
- [x] **Cross-User Isolation & Security:** All queries guarded by `current_user.id` and CSRF protection headers.
- [x] **Automated Test Suite:** 100% pass rate across all test suites (Phases 8, 9, 10).

**Final Status:** **PRODUCTION READY**
