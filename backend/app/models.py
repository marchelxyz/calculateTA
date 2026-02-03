from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Role(str, Enum):
    """Project role types for estimation."""

    frontend = "frontend"
    backend = "backend"
    qa = "qa"
    pm = "pm"
    ux = "ux"


class Level(str, Enum):
    """Seniority levels for pricing."""

    junior = "junior"
    middle = "middle"
    senior = "senior"


class Module(Base):
    """Catalog module with default hours."""

    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    hours_frontend: Mapped[float] = mapped_column(Float, default=0)
    hours_backend: Mapped[float] = mapped_column(Float, default=0)
    hours_qa: Mapped[float] = mapped_column(Float, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project_modules: Mapped[list["ProjectModule"]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
    )


class Project(Base):
    """Project entity containing estimation parameters."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")

    uncertainty_level: Mapped[str] = mapped_column(String(32), default="known")
    uiux_level: Mapped[str] = mapped_column(String(32), default="mvp")
    legacy_code: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    modules: Mapped[list["ProjectModule"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    coefficients: Mapped[list["ProjectCoefficient"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectModule(Base):
    """Module instance inside a project with overrides."""

    __tablename__ = "project_modules"
    __table_args__ = (UniqueConstraint("project_id", "module_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"))

    custom_name: Mapped[str] = mapped_column(String(128), default="")
    override_frontend: Mapped[float | None] = mapped_column(Float, nullable=True)
    override_backend: Mapped[float | None] = mapped_column(Float, nullable=True)
    override_qa: Mapped[float | None] = mapped_column(Float, nullable=True)

    uncertainty_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    uiux_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    legacy_code: Mapped[bool | None] = mapped_column(nullable=True)

    project: Mapped[Project] = relationship(back_populates="modules")
    module: Mapped[Module] = relationship(back_populates="project_modules")


class Rate(Base):
    """Hourly rate per role and level."""

    __tablename__ = "rates"
    __table_args__ = (UniqueConstraint("role", "level"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(32))
    level: Mapped[str] = mapped_column(String(32))
    hourly_rate: Mapped[float] = mapped_column(Float, default=0)


class Assignment(Base):
    """Assignment of role level for a project module."""

    __tablename__ = "assignments"
    __table_args__ = (UniqueConstraint("project_id", "project_module_id", "role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    project_module_id: Mapped[int] = mapped_column(ForeignKey("project_modules.id"))
    role: Mapped[str] = mapped_column(String(32))
    level: Mapped[str] = mapped_column(String(32))

    project: Mapped[Project] = relationship(back_populates="assignments")
    project_module: Mapped[ProjectModule] = relationship()


class ProjectCoefficient(Base):
    """Project-level complexity coefficient."""

    __tablename__ = "project_coefficients"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(64))
    multiplier: Mapped[float] = mapped_column(Float, default=1.0)

    project: Mapped[Project] = relationship(back_populates="coefficients")
