# Database design

ORM: SQLAlchemy 2.x. Default URL: `sqlite:///data/qmlforge.db` (override with `QMLFORGE_DB_URL`).

## Tables

**projects**: `id`, `name`, `created_at`

**datasets**: `id`, `project_id`, `filename`, `sha256`, `stored_path`, `n_rows`, `n_cols`, `uploaded_at`

**pipeline_versions** (one row = one immutable configuration)
`id`, `project_id`, `dataset_id`, `parent_id` (nullable, self-reference), `version_no` (per project),
`label`, `notes`, `task`, `target`, `cleaning_steps` (JSON), `optimization` (JSON),
`algorithms` (JSON list with parameters), `seed`, `cv_folds`, `env` (JSON: library versions),
`schema_version`, `created_at`

**runs**: `id`, `version_id`, `status` (`running` / `done` / `failed`), `started_at`, `finished_at`, `rows_used`

**run_results**: `id`, `run_id`, `model_name`, `model_type` (`classical` / `quantum`), `params` (JSON),
`metrics` (JSON), `fit_time_s`, `error`

## Example JSON

    cleaning_steps: [{"op": "impute", "params": {"cols": ["age"], "strategy": "median"}},
                     {"op": "drop_duplicates", "params": {}}]
    optimization:   {"scaler": "standard", "pca_components": 4, "feature_selection": "mutual_info",
                     "search": {"method": "random", "n_iter": 20}}
    algorithms:     [{"name": "Random Forest", "params": {"n_estimators": 200}},
                     {"name": "Quantum Kernel SVM", "params": {"n_qubits": 4}}]

## Version semantics

- A version is **never edited** after it is saved.
- **Revert to version N**: the UI loads N's configuration; saving it creates version N+k with `parent_id = N`.
- **History** is a tree: following `parent_id` shows how a setup evolved.
- **Compare**: diff the JSON columns of two versions and join their `run_results` by `model_name`.
- **Delete dataset**: cascades to its versions and results; the stored file is removed.

## Indexes
`datasets(sha256)`, `pipeline_versions(project_id, version_no)` (unique), `run_results(run_id)`.
