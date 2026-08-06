"""
Import every ORM model here so that a single `import app.models` registers
all tables on `Base.metadata` — this is what Alembic's autogenerate relies on.
"""
from app.models.user import User, UserRole  # noqa: F401
