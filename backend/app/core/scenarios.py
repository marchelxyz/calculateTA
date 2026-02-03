from __future__ import annotations

from app.core.config import settings


def optimistic_value(value: float) -> float:
    """Return optimistic scenario value."""

    return value * settings.optimistic_multiplier


def pessimistic_value(value: float) -> float:
    """Return pessimistic scenario value."""

    return value * settings.pessimistic_multiplier
