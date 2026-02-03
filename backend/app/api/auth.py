from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db import get_db_session
from app.models import User
from app.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBasic()


def require_user(
    credentials: HTTPBasicCredentials = Depends(security),
    session: Session = Depends(get_db_session),
) -> User:
    """Require a valid user."""

    result = session.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    """Require admin role."""

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(require_user)) -> UserOut:
    """Return current user."""

    return UserOut(id=user.id, username=user.username, role=user.role)
