from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.taxonomy import TargetRole, Skill, TargetRoleSkill

def seed_taxonomy():
    db: Session = SessionLocal()
    try:
        # Seed Backend Engineer Role
        backend_role = db.query(TargetRole).filter(TargetRole.name == "Backend Engineer").first()
        if not backend_role:
            backend_role = TargetRole(name="Backend Engineer", description="Builds server-side logic and database architecture.")
            db.add(backend_role)
            db.commit()
            db.refresh(backend_role)

        skills_data = [
            {"name": "Python", "category": "Programming Fundamentals"},
            {"name": "REST APIs", "category": "APIs"},
            {"name": "SQL", "category": "Databases"},
            {"name": "PostgreSQL", "category": "Databases"},
            {"name": "Database Design", "category": "Databases"},
            {"name": "Authentication", "category": "Security"},
            {"name": "Testing", "category": "Quality"},
            {"name": "Git", "category": "Version Control"},
            {"name": "Docker", "category": "Deployment"}
        ]
        
        # Insert skills idempotently
        for skill_dict in skills_data:
            skill = db.query(Skill).filter(Skill.name == skill_dict["name"]).first()
            if not skill:
                skill = Skill(**skill_dict)
                db.add(skill)
        db.commit()
        
        # Map target role skills idempotently
        # Weights and min expectations
        mappings = {
            "REST APIs": (1.0, "Developing"),
            "PostgreSQL": (0.9, "Developing"),
            "Authentication": (0.9, "Developing"),
            "Testing": (0.8, "Developing"),
            "Docker": (0.7, "Weak")
        }
        
        for skill_name, (weight, min_state) in mappings.items():
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if skill:
                mapping = db.query(TargetRoleSkill).filter(
                    TargetRoleSkill.target_role_id == backend_role.id,
                    TargetRoleSkill.skill_id == skill.id
                ).first()
                if not mapping:
                    mapping = TargetRoleSkill(
                        target_role_id=backend_role.id,
                        skill_id=skill.id,
                        importance_weight=weight,
                        minimum_expected_state=min_state
                    )
                    db.add(mapping)
        db.commit()
        
        print("Taxonomy successfully seeded!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_taxonomy()
