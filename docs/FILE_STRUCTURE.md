# QML Forge File Structure

This document describes the main files and folders in the project.

```text
QML-Forge/
├── app.py                    # Streamlit application entry point
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Pytest configuration
├── .env.example              # Example local environment configuration
├── Dockerfile                # Container image definition
├── docker-compose.yml        # Local container orchestration
├── core/
│   ├── config.py             # Shared application constants and local environment loading
│   ├── upload.py             # CSV, URL, and Kaggle ingestion and validation
│   ├── cleaning.py           # Replayable cleaning operations and pipeline
│   ├── features.py           # Feature/target construction and quantum readiness
│   ├── optimization.py       # Scaling, feature selection, PCA, and search helpers
│   ├── pipelines.py          # Leakage-safe classical and quantum pipelines
│   ├── classical_models.py   # Classical model registries
│   ├── quantum_models.py     # Optional PennyLane model implementations
│   ├── recommend.py          # Rule-based recommended model selection
│   ├── evaluation.py         # Cross-validation and clustering evaluation
│   └── db/
│       ├── models.py          # SQLAlchemy database models
│       └── repository.py      # Database access and immutable version operations
├── data/
│   └── samples/               # Small demo CSV datasets
├── tests/                     # Automated tests for core functionality
├── docs/                      # Requirements, architecture, database, and project documentation
└── .github/
    └── workflows/             # Continuous-integration workflows
```

Business logic belongs in `core/`. The Streamlit entry point should coordinate user interaction
and call reusable functions from the core modules.
