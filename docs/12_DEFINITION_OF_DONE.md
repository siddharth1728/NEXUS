# NEXUS: Definition of Done (DoD)

**Document Version:** 1.0.0  
**Status:** Canonical Source of Truth  

---

## 1. Definition of Done Checklist

A feature, module, or user story is **NOT** complete merely because code compiles and runs locally. Every deliverable in NEXUS must satisfy the following criteria:

### 1. Implementation & Code Quality
- [ ] Code is written in strict alignment with the domain architecture and active phase.
- [ ] Fully typed: zero implicit `any` in TypeScript, 100% type annotations in Python with `mypy`/`pyright` validation.
- [ ] Code passes all linter and formatting checks (`ruff check`, `ruff format`, `eslint`).
- [ ] Zero commented-out code, temporary debug logs, or hardcoded secrets/API keys.

### 2. Validation & Error Handling
- [ ] All inputs and external outputs are validated against Pydantic v2 schemas or Zod/TypeScript schemas.
- [ ] Boundary conditions, empty states, and malformed inputs are gracefully handled.
- [ ] AI extraction errors trigger the repair loop (max 2 retries) and degrade safely to `REQUIRES_REVIEW` or `UNKNOWN`.

### 3. Automated Testing
- [ ] Unit tests cover all core algorithms, state transitions, and edge cases.
- [ ] Integration tests cover API endpoints and database interactions.
- [ ] Mock LLM provider fixtures simulate edge cases, malformed outputs, and rate limits without external network calls.
- [ ] All existing and new tests pass with `pytest` and `playwright`.

### 4. Security & Access Control
- [ ] Authorization checks (RBAC/PBAC) are enforced in deterministic application code.
- [ ] All database queries enforce tenant and user isolation filters.
- [ ] LLM is not granted direct authorization decision power or untrusted execution access.

### 5. Observability & Telemetry
- [ ] AI pipeline stages emit structured traces and spans to Langfuse.
- [ ] Core business events emit OpenTelemetry metrics.
- [ ] Logs are structured (JSON format in production, clear contextual messages).

### 6. Documentation
- [ ] Public functions, classes, and REST endpoints are documented with clear docstrings.
- [ ] OpenAPI documentation is auto-generated and accurate.
- [ ] Any architectural modifications are recorded in a dedicated ADR.

### 7. Acceptance Criteria Verification
- [ ] The feature is verified against all explicit user acceptance criteria defined in the phase specification.
