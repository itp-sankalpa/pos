"""
Database initialization and session management.
Uses SQLAlchemy 2.0 with Mapped[] syntax and SQLite in WAL mode.
"""

import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from config import DB_URL

logger = logging.getLogger(__name__)

engine = None
SessionFactory = None


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


def init_db():
    """Initialize the database engine, enable WAL mode, and create tables."""
    global engine, SessionFactory

    logger.info(f"Initializing database at: {DB_URL}")
    engine = create_engine(DB_URL, echo=False, pool_pre_ping=True)

    # Enable WAL mode for better concurrent read performance
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Import all models so they register on Base.metadata
    import models  # noqa: F401

    Base.metadata.create_all(engine)

    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    logger.info("Database tables created/verified successfully.")


def get_session() -> Session:
    """Return a new SQLAlchemy session."""
    if SessionFactory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return SessionFactory()


class SessionContext:
    """Context manager for session-scoped database operations."""

    def __init__(self):
        self.session = None

    def __enter__(self) -> Session:
        self.session = get_session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
                raise
        self.session.close()
