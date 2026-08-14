from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.models.project import EvidenceType
from app.models.user import SkillState

class ActionDefinition(BaseModel):
    action_key: str
    skill_name: str
    title_template: str
    description: str
    mission_brief: str
    expected_evidence_types: List[EvidenceType]
    expected_artifact_types: List[str]  # e.g., ["Test file", "Dockerfile"]
    min_current_state: SkillState = SkillState.MISSING
    max_current_state: SkillState = SkillState.DEVELOPING
    target_state: SkillState = SkillState.DEVELOPING
    effort: int = 2  # 1=LOW, 2=MEDIUM, 3=HIGH
    prerequisites: Dict[str, SkillState] = {}  # e.g., {"Python": SkillState.WEAK}
    requires_existing_project: bool = True
    allowed_project_context: Optional[str] = None
    verification_expectations: str = "NEXUS will scan repository files for corresponding evidence types during synchronization."

    @property
    def applicable_skill(self) -> str:
        return self.skill_name

# The version-controlled deterministic action catalog for Proof Quests
ACTION_CATALOG: List[ActionDefinition] = [
    ActionDefinition(
        action_key="ADD_API_TESTS",
        skill_name="Testing",
        title_template="Prove automated testing in {project_name}",
        description="Integrate a testing framework (pytest) and write automated tests with assertions for your API endpoints.",
        mission_brief="Create a `tests/` directory with `test_*.py` files, implement pytest functions asserting expected API responses and business logic.",
        expected_evidence_types=[EvidenceType.TESTING],
        expected_artifact_types=["Test file", "pytest configuration"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.DEVELOPING,
        target_state=SkillState.DEVELOPING,
        effort=2, # MEDIUM
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=True,
        allowed_project_context="Existing Python or API repository",
        verification_expectations="NEXUS will scan for pytest imports and test functions (`test_*`) across repository files."
    ),
    ActionDefinition(
        action_key="ADD_DOCKER_CONTAINERIZATION",
        skill_name="Docker",
        title_template="Containerize {project_name} with Docker",
        description="Add a Dockerfile to your project to containerize the application and declare reproducible runtime dependencies.",
        mission_brief="Author a clean, production-ready `Dockerfile` in the root of your project specifying the base image, dependency installation, and entrypoint command.",
        expected_evidence_types=[EvidenceType.CONTAINERIZATION],
        expected_artifact_types=["Dockerfile", "Container specification"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.WEAK,
        target_state=SkillState.DEVELOPING,
        effort=1, # LOW
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=True,
        allowed_project_context="Any functional repository",
        verification_expectations="NEXUS will detect the presence and structure of a `Dockerfile` in your repository tree."
    ),
    ActionDefinition(
        action_key="IMPLEMENT_DB_INTEGRATION",
        skill_name="PostgreSQL",
        title_template="Integrate database persistence in {project_name}",
        description="Add database modeling and persistence to your backend project using an ORM or structured SQL queries.",
        mission_brief="Configure PostgreSQL connection settings and define SQLAlchemy declarative models for relational entity persistence.",
        expected_evidence_types=[EvidenceType.DATABASE, EvidenceType.IMPLEMENTATION],
        expected_artifact_types=["Database Models", "PostgreSQL Config"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.DEVELOPING,
        target_state=SkillState.DEVELOPING,
        effort=3, # HIGH
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=True,
        allowed_project_context="Backend or API service",
        verification_expectations="NEXUS will detect PostgreSQL configuration strings and SQLAlchemy database models."
    ),
    ActionDefinition(
        action_key="IMPLEMENT_DATABASE_MIGRATIONS",
        skill_name="Database Design",
        title_template="Configure database migrations in {project_name}",
        description="Implement schema migration tracking using Alembic to manage relational schema evolutions safely.",
        mission_brief="Initialize an Alembic environment (`alembic/`), define migration versions, and link them to your database models.",
        expected_evidence_types=[EvidenceType.DATABASE],
        expected_artifact_types=["Alembic migration scripts", "alembic.ini"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.DEVELOPING,
        target_state=SkillState.DEVELOPING,
        effort=2, # MEDIUM
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=True,
        allowed_project_context="Database or ORM project",
        verification_expectations="NEXUS will detect Alembic migration scripts and dependency declarations."
    ),
    ActionDefinition(
        action_key="CREATE_NEW_API_PROJECT",
        skill_name="REST APIs",
        title_template="Build a new REST API service",
        description="Create and publish a backend service that exposes RESTful HTTP endpoints using FastAPI or standard Python web frameworks.",
        mission_brief="Initialize a new repository with FastAPI route definitions, request/response validation schemas, and HTTP verb handlers.",
        expected_evidence_types=[EvidenceType.API, EvidenceType.IMPLEMENTATION],
        expected_artifact_types=["API Routes", "Pydantic Schemas"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.WEAK,
        target_state=SkillState.DEVELOPING,
        effort=3, # HIGH
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=False,
        allowed_project_context=None,
        verification_expectations="NEXUS will detect FastAPI router decorators and HTTP endpoint definitions in the surveyed project."
    ),
    ActionDefinition(
        action_key="ADD_CI_PIPELINE",
        skill_name="CI/CD",
        title_template="Add continuous integration to {project_name}",
        description="Add a GitHub Actions workflow to automatically test and lint your codebase on every pull request.",
        mission_brief="Create `.github/workflows/ci.yml` defining automated test execution and linting stages triggered on push and pull_request.",
        expected_evidence_types=[EvidenceType.CI_CD],
        expected_artifact_types=["GitHub Actions workflow", "CI config"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.DEVELOPING,
        target_state=SkillState.DEVELOPING,
        effort=2, # MEDIUM
        prerequisites={"Testing": SkillState.WEAK},
        requires_existing_project=True,
        allowed_project_context="Any repository with tests",
        verification_expectations="NEXUS will detect CI configuration files (`.github/workflows/*.yml`)."
    ),
    ActionDefinition(
        action_key="ADD_JWT_AUTHENTICATION",
        skill_name="Authentication",
        title_template="Implement JWT authentication in {project_name}",
        description="Implement secure token-based authentication with password hashing and JWT claims verification.",
        mission_brief="Implement login and token verification endpoints using bcrypt password hashing and HMAC-SHA256 JWT generation.",
        expected_evidence_types=[EvidenceType.AUTHENTICATION],
        expected_artifact_types=["Security utilities", "Auth router"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.DEVELOPING,
        target_state=SkillState.STRONG,
        effort=2, # MEDIUM
        prerequisites={"REST APIs": SkillState.WEAK},
        requires_existing_project=True,
        allowed_project_context="API repository",
        verification_expectations="NEXUS will detect JWT token generation, header extraction, or password hashing libraries."
    )
]

def get_action_catalog() -> List[ActionDefinition]:
    return ACTION_CATALOG
