import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Tuple, Dict, Any, Optional
import logging

from app.models.project import (
    RepositorySnapshot, Artifact, RawObservation,
    Evidence, EvidenceType, EvidenceSkill
)
from app.models.taxonomy import Skill

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# CENTRALIZED EVIDENCE RULE REGISTRY
# ---------------------------------------------------------
# Each rule defines:
#   pattern: regex to match in the raw observation text
#   type: EvidenceType
#   quality_score: 0.0 - 1.0
#   target_skills: List of exact Skill names from the taxonomy
#   explanation: human readable reason (optional)
EVIDENCE_RULES = [
    {
        "pattern": r"fastapi\s+(?:import|dependency|detected|found)",
        "type": EvidenceType.API,
        "quality_score": 0.8,
        "target_skills": ["REST APIs", "Python"],
        "explanation": "Detected FastAPI usage for building REST APIs in Python."
    },
    {
        "pattern": r"pytest\s+test\s+function\s+detected",
        "type": EvidenceType.TESTING,
        "quality_score": 0.9,
        "target_skills": ["Testing", "Python"],
        "explanation": "Detected actual executable pytest function."
    },
    {
        "pattern": r"pytest\s+(?:dependency|import)\s+detected",
        "type": EvidenceType.TESTING,
        "quality_score": 0.4,
        "target_skills": ["Testing"],
        "explanation": "Detected pytest dependency, but no actual test execution yet."
    },
    {
        "pattern": r"jwt\s+authentication\s+implementation\s+detected",
        "type": EvidenceType.AUTHENTICATION,
        "quality_score": 0.9,
        "target_skills": ["Authentication", "REST APIs"],
        "explanation": "Concrete JWT authentication logic."
    },
    {
        "pattern": r"dockerfile\s+detected",
        "type": EvidenceType.CONTAINERIZATION,
        "quality_score": 0.8,
        "target_skills": ["Docker"],
        "explanation": "Detected Dockerfile for containerization."
    },
    {
        "pattern": r"sqlalchemy\s+(?:import|dependency)\s+detected",
        "type": EvidenceType.DATABASE,
        "quality_score": 0.8,
        "target_skills": ["Database Design", "Python", "SQL"],
        "explanation": "Detected SQLAlchemy usage for database modeling."
    },
    {
        "pattern": r"postgresql\s+configuration\s+detected",
        "type": EvidenceType.DATABASE,
        "quality_score": 0.7,
        "target_skills": ["PostgreSQL"],
        "explanation": "Detected PostgreSQL-specific configuration."
    },
    {
        "pattern": r"alembic\s+(?:import|dependency)\s+detected",
        "type": EvidenceType.DATABASE,
        "quality_score": 0.7,
        "target_skills": ["Database Design"],
        "explanation": "Detected Alembic for database migrations."
    },
    {
        "pattern": r"readme\s+claims\s+",
        "type": EvidenceType.DOCUMENTATION,
        "quality_score": 0.2,
        "target_skills": [],
        "explanation": "Readme claim is low-quality evidence and doesn't map directly to technical skills without implementation."
    }
]

VANITY_METRICS_PATTERNS = [
    r"github\s+repository\s+has\s+\d+\s+stars",
    r"github\s+followers",
    r"fork\s+count",
    r"repository\s+popularity"
]

def calculate_freshness(captured_at: datetime) -> float:
    """
    Calculate freshness based on snapshot timestamp.
    Returns value between 0.1 and 1.0.
    """
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    days_old = (now - captured_at).days
    if days_old < 0:
        days_old = 0
        
    # Formula: max(0.1, 1.0 - (days_old / 365))
    freshness = max(0.1, 1.0 - (days_old / 365.0))
    return float(round(freshness, 4))


def _match_rule(observation_text: str) -> Optional[Dict[str, Any]]:
    # 1. Ignore vanity metrics
    text_lower = observation_text.lower()
    for v_pattern in VANITY_METRICS_PATTERNS:
        if re.search(v_pattern, text_lower):
            return None # Explicitly ignored
            
    # 2. Find first matching rule
    for rule in EVIDENCE_RULES:
        if re.search(rule["pattern"], text_lower):
            return rule
            
    return None

def rebuild_snapshot_evidence(snapshot_id: int, db: Session):
    """
    Idempotent operation to regenerate Evidence for a given snapshot.
    1. Deletes existing Evidence linked to the snapshot.
    2. Fetches all RawObservations for the snapshot.
    3. Runs the evaluation engine and creates new Evidence + EvidenceSkill records.
    """
    snapshot = db.query(RepositorySnapshot).filter(RepositorySnapshot.id == snapshot_id).first()
    if not snapshot:
        logger.error(f"Cannot rebuild evidence: snapshot {snapshot_id} not found.")
        return
        
    # 1. Delete existing Evidence by finding all observations in the snapshot
    # Since Evidence is tied to RawObservation, and RawObservation is tied to Artifact,
    # which is tied to Snapshot, we can do a joined query.
    evidence_to_delete = db.query(Evidence).join(
        RawObservation
    ).join(
        Artifact
    ).filter(
        Artifact.snapshot_id == snapshot_id
    ).all()
    
    for ev in evidence_to_delete:
        db.delete(ev)
    db.commit()
    
    # 2. Fetch all RawObservations
    observations = db.query(RawObservation).join(
        Artifact
    ).filter(
        Artifact.snapshot_id == snapshot_id
    ).all()
    
    # Pre-fetch all available skills in a map to avoid DB queries inside the loop
    all_skills = {s.name: s.id for s in db.query(Skill).all()}
    
    freshness = calculate_freshness(snapshot.captured_at)
    
    # 3. Process each observation
    for obs in observations:
        rule = _match_rule(obs.observation_text)
        if not rule:
            continue
            
        # Create Evidence
        # Safe source reference privacy: Do not include full source lines, just the file path and optionally the line number
        safe_source_ref = f"{obs.artifact.file_path}"
        if obs.line_numbers:
            safe_source_ref += f":{obs.line_numbers}"
            
        evidence = Evidence(
            raw_observation_id=obs.id,
            type=rule["type"],
            quality_score=rule["quality_score"],
            freshness_weight=freshness,
            source_reference=safe_source_ref
        )
        db.add(evidence)
        db.flush() # flush to get evidence.id
        
        # Map to Skills
        for skill_name in rule["target_skills"]:
            if skill_name in all_skills:
                skill_id = all_skills[skill_name]
                evidence_skill = EvidenceSkill(
                    evidence_id=evidence.id,
                    skill_id=skill_id
                )
                db.add(evidence_skill)
            else:
                logger.warning(f"Engine rule specified missing taxonomy skill: '{skill_name}'. Ignoring.")
                
    db.commit()
