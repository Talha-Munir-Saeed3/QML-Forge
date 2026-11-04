"""All database access lives here. Versions are immutable; revert creates a new child version."""
import hashlib
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from .models import Base, Dataset, PipelineVersion, Project, Run, RunResult

SCHEMA_VERSION = 1


def _env_snapshot():
    import numpy, pandas, sklearn
    return {"python": sys.version.split()[0], "platform": platform.system(),
            "numpy": numpy.__version__, "pandas": pandas.__version__, "sklearn": sklearn.__version__}


class Repository:
    def __init__(self, url=None, data_dir="data"):
        self.data_dir = Path(data_dir)
        (self.data_dir / "uploads").mkdir(parents=True, exist_ok=True)
        url = url or os.getenv("QMLFORGE_DB_URL") or f"sqlite:///{self.data_dir / 'qmlforge.db'}"
        self.engine = create_engine(url)
        Base.metadata.create_all(self.engine)

    # ---- projects & datasets
    def create_project(self, name):
        with Session(self.engine) as s:
            p = Project(name=name)
            s.add(p)
            s.commit()
            return p.id

    def add_dataset(self, project_id, filename, content: bytes, n_rows, n_cols):
        digest = hashlib.sha256(content).hexdigest()
        path = self.data_dir / "uploads" / f"{digest}.csv"
        path.write_bytes(content)
        with Session(self.engine) as s:
            d = Dataset(project_id=project_id, filename=filename, sha256=digest,
                        stored_path=str(path), n_rows=n_rows, n_cols=n_cols)
            s.add(d)
            s.commit()
            return d.id

    def delete_dataset(self, dataset_id):
        with Session(self.engine) as s:
            d = s.get(Dataset, dataset_id)
            if d is None:
                return
            for v in s.scalars(select(PipelineVersion).where(PipelineVersion.dataset_id == dataset_id)):
                s.delete(v)
            shared = s.scalar(select(func.count()).select_from(Dataset)
                              .where(Dataset.sha256 == d.sha256, Dataset.id != d.id))
            if not shared:
                Path(d.stored_path).unlink(missing_ok=True)
            s.delete(d)
            s.commit()

    # ---- versions
    def save_version(self, project_id, dataset_id, task, target, cleaning_steps, optimization,
                     algorithms, seed=0, cv_folds=3, label=None, notes=None, parent_id=None):
        with Session(self.engine) as s:
            last = s.scalar(select(func.max(PipelineVersion.version_no))
                            .where(PipelineVersion.project_id == project_id)) or 0
            v = PipelineVersion(project_id=project_id, dataset_id=dataset_id, parent_id=parent_id,
                                version_no=last + 1, label=label, notes=notes, task=task, target=target,
                                cleaning_steps=cleaning_steps, optimization=optimization,
                                algorithms=algorithms, seed=seed, cv_folds=cv_folds,
                                env=_env_snapshot(), schema_version=SCHEMA_VERSION)
            s.add(v)
            s.commit()
            return v.id

    def get_version(self, version_id):
        with Session(self.engine) as s:
            v = s.get(PipelineVersion, version_id)
            if v is None:
                raise KeyError(f"version {version_id} not found")
            return {c.name: getattr(v, c.name) for c in v.__table__.columns}

    def history(self, project_id):
        with Session(self.engine) as s:
            rows = s.scalars(select(PipelineVersion).where(PipelineVersion.project_id == project_id)
                             .order_by(PipelineVersion.version_no.desc()))
            return [{"id": v.id, "version_no": v.version_no, "parent_id": v.parent_id,
                     "label": v.label, "task": v.task, "created_at": v.created_at} for v in rows]

    def revert_to(self, version_id, label=None):
        """Create a NEW version copying an old configuration. The old version is untouched."""
        old = self.get_version(version_id)
        return self.save_version(
            old["project_id"], old["dataset_id"], old["task"], old["target"], old["cleaning_steps"],
            old["optimization"], old["algorithms"], old["seed"], old["cv_folds"],
            label=label or f"Revert to v{old['version_no']}", parent_id=old["id"])

    # ---- runs
    def record_run(self, version_id, results, rows_used=None, status="done"):
        with Session(self.engine) as s:
            run = Run(version_id=version_id, status=status, rows_used=rows_used,
                      finished_at=datetime.now(timezone.utc))
            for r in results:
                r = dict(r)
                run.results.append(RunResult(
                    model_name=r.pop("model"), model_type=r.pop("type", "classical"),
                    params=r.pop("params", {}), error=r.pop("error", None),
                    fit_time_s=r.pop("fit_time_s", None), metrics=r))
            s.add(run)
            s.commit()
            return run.id

    def results_for(self, version_id):
        with Session(self.engine) as s:
            q = (select(RunResult).join(Run, Run.id == RunResult.run_id)
                 .where(Run.version_id == version_id).order_by(RunResult.id))
            return [{"model": r.model_name, "type": r.model_type, "params": r.params,
                     "fit_time_s": r.fit_time_s, "error": r.error, **r.metrics}
                    for r in s.scalars(q)]

    def compare(self, version_a, version_b):
        a, b = self.get_version(version_a), self.get_version(version_b)
        keys = ["cleaning_steps", "optimization", "algorithms", "seed", "cv_folds", "task", "target"]
        settings_diff = {k: (a[k], b[k]) for k in keys if a[k] != b[k]}
        ra = {r["model"]: r for r in self.results_for(version_a)}
        rb = {r["model"]: r for r in self.results_for(version_b)}
        return {"settings_diff": settings_diff, "models_a": ra, "models_b": rb}
