# QML Forge File Structure

This is the complete application file map. Generated files, virtual environments, uploaded data,
and local databases are intentionally excluded.

```text
QML-Forge/
├── .dockerignore
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── LICENSE
├── README.md
├── app.py
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── classical_models.py
│   ├── cleaning.py
│   ├── config.py
│   ├── evaluation.py
│   ├── features.py
│   ├── optimization.py
│   ├── pipelines.py
│   ├── quantum_models.py
│   ├── recommend.py
│   ├── ui.py
│   ├── upload.py
│   └── db/
│       ├── __init__.py
│       ├── models.py
│       └── repository.py
├── data/
│   └── samples/
│       ├── iris.csv
│       ├── messy.csv
│       └── regression.csv
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── DESCRIPTION.md
│   ├── FILE_STRUCTURE.md
│   ├── PRD.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   ├── USER_FLOW.md
│   └── images/
│       └── .gitkeep
├── pages/
│   ├── Upload_Clean.py
│   ├── Define_Task.py
│   ├── Train_Compare.py
│   └── History.py
├── tests/
│   ├── test_cleaning.py
│   ├── test_evaluation.py
│   ├── test_features.py
│   ├── test_quantum_models.py
│   ├── test_recommend.py
│   ├── test_repository.py
│   └── test_upload.py
└── .github/
    └── workflows/
        └── ci.yml
```

## UI responsibilities

- `app.py` is the Streamlit home page and shared entry point.
- `pages/1_Upload_Clean.py` handles data ingestion, profiling, and cleaning.
- `pages/2_Define_Task.py` handles task and target selection.
- `pages/3_Train_Compare.py` handles model selection, optimization, evaluation, and saving runs.
- `pages/4_History.py` handles version history, comparison, revert, and deletion.
- `core/ui.py` contains shared UI/session/database helpers used by the pages.

Business logic remains in `core/`; the page files coordinate user interaction and call reusable
core functions.
