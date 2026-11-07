# QML Forge File Structure

This is the complete application file map. Generated files, virtual environments, uploaded data,
and local databases are intentionally excluded.

```text
QML-Forge/
├── .dockerignore
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── app.py
├── CHANGELOG.md
├── CONTRIBUTING.md
├── core/
│   ├── __init__.py
│   ├── classical_models.py
│   ├── cleaning.py
│   ├── config.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── evaluation.py
│   ├── features.py
│   ├── optimization.py
│   ├── pipelines.py
│   ├── quantum_models.py
│   ├── recommend.py
│   ├── ui.py
│   └── upload.py
├── data/
│   └── samples/
│       ├── iris.csv
│       ├── messy.csv
│       └── regression.csv
├── docker-compose.yml
├── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CODEBASE_FILES.md
│   ├── DATABASE.md
│   ├── DESCRIPTION.md
│   ├── FILE_STRUCTURE.md
│   ├── PRD.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   ├── USER_FLOW.md
│   └── images/
│       ├── .gitkeep
│       └── dashboard-placeholder.svg
├── LICENSE
├── pages/
│   ├── Define_Task.py
│   ├── History.py
│   ├── Train_Compare.py
│   └── Upload_Clean.py
├── pyproject.toml
├── README.md
├── requirements.txt
└── tests/
    ├── test_cleaning.py
    ├── test_evaluation.py
    ├── test_features.py
    ├── test_quantum_models.py
    ├── test_recommend.py
    ├── test_repository.py
    └── test_upload.py
```

## UI responsibilities

- `app.py` is the Streamlit home page and shared entry point.
- `pages/Upload_Clean.py` handles data ingestion, profiling, and cleaning.
- `pages/Define_Task.py` handles task and target selection.
- `pages/Train_Compare.py` handles model selection, optimization, evaluation, and saving runs.
- `pages/History.py` handles version history, comparison, revert, and deletion.
- `core/ui.py` contains shared UI/session/database helpers used by the pages.

Business logic remains in `core/`; the page files coordinate user interaction and call reusable
core functions.
