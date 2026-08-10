from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.models.project import EvidenceType
from app.models.user import SkillState

class ActionDefinition(BaseModel):
    action_key: str
    skill_name: str
    title_template: str
    description: str
    expected_evidence_types: List[EvidenceType]
    expected_artifact_types: List[str]  # e.g., ["Test file", "Dockerfile"]
    min_current_state: SkillState
    max_current_state: SkillState
    effort: int  # 1=LOW, 2=MEDIUM, 3=HIGH
    prerequisites: Dict[str, SkillState]  # e.g., {"REST APIs": SkillState.WEAK}
    requires_existing_project: bool

# The version-controlled deterministic action catalog
ACTION_CATALOG: List[ActionDefinition] = [
    ActionDefinition(
        action_key="ADD_API_TESTS",
        skill_name="Testing",
        title_template="Add automated tests to {project_name}",
        description="Integrate a testing framework (e.g., pytest) and write automated tests for your API endpoints. This creates new testing artifacts.",
        expected_evidence_types=[EvidenceType.TESTING],
        expected_artifact_types=["Test file"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.DEVELOPING,
        effort=2, # MEDIUM
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=True,
    ),
    ActionDefinition(
        action_key="ADD_DOCKER_CONTAINERIZATION",
        skill_name="Containerization",
        title_template="Containerize {project_name} with Docker",
        description="Add a Dockerfile to your project to containerize the application. This demonstrates infrastructure-as-code and containerization skills.",
        expected_evidence_types=[EvidenceType.CONTAINERIZATION],
        expected_artifact_types=["Dockerfile"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.WEAK,
        effort=1, # LOW
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=True,
    ),
    ActionDefinition(
        action_key="IMPLEMENT_DB_INTEGRATION",
        skill_name="Databases",
        title_template="Integrate a database into {project_name}",
        description="Add database persistence (e.g., PostgreSQL, SQLite) to your existing backend project using an ORM or direct queries.",
        expected_evidence_types=[EvidenceType.DATABASE, EvidenceType.IMPLEMENTATION],
        expected_artifact_types=["Database Models", "Repository"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.DEVELOPING,
        effort=3, # HIGH
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=True,
    ),
    ActionDefinition(
        action_key="CREATE_NEW_API_PROJECT",
        skill_name="REST APIs",
        title_template="Create a new REST API project",
        description="Start a new backend project that implements a REST API. This will build your foundation in API design and implementation.",
        expected_evidence_types=[EvidenceType.API, EvidenceType.IMPLEMENTATION],
        expected_artifact_types=["API Routes", "Controllers"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.WEAK,
        effort=3, # HIGH
        prerequisites={"Python": SkillState.WEAK},
        requires_existing_project=False,
    ),
    ActionDefinition(
        action_key="ADD_CI_PIPELINE",
        skill_name="CI/CD",
        title_template="Add a CI pipeline to {project_name}",
        description="Add a GitHub Actions workflow or similar CI pipeline to automatically build and test your project on every push.",
        expected_evidence_types=[EvidenceType.CI_CD],
        expected_artifact_types=["CI Configuration"],
        min_current_state=SkillState.MISSING,
        max_current_state=SkillState.DEVELOPING,
        effort=2, # MEDIUM
        prerequisites={"Testing": SkillState.WEAK},
        requires_existing_project=True,
    )
]

def get_action_catalog() -> List[ActionDefinition]:
    return ACTION_CATALOG
