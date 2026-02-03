from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import Rate
from app.schemas import RateOut, RateUpsert

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("", response_model=list[RateOut])
def list_rates(session: Session = Depends(get_db_session)) -> list[RateOut]:
    """List all rates."""

    result = session.execute(select(Rate))
    return [RateOut(**rate.__dict__) for rate in result.scalars()]


@router.put("", response_model=list[RateOut])
def upsert_rates(
    payload: list[RateUpsert],
    session: Session = Depends(get_db_session),
) -> list[RateOut]:
    """Upsert rates."""

    results = []
    for rate_payload in payload:
        rate = _get_rate(session, rate_payload.role, rate_payload.level)
        if rate:
            rate.hourly_rate = rate_payload.hourly_rate
        else:
            rate = Rate(
                role=rate_payload.role,
                level=rate_payload.level,
                hourly_rate=rate_payload.hourly_rate,
            )
            session.add(rate)
        session.flush()
        results.append(RateOut(**rate.__dict__))
    session.commit()
    return results


def _get_rate(session: Session, role: str, level: str) -> Rate | None:
    result = session.execute(
        select(Rate).where(Rate.role == role).where(Rate.level == level)
    )
    return result.scalar_one_or_none()
