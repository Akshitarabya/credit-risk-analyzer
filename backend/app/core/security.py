"""
Password hashing and JWT creation/verification.

Scope note: a single JWT access token with a fixed expiry (default 60 minutes)
is used, with no refresh-token rotation. When the token expires, the user
logs in again. This is a deliberate simplification for the project's scope,
not an oversight.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(*, subject: uuid.UUID, role: str) -> str:
    """
    Encodes a JWT whose payload carries the user id (`sub`) and `role`, so
    every downstream request can authorize without hitting the DB for the
    role check (the DB is still hit to load the full user via `sub`).
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class InvalidTokenError(Exception):
    pass


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Could not validate credentials") from exc
