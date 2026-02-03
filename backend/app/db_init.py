from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from app.db import Base, engine
from app.models import (
    Assignment,
    InfrastructureItem,
    Module,
    Project,
    ProjectCoefficient,
    ProjectConnection,
    ProjectInfrastructure,
    ProjectModule,
    Rate,
    User,
)


def init_and_verify_db() -> None:
    """Create tables and verify expected schema."""

    Base.metadata.create_all(bind=engine)
    _verify_schema(engine)


def _verify_schema(db_engine: Engine) -> None:
    inspector = inspect(db_engine)
    expected = {
        "modules": _columns(Module),
        "projects": _columns(Project),
        "project_modules": _columns(ProjectModule),
        "rates": _columns(Rate),
        "assignments": _columns(Assignment),
        "project_coefficients": _columns(ProjectCoefficient),
        "infrastructure_items": _columns(InfrastructureItem),
        "project_infrastructure": _columns(ProjectInfrastructure),
        "project_connections": _columns(ProjectConnection),
        "users": _columns(User),
    }

    missing_tables = [table for table in expected if not inspector.has_table(table)]
    if missing_tables:
        raise RuntimeError(f"Missing tables: {', '.join(missing_tables)}")

    for table_name, expected_columns in expected.items():
        columns = inspector.get_columns(table_name)
        present = {column["name"] for column in columns}
        missing = expected_columns - present
        if missing:
            raise RuntimeError(
                f"Missing columns in {table_name}: {', '.join(sorted(missing))}"
            )


def _columns(model: type[Base]) -> set[str]:
    return {column.name for column in model.__table__.columns}
