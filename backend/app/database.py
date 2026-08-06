"""
SQLAlchemy engine + session setup.

Single Postgres database, single engine, connection-pooled by SQLAlchemy itself
(no external pooler needed at this scale).
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # avoids "server closed the connection unexpectedly" on idle connections
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model in the app."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a request-scoped DB session and always
    closes it afterwards, even if the request raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
