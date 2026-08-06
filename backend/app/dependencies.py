"""
Shared FastAPI dependencies: pulling the current user off the JWT, and
guarding routes by role.
"""
import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, decode_access_token
from app.database import get_db
from app.models.user import User, UserRole

# tokenUrl only documents "where to get a token" for the interactive Swagger
# docs (/docs) — the actual auth endpoint is POST /auth/login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=True)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except InvalidTokenError as exc:
        raise credentials_error from exc

    user = db.get(User, uuid.UUID(user_id))
    if user is None:
        raise credentials_error
    return user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    """
    Usage: `current_user: User = Depends(require_role(UserRole.STAFF, UserRole.ADMIN))`

    Returns a dependency that first resolves the current user from the JWT,
    then checks their role is one of `allowed_roles`, raising 403 otherwise.
    """

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _checker
