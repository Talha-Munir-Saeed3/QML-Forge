# Architecture

## Layers

    Streamlit UI (app.py, pages)
            |
    Service layer  --  core/  (cleaning, features, pipelines, evaluation, recommend)
            |
    Persistence    --  core/db/  (SQLAlchemy models + repository)
            |
    SQLite / PostgreSQL        data/uploads/  (raw CSV files)

The UI contains no business logic. Everything in `core/` can be called from tests or a future REST API.

## Data flow

1. Upload: file saved to `data/uploads/<sha256>.csv`; a `datasets` row is created.
2. User builds a configuration: cleaning steps, optimization settings, algorithm list, seed.
3. The cleaning log is replayed on the raw CSV to produce the working dataframe. The cleaned data is
   not stored; it is *derived* from raw file + steps, which keeps the database small and makes revert trivial.
4. Models run inside scikit-learn pipelines (impute, scale, optional PCA, model) so CV has no leakage.
   Quantum models are sklearn-compatible estimators, so they use the same evaluation code.
5. Configuration (as a `pipeline_versions` row) and results (`runs`, `run_results`) are written in one transaction.

## Key design decisions

| Decision | Reason |
|----------|--------|
| Versions are immutable | History can always be trusted; revert never destroys data |
| Revert = new version with `parent_id` | Gives a branching history, like git, without complexity |
| Store steps, not cleaned data | Reproducible, small, and cheap to diff |
| Quantum models as sklearn estimators | One evaluation path; fair classical vs quantum comparison |
| SQLite first, PostgreSQL via URL | Zero setup for users, a clean upgrade path |
| Preprocessing inside the CV pipeline | Prevents data leakage that inflates metrics |

## Planned modules

    app.py                    Streamlit entry point
    core/cleaning.py          replayable cleaning operations
    core/features.py          X/y building, quantum-readiness notes
    core/pipelines.py         classical and quantum sklearn pipelines
    core/classical_models.py  model registry
    core/quantum_models.py    quantum kernel SVM, VQC, VQR (PennyLane)
    core/evaluation.py        CV metrics, clustering metrics, qubit sweep, stratified sampling
    core/recommend.py         rule-based algorithm recommender
    core/optimization.py      leakage-safe preprocessing and hyperparameter search
    core/db/models.py         SQLAlchemy tables
    core/db/repository.py     save/load/revert/compare versions
    tests/                    pytest suite

## Risks

| Risk | Mitigation |
|------|-----------|
| Quantum simulation is slow | Row/qubit caps, progress bar, background execution later |
| Large CSVs freeze the UI | Chunked reading, sampling for previews, size limit |
| Version configs drift as code changes | Store `schema_version` and library versions with each version |
