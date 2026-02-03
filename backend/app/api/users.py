from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.core.security import hash_password
from app.db import get_db_session
from app.models import User
from app.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    _: User = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> list[UserOut]:
    """List users (admin only)."""

    result = session.execute(select(User))
    return [UserOut(id=user.id, username=user.username, role=user.role) for user in result.scalars()]


@router.post("", response_model=UserOut)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> UserOut:
    """Create user (admin only)."""

    existing = session.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut(id=user.id, username=user.username, role=user.role)
