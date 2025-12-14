"""
Database initialization and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os

DATABASE_FILE = "health_database.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize the database and create all tables"""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {DATABASE_FILE}")


def get_session() -> Session:
    """Get a database session"""
    return SessionLocal()


def close_session(session: Session):
    """Close a database session"""
    session.close()

