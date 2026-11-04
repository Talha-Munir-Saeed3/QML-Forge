from datetime import datetime, timezone
from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(default=_now)
    datasets = relationship("Dataset", cascade="all, delete-orphan")
    versions = relationship("PipelineVersion", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    filename: Mapped[str] = mapped_column(String(300))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    stored_path: Mapped[str] = mapped_column(String(500))
    n_rows: Mapped[int]
    n_cols: Mapped[int]
    uploaded_at: Mapped[datetime] = mapped_column(default=_now)


class PipelineVersion(Base):
    __tablename__ = "pipeline_versions"
    __table_args__ = (UniqueConstraint("project_id", "version_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("pipeline_versions.id"), nullable=True)
    version_no: Mapped[int]
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    task: Mapped[str] = mapped_column(String(20))
    target: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cleaning_steps: Mapped[list] = mapped_column(JSON, default=list)
    optimization: Mapped[dict] = mapped_column(JSON, default=dict)
    algorithms: Mapped[list] = mapped_column(JSON, default=list)
    seed: Mapped[int] = mapped_column(default=0)
    cv_folds: Mapped[int] = mapped_column(default=3)
    env: Mapped[dict] = mapped_column(JSON, default=dict)
    schema_version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=_now)
    runs = relationship("Run", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("pipeline_versions.id"))
    status: Mapped[str] = mapped_column(String(20), default="running")
    started_at: Mapped[datetime] = mapped_column(default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    rows_used: Mapped[int | None] = mapped_column(nullable=True)
    results = relationship("RunResult", cascade="all, delete-orphan")


class RunResult(Base):
    __tablename__ = "run_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(100))
    model_type: Mapped[str] = mapped_column(String(20))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    fit_time_s: Mapped[float | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
