"""
Database engine + session management.
Every model (in app/models/) inherits from `Base` defined here.
Every route that needs DB access takes `db: Session = Depends(get_db)`.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# The engine manages the actual connection pool to Postgres (Neon).
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Each request gets its own Session, created from this factory.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All SQLAlchemy models (app/models/*.py) inherit from this Base,
# which is how Alembic autogenerates migrations from model changes.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a DB session for the duration of one
    request, and guarantees it's closed afterward even if an error
    occurs. Used as: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()