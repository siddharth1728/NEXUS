from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

@dataclass
class ChallengeOption:
    text: str
    is_correct: bool
    explanation: str

@dataclass
class TryItChallenge:
    prompt: str
    options: List[ChallengeOption]
    engineering_principle: str

@dataclass
class DiagramStep:
    step_number: int
    label: str
    technical_detail: str
    layer: str  # CLIENT, ROUTER, LOGIC, PERSISTENCE, INFRA

@dataclass
class ConceptDefinition:
    concept_key: str
    title: str
    short_description: str
    domain: str  # "API & Routing", "Security & Auth", "Data & Persistence", "Quality & Testing", "Infrastructure & DevOps"
    difficulty: str  # "FOUNDATION", "INTERMEDIATE", "ADVANCED"
    related_skill_names: List[str]
    related_evidence_types: List[str]
    prerequisites: List[str]
    learning_objectives: List[str]
    why_it_matters: str
    how_it_appears_in_projects: str
    diagram_steps: List[DiagramStep]
    try_it_challenge: TryItChallenge
    explain_it_prompt: str
    related_action_key: Optional[str] = None

CONCEPT_CATALOG: Dict[str, ConceptDefinition] = {
    "HTTP_REQUEST_LIFECYCLE": ConceptDefinition(
        concept_key="HTTP_REQUEST_LIFECYCLE",
        title="HTTP Request & Routing Lifecycle",
        short_description="How requests travel from client sockets through middleware, routers, and handlers back to formatted responses.",
        domain="API & Routing",
        difficulty="FOUNDATION",
        related_skill_names=["REST APIs", "Python"],
        related_evidence_types=["API", "IMPLEMENTATION"],
        prerequisites=[],
        learning_objectives=[
            "Understand how ASGI/WSGI servers parse HTTP methods, paths, headers, and payloads.",
            "Trace request lifecycle through route matching, parameter dependency injection, and error handlers.",
            "Design idempotent and predictable REST endpoint contracts."
        ],
        why_it_matters="Every web service begins with HTTP. Knowing where the boundary between transport (HTTP headers/status) and business logic lies prevents routing bugs, leaked exceptions, and inconsistent client contracts.",
        how_it_appears_in_projects="NEXUS identifies routing decorators (@app.get, @router.post), Pydantic schemas, query parameters, and status code specifications across your route files.",
        diagram_steps=[
            DiagramStep(1, "Client Request", "Browser or API client initiates TCP/TLS handshake and transmits HTTP verb + path + headers.", "CLIENT"),
            DiagramStep(2, "ASGI / WSGI Server", "Server worker (e.g. Uvicorn) receives raw bytes, parses HTTP envelope, and invokes the framework application.", "ROUTER"),
            DiagramStep(3, "Route Dispatcher", "Router matches URL path and method regex against registered route handlers.", "ROUTER"),
            DiagramStep(4, "Dependency Injection", "Framework resolves parameters, validates JSON request body against schema, and checks auth headers.", "LOGIC"),
            DiagramStep(5, "Controller / Business Logic", "Endpoint function executes service logic, queries databases, and formats return payload.", "LOGIC"),
            DiagramStep(6, "Response Serialization", "Framework serializes Python model to JSON bytes, attaches HTTP 200/201 status and Content-Type header.", "CLIENT")
        ],
        try_it_challenge=TryItChallenge(
            prompt="A client sends a POST request with an invalid JSON body. Which layer in a modern web framework (like FastAPI) should intercept and reject this request?",
            options=[
                ChallengeOption("The database engine during SQL insert execution.", False, "The database is too deep in the stack. Validating input before touching the DB prevents SQL injection and unnecessary database connections."),
                ChallengeOption("The schema validation layer during parameter dependency injection before handler execution.", True, "Modern frameworks reject invalid payloads at the boundary with HTTP 422 Unprocessable Entity before any controller or DB logic runs."),
                ChallengeOption("The background task worker queue.", False, "Background workers handle asynchronous tasks, not synchronous HTTP envelope validation."),
                ChallengeOption("The client DNS resolver.", False, "DNS only translates domain names to IP addresses.")
            ],
            engineering_principle="Fail Fast at the Boundary: Schema validation at the routing perimeter protects downstream database and business layers from corrupted state."
        ),
        explain_it_prompt="Explain why returning explicit HTTP status codes (e.g. 201 Created vs 200 OK, 404 Not Found vs 400 Bad Request) is critical for client applications.",
        related_action_key="BUILD_REST_API"
    ),

    "AUTHENTICATION_FLOWS": ConceptDefinition(
        concept_key="AUTHENTICATION_FLOWS",
        title="Stateless Token Authentication & JWT Lifecycle",
        short_description="Verifying identity across distributed web boundaries using cryptographic signatures and token lifespans.",
        domain="Security & Auth",
        difficulty="INTERMEDIATE",
        related_skill_names=["Authentication", "Python"],
        related_evidence_types=["AUTHENTICATION", "API"],
        prerequisites=["HTTP_REQUEST_LIFECYCLE"],
        learning_objectives=[
            "Distinguish between identity verification (Authentication) and permissions (Authorization).",
            "Understand symmetric vs asymmetric signing algorithms (HS256 vs RS256).",
            "Implement secure token expiration, refresh rotation, and password hashing with salt."
        ],
        why_it_matters="Passwords must never be stored in plain text. Stateless tokens allow APIs to scale across multiple servers without centralized session storage, provided signature secrets and token expiration are rigorously enforced.",
        how_it_appears_in_projects="NEXUS detects password hashing utilities (bcrypt, argon2), JWT encoding/decoding routines, and Bearer token / OAuth2 dependencies guarding route functions.",
        diagram_steps=[
            DiagramStep(1, "Credentials Handshake", "Client transmits email + password over HTTPS to /api/auth/login.", "CLIENT"),
            DiagramStep(2, "Password Verification", "Auth service fetches hashed password from database and runs constant-time cryptographic compare.", "LOGIC"),
            DiagramStep(3, "Token Minting", "Auth service signs JWT payload (user_id, exp, scopes) with HMAC secret key.", "LOGIC"),
            DiagramStep(4, "Token Dispatch", "Server responds with access token (and/or httpOnly secure refresh cookie).", "CLIENT"),
            DiagramStep(5, "Subsequent Request", "Client attaches Authorization: Bearer <token> to protected endpoint requests.", "CLIENT"),
            DiagramStep(6, "Signature Verification", "Middleware verifies cryptographic signature and expiration timestamp without querying the DB.", "ROUTER")
        ],
        try_it_challenge=TryItChallenge(
            prompt="Why should access tokens have a short lifespan (e.g. 15-60 minutes) instead of lasting indefinitely?",
            options=[
                ChallengeOption("To make tokens take up less storage on the user's hard drive.", False, "Token size is determined by payload claims, not expiration timestamp length."),
                ChallengeOption("Because tokens cannot be easily revoked in a pure stateless architecture without a blocklist, limiting the blast radius of a stolen token.", True, "Since stateless servers verify tokens via signature math without DB lookups, short lifespans ensure a leaked token expires quickly."),
                ChallengeOption("To force the database to re-index all user passwords every 15 minutes.", False, "Access token validation does not touch database password tables."),
                ChallengeOption("HTTP headers do not support numbers greater than 60.", False, "HTTP headers support arbitrary ASCII text.")
            ],
            engineering_principle="Least Privilege & Blast Radius Containment: Stateless credentials must expire rapidly to minimize the exposure window if compromised."
        ),
        explain_it_prompt="In your own words, what is the difference between a password hash and an encrypted password?",
        related_action_key="ADD_JWT_AUTHENTICATION"
    ),

    "DATABASE_PERSISTENCE": ConceptDefinition(
        concept_key="DATABASE_PERSISTENCE",
        title="Relational Modeling & Query Execution",
        short_description="Structuring data integrity with primary keys, foreign constraints, relational normalization, and transactions.",
        domain="Data & Persistence",
        difficulty="FOUNDATION",
        related_skill_names=["PostgreSQL", "SQL", "Database Design"],
        related_evidence_types=["DATABASE"],
        prerequisites=[],
        learning_objectives=[
            "Design normalized relational schemas with clear referential integrity constraints.",
            "Understand ACID guarantees (Atomicity, Consistency, Isolation, Durability) in transactions.",
            "Prevent N+1 query bottlenecks using joined queries and proper ORM eager loading."
        ],
        why_it_matters="Application code is transient; database state is permanent. Relational databases enforce invariants and prevent orphaned or conflicting business records.",
        how_it_appears_in_projects="NEXUS detects database engine configurations (PostgreSQL connection strings), ORM declarative base models, ForeignKey constraints, and Session management.",
        diagram_steps=[
            DiagramStep(1, "ORM Entity Mapping", "Declarative Python classes define table columns, types, and relational foreign keys.", "LOGIC"),
            DiagramStep(2, "Connection Pool", "Application checks out an active database socket connection from the thread pool.", "LOGIC"),
            DiagramStep(3, "Transaction Begin", "Database begins transaction block (BEGIN) enforcing isolation levels.", "PERSISTENCE"),
            DiagramStep(4, "SQL Execution", "Engine parses SQL statement, optimizes query plan, and executes index lookups.", "PERSISTENCE"),
            DiagramStep(5, "Transaction Commit", "All mutations are written to WAL (Write-Ahead Log) and flushed to disk on COMMIT.", "PERSISTENCE"),
            DiagramStep(6, "Connection Release", "Socket connection is returned to the pool for reuse by subsequent requests.", "LOGIC")
        ],
        try_it_challenge=TryItChallenge(
            prompt="What is the primary danger of the 'N+1 query problem' in backend services?",
            options=[
                ChallengeOption("It causes the database to permanently delete table primary keys.", False, "N+1 affects performance, not schema definitions."),
                ChallengeOption("Querying child relationships inside a loop makes N individual database round-trips instead of 1 batched query, causing massive latency.", True, "Each network hop to the database adds latency. Fetching 100 items with N+1 results in 101 round-trips instead of a single JOIN."),
                ChallengeOption("It overflows the CPU register on the client browser.", False, "N+1 is a server/database round-trip bottleneck."),
                ChallengeOption("It converts relational tables into NoSQL documents.", False, "Query patterns do not change database storage paradigms.")
            ],
            engineering_principle="Batch and Join at the Database Layer: Always leverage database relational operators to fetch related data in single round-trips."
        ),
        explain_it_prompt="Why is wrapping multiple related database operations in a single Transaction (commit/rollback) critical for data integrity?",
        related_action_key="SETUP_POSTGRES_DB"
    ),

    "DATABASE_MIGRATIONS": ConceptDefinition(
        concept_key="DATABASE_MIGRATIONS",
        title="Schema Evolution & Database Migrations",
        short_description="Version-controlling database schema modifications reproducibly across development, staging, and production.",
        domain="Data & Persistence",
        difficulty="INTERMEDIATE",
        related_skill_names=["Database Design", "SQL"],
        related_evidence_types=["DATABASE", "CONFIGURATION"],
        prerequisites=["DATABASE_PERSISTENCE"],
        learning_objectives=[
            "Track relational schema evolution in Git alongside application source code.",
            "Write reversible upgrade() and downgrade() migration steps.",
            "Safely alter existing tables in production without locking or data loss."
        ],
        why_it_matters="Manual database edits cause environment drift where staging and production schemas diverge. Automated migrations ensure deterministic deployments and repeatable rollbacks.",
        how_it_appears_in_projects="NEXUS detects Alembic migration repositories, alembic.ini configuration, revision scripts in versions/, and migration execution commands.",
        diagram_steps=[
            DiagramStep(1, "Model Change", "Engineer modifies an ORM model (adds column, modifies constraint) in application code.", "LOGIC"),
            DiagramStep(2, "Revision Generation", "Migration tool inspects model diff and writes versioned migration script with upgrade/downgrade.", "LOGIC"),
            DiagramStep(3, "Migration Review", "Engineer reviews generated SQL statements for lock safety and default values.", "LOGIC"),
            DiagramStep(4, "Version Table Check", "Migration tool checks alembic_version table in target DB to determine current revision.", "PERSISTENCE"),
            DiagramStep(5, "DDL Execution", "Tool executes incremental ALTER TABLE / CREATE TABLE DDL statements in a transaction.", "PERSISTENCE"),
            DiagramStep(6, "Version Stamp", "Database version table is updated to the new revision hash upon successful DDL execution.", "PERSISTENCE")
        ],
        try_it_challenge=TryItChallenge(
            prompt="Why should database migration files be committed to version control (Git) alongside application code?",
            options=[
                ChallengeOption("To make database backups unnecessary.", False, "Migrations define schema changes, not stored user data backups."),
                ChallengeOption("To ensure every environment (CI, staging, prod) can deterministically replay schema changes in exact order.", True, "Version-controlled migrations allow automated deployment pipelines to bring any database instance to the exact schema required by the code."),
                ChallengeOption("To compress table data into binary files.", False, "Migrations contain DDL instructions, not table compression algorithms."),
                ChallengeOption("Because SQL databases refuse to run without a Git repository connected.", False, "Databases run standalone; migrations are an engineering discipline.")
            ],
            engineering_principle="Infrastructure as Code: Database schemas must evolve through versioned, reviewable, and automated migration scripts."
        ),
        explain_it_prompt="What happens if a developer alters a production database manually via GUI instead of using a migration script?",
        related_action_key="ADD_DATABASE_MIGRATIONS"
    ),

    "AUTOMATED_TESTING": ConceptDefinition(
        concept_key="AUTOMATED_TESTING",
        title="Test Automation & Regression Prevention",
        short_description="Verifying expected invariants and edge cases programmatically to ensure code correctness over time.",
        domain="Quality & Testing",
        difficulty="INTERMEDIATE",
        related_skill_names=["Testing", "Python"],
        related_evidence_types=["TESTING"],
        prerequisites=["HTTP_REQUEST_LIFECYCLE"],
        learning_objectives=[
            "Distinguish between Unit Tests (isolated logic) and Integration Tests (API + DB).",
            "Use test fixtures and mocks to isolate side effects without polluting production databases.",
            "Assert positive, negative, and edge-case execution branches."
        ],
        why_it_matters="Manual testing does not scale. Automated test suites execute in seconds, proving that recent code modifications did not silently break existing functionality.",
        how_it_appears_in_projects="NEXUS detects test directories (tests/), pytest configuration (pytest.ini, conftest.py), test function definitions (def test_*), and assertion statements.",
        diagram_steps=[
            DiagramStep(1, "Test Runner Trigger", "Pytest discovers test files matching test_*.py across the repository.", "LOGIC"),
            DiagramStep(2, "Fixture Setup", "Conftest initializes clean isolated test database and HTTP TestClient fixture.", "PERSISTENCE"),
            DiagramStep(3, "Arrange State", "Test seeds required test records or mock states.", "LOGIC"),
            DiagramStep(4, "Act / Execute", "Test client invokes target endpoint with specified parameters or payload.", "ROUTER"),
            DiagramStep(5, "Assert Invariants", "Assertions verify HTTP status code, returned response JSON structure, and database side effects.", "LOGIC"),
            DiagramStep(6, "Fixture Teardown", "Test framework rolls back transaction or drops temporary test fixtures cleanly.", "PERSISTENCE")
        ],
        try_it_challenge=TryItChallenge(
            prompt="What is the key advantage of testing error cases (e.g. invalid input, 404s, unauthorized access) in addition to 'happy path' cases?",
            options=[
                ChallengeOption("Error tests speed up the CPU clock rate.", False, "Tests verify logic correctness, not hardware clock speed."),
                ChallengeOption("They guarantee the service fails gracefully with clean HTTP error envelopes rather than crashing or leaking stack traces.", True, "Testing negative branches ensures unauthorized users are blocked and invalid requests receive safe, informative error messages."),
                ChallengeOption("They automatically eliminate the need for authentication.", False, "Testing verifies authentication works; it does not replace it."),
                ChallengeOption("They decrease the size of the repository on disk.", False, "Test code adds lines of code, but delivers immense reliability.")
            ],
            engineering_principle="Verify Negative Boundaries: A production service is defined as much by how it handles bad input as by how it handles good input."
        ),
        explain_it_prompt="Explain why integration tests using an ephemeral test database provide higher confidence than purely mocking every database call.",
        related_action_key="ADD_API_TESTS"
    ),

    "CONTAINERIZATION_DOCKER": ConceptDefinition(
        concept_key="CONTAINERIZATION_DOCKER",
        title="Containerization & Reproducible Environments",
        short_description="Packaging application runtime, OS dependencies, and code into deterministic container images.",
        domain="Infrastructure & DevOps",
        difficulty="INTERMEDIATE",
        related_skill_names=["Docker"],
        related_evidence_types=["CONTAINERIZATION", "CONFIGURATION"],
        prerequisites=[],
        learning_objectives=[
            "Understand container isolation vs traditional virtual machine overhead.",
            "Write multi-stage Dockerfiles optimizing image size and build caching.",
            "Configure environment variables and non-root execution users for container security."
        ],
        why_it_matters="Eliminates the 'it works on my machine' paradox. Containers guarantee that the exact same binary environment runs on development laptops, CI servers, and cloud clusters.",
        how_it_appears_in_projects="NEXUS detects Dockerfile, .dockerignore, docker-compose.yml, base image declarations (FROM python:3.11-slim), and ENTRYPOINT configurations.",
        diagram_steps=[
            DiagramStep(1, "Dockerfile Definition", "Declarative manifest specifies base OS image, dependencies, and startup command.", "INFRA"),
            DiagramStep(2, "Docker Build & Cache", "Engine builds layered image, reusing unchanged dependency layers to speed up builds.", "INFRA"),
            DiagramStep(3, "Image Artifact", "Self-contained immutable container image is tagged with version or commit SHA.", "INFRA"),
            DiagramStep(4, "Container Instantiation", "Docker daemon launches container instance with isolated filesystem, network, and process space.", "INFRA"),
            DiagramStep(5, "Port Forwarding", "Host forwards incoming traffic (e.g. host:8000 -> container:8000) to application process.", "INFRA"),
            DiagramStep(6, "Health Check", "Container runtime monitors process health and restarts unhealthy containers automatically.", "INFRA")
        ],
        try_it_challenge=TryItChallenge(
            prompt="Why should production Dockerfiles leverage a .dockerignore file to exclude local .venv/ and .git/ directories?",
            options=[
                ChallengeOption("To prevent Docker from converting Python into JavaScript.", False, "Docker does not transpile languages."),
                ChallengeOption("To reduce build context transfer time, prevent cache invalidation, and avoid baking local OS binaries into Linux containers.", True, "Excluding local virtualenvs ensures dependencies are freshly compiled for the target Linux architecture inside the container."),
                ChallengeOption("Because Docker refuses to build images that contain the letter 'v'.", False, "Fictitious rule."),
                ChallengeOption("To automatically deploy the image to Kubernetes.", False, ".dockerignore controls build context, not cluster deployment.")
            ],
            engineering_principle="Immutable Artifacts: Containers must build deterministically from source without inheriting dirty local host artifacts."
        ),
        explain_it_prompt="In your own words, what is the difference between a Docker Image and a Docker Container?",
        related_action_key="DOCKERIZE_SERVICE"
    ),

    "CI_CD_AUTOMATION": ConceptDefinition(
        concept_key="CI_CD_AUTOMATION",
        title="Continuous Integration & Automated Pipelines",
        short_description="Automating linting, test suites, and security scans on every Git push to maintain repository health.",
        domain="Infrastructure & DevOps",
        difficulty="INTERMEDIATE",
        related_skill_names=["Git"],
        related_evidence_types=["CI_CD", "CONFIGURATION"],
        prerequisites=["AUTOMATED_TESTING"],
        learning_objectives=[
            "Configure automated workflow triggers on pull requests and branch merges.",
            "Parallelize testing matrix across multiple runtime versions.",
            "Block broken code from merging into mainline production branches."
        ],
        why_it_matters="Manual verification is prone to human oversight. CI pipelines act as automated quality gates, ensuring every committed branch passes formatting, typing, and unit tests.",
        how_it_appears_in_projects="NEXUS detects GitHub Actions workflow files (.github/workflows/*.yml), step commands (pytest, flake8, ruff), and automated trigger events.",
        diagram_steps=[
            DiagramStep(1, "Git Push / Pull Request", "Developer pushes feature branch to GitHub.", "CLIENT"),
            DiagramStep(2, "Webhook Trigger", "GitHub detects push event and schedules workflow runners matching repository rules.", "ROUTER"),
            DiagramStep(3, "Clean Environment Setup", "Ephemeral runner boots clean Linux container and checks out branch source code.", "INFRA"),
            DiagramStep(4, "Dependency Installation", "Runner installs project packages using pinned lockfile (pip, poetry, npm).", "LOGIC"),
            DiagramStep(5, "Test Execution", "Runner executes test suite and static analysis tools, capturing exit codes.", "LOGIC"),
            DiagramStep(6, "Status Check Stamp", "CI service reports PASS/FAIL status check, enabling or blocking branch merge.", "ROUTER")
        ],
        try_it_challenge=TryItChallenge(
            prompt="What is the primary objective of running tests in a clean CI runner rather than only on the developer's laptop?",
            options=[
                ChallengeOption("To make GitHub repositories appear higher in Google search results.", False, "CI status does not affect web search engine ranking."),
                ChallengeOption("To verify code works in an unpolluted environment without uncommitted local files or machine-specific environment variables.", True, "Developers often have local files or uncommitted packages that mask bugs. CI proves the repository is truly self-contained."),
                ChallengeOption("To automatically write documentation for the code.", False, "CI executes configured jobs; it does not automatically author documentation."),
                ChallengeOption("To disable database constraints.", False, "CI tests should verify constraints remain fully enforced.")
            ],
            engineering_principle="Deterministic Verification: Code is only proven when it builds and passes in a clean, reproducible runner environment."
        ),
        explain_it_prompt="Why is it important to prevent merging pull requests when a CI pipeline fails?",
        related_action_key="SETUP_CI_PIPELINE"
    )
}

def get_concept_catalog() -> Dict[str, ConceptDefinition]:
    return CONCEPT_CATALOG

def get_concept(concept_key: str) -> Optional[ConceptDefinition]:
    return CONCEPT_CATALOG.get(concept_key)
