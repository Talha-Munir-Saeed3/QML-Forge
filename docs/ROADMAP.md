# Roadmap

| Phase | Goal | Deliverables |
|-------|------|--------------|
| 0. Done | Prototype | Streamlit UI, cleaning log, classical + quantum models, evaluation, qubit sweep |
| 1. MVP | Persistence + versions | SQLite repository, save every run as a version, history page, revert (FR-23 to FR-26), tests |
| 2. v1 | Optimization + recommender | Feature selection, hyperparameter search, rule-based recommended preset, version compare, charts |
| 3. v1.1 | Polish and packaging | Dockerfile, PDF/HTML report, delete/archive, better error messages, docs site |
| 4. v2 | Multi-user | Auth, per-user projects, PostgreSQL deployment, background job queue |
| 5. Stretch | Research features | Quantum feature selection, noise models, real-hardware backend |

## Definition of done (per phase)
Tests pass, docs updated, a demo dataset runs end-to-end, no known data-loss bugs.
