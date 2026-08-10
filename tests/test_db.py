from app.db.seed import seed_taxonomy
from app.database.database import Base
from app.models.taxonomy import TargetRole, Skill
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

def test_idempotent_seed():
    engine = create_engine(settings.TEST_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    # Run seed once
    import app.db.seed
    
    # We must patch the SessionLocal inside seed.py to use our test DB for this isolated test
    original_session = app.db.seed.SessionLocal
    app.db.seed.SessionLocal = Session
    
    try:
        app.db.seed.seed_taxonomy()
        
        db = Session()
        roles_count_1 = db.query(TargetRole).count()
        skills_count_1 = db.query(Skill).count()
        
        assert roles_count_1 == 1
        assert skills_count_1 > 0
        
        # Run seed twice
        app.db.seed.seed_taxonomy()
        
        roles_count_2 = db.query(TargetRole).count()
        skills_count_2 = db.query(Skill).count()
        
        # Verify no duplicates
        assert roles_count_1 == roles_count_2
        assert skills_count_1 == skills_count_2
    finally:
        app.db.seed.SessionLocal = original_session
        if 'db' in locals():
            db.close()
