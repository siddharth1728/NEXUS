# NEXUS: Engineering Constitution

**Document Version:** 1.0.0  
**Status:** Canonical & Non-Negotiable  
**Applies To:** All Engineers, Contributors, and Autonomous Coding Agents  

---

## 1. Fundamental Tenets

Every architectural and implementation decision within the NEXUS repository must rigorously adhere to the ten core engineering principles outlined in this Constitution.

---

### Principle A — Build in Explicit Phases
- Implementation must progress through defined, bounded phases.
- No developer or AI agent is permitted to write forward-phase infrastructure or stub code until the current phase's acceptance criteria are 100% met.
- Scope creep is treated as an architectural defect.

### Principle B — Small, Bounded Changes
- Every PR or agent edit must be small, coherent, and isolated.
- Unrelated refactoring, dependency churn, and drive-by changes to stable files are strictly forbidden.
- Clean git history with atomic, informative commits is required.

### Principle C — Contract-First Engineering
- Data schemas (Pydantic v2), database models (SQLAlchemy), and API specifications (OpenAPI) must be designed and reviewed before writing business logic.
- AI pipelines must operate strictly against validated JSON Schemas.

### Principle D — Comprehensive Testing
- Testing is not an afterthought; it is written alongside implementation.
- Every domain service must have unit test coverage.
- Every API endpoint must have automated integration tests.
- Every critical user flow must have automated E2E tests (Playwright).

### Principle E — Structured & Validated AI Output
- The application must never parse raw, free-form LLM string outputs when structured data is required.
- All AI transformations must use Pydantic models with strict validation, automatic retries on validation errors, and deterministic schema enforcement.

### Principle F — Never Invent Facts (Zero Hallucination Rule)
- When source evidence is missing: assign status `UNKNOWN`.
- When source documents conflict: assign status `CONFLICT`.
- When AI extraction confidence is low: assign status `REQUIRES_REVIEW`.
- The system must never guess a deadline, an assignee, or a policy rule.

### Principle G — Strict Source Grounding & Attribution
- Every extracted Fact, Task, Constraint, and Deadline must preserve its provenance:
  - Document ID
  - Page number or timestamp
  - Exact verbatim text snippet / citation
  - Bounding box coordinates (where multimodal/OCR data is available)

### Principle H — Human Control & Authorization
- NEXUS adheres to the "AI Recommends, Human Decides" paradigm for consequential actions.
- External side-effects (sending emails, modifying Jira, executing code, signing off compliance) require explicit human approval gates unless a policy explicitly delegates autonomy.

### Principle I — Security by Design
- LLMs are considered untrusted processing units.
- An LLM must NEVER evaluate user permissions, roles, or authorization policies.
- Authorization (RBAC / PBAC) is strictly enforced in deterministic application code before data reaches the model and after data is returned.

### Principle J — Total Measurability
- If a subsystem's accuracy or quality cannot be measured, it cannot be claimed as production-ready.
- The platform must measure and report:
  - Extraction precision & recall
  - Deadline parsing accuracy
  - Dependency graph correctness
  - Attribution grounding fidelity
  - End-to-end processing latency & model cost

---

## 2. Code Quality & Standards

1. **Python Backend:**
   - Python 3.12+ (compatible with 3.14+)
   - Static type checking with `mypy` or `pyright` (strict mode enabled for domain modules)
   - Formatting and linting with `ruff`
   - Fully async I/O (`asyncio`, `asyncpg`, `httpx`) for all I/O-bound operations
2. **Frontend:**
   - TypeScript strict mode
   - Next.js App Router with Server Components where appropriate
   - Tailwind CSS for design system tokens and styling
   - Zero console errors, zero implicit `any`
3. **Documentation Integrity:**
   - All public APIs, domain models, and service methods must include docstrings explaining intent, arguments, exceptions, and return types.
