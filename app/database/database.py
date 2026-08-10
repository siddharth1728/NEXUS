from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# In SQLAlchemy 2.0+, declarative_base is in sqlalchemy.orm
Base = declarative_base()

def get_engine(url: str):
    return create_engine(url, echo=settings.ENVIRONMENT == "development")

engine = get_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
