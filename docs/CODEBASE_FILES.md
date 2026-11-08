# QML Forge Codebase Files

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

## First project files

These are project configuration, documentation, and entry-point files. They are not part of the
machine-learning algorithms themselves.

### `.dockerignore`

This tells Docker which files and folders to leave out when Docker sends the project to the image
builder. It keeps local virtual environments, caches, the local database, uploaded files, and
`.env` credentials out of the Docker build context.

It is similar to `.gitignore`, but it controls Docker build input rather than Git tracking. It
does not ignore file extensions only; each line can match a file, folder, or pattern.

### `.env.example`

This is a safe template showing which environment variables the application can use. A developer
can copy it to `.env` and fill in local values, such as the database URL or Kaggle credentials.
The example must not contain real passwords or tokens. The real `.env` is intentionally ignored
by Git and should remain private.

### `.github/`

This is a special folder recognized by GitHub. It stores repository automation and GitHub-specific
configuration.

#### `.github/workflows/ci.yml`

This is a GitHub Actions workflow. GitHub Actions runs automated jobs on GitHub's servers when
specified events happen in the repository.

The `ci.yml` workflow is continuous integration (CI). It runs when code is pushed or when a pull
request is opened or updated. Its job:

1. Starts an Ubuntu runner.
2. Checks out the repository code.
3. Installs Python 3.13.
4. Installs the packages from `requirements.txt`.
5. Runs `pytest -q`.

If the tests fail, GitHub reports the workflow as failed. This gives contributors an automatic
check that their changes do not break the project before a pull request is merged. The workflow
does not run on the user's computer unless they run the same commands locally.

### `.gitignore`

This tells Git which local files should not be tracked or committed. In this project it excludes
Python caches, the virtual environment, generated data, the local SQLite database, uploaded files,
`.env`, and test caches.

`.gitignore` protects the repository from accidentally committing generated or private files. It
does not provide encryption or protect a file that has already been committed.

### `app.py`

This is the Streamlit home page and application entry point. It creates the shared page layout,
shows the project workflow, and links to the pages in the `pages/` folder. The detailed screen
logic is kept in those page files rather than being placed entirely in `app.py`.

### `CHANGELOG.md`

This records notable changes made to the project, grouped by release or development period. It
helps users and contributors see what functionality was added, changed, or fixed without reading
the entire Git history.

The current `Unreleased` section lists completed changes that have not yet been assigned to a
published release.

### `CONTRIBUTING.md`

This gives contributors the project rules for making changes. It explains how to install
dependencies, run tests, organize business logic and UI code, keep commits focused, and avoid
committing credentials or generated data.

It is intended for anyone who wants to modify QML Forge, including the original author and future
contributors.

## `core/__init__.py`

This file is currently empty. Its practical role is to mark `core/` as a regular Python package,
so Python can treat the files inside it as importable modules.

For example, another module inside `core/` can use a relative import:

```python
from .upload import parse_csv_bytes
```

Code outside the package, such as a page, can use an absolute package import:

```python
from core.ui import setup_page
```

Modern Python can also support some packages without an `__init__.py`, but keeping this file makes
the package boundary explicit and supports the import style used by this project.

## `core/classical_models.py`

This file imports scikit-learn model classes and organizes model factories into three dictionaries:

- `CLASSIFIERS` contains models that predict discrete labels.
- `REGRESSORS` contains models that predict continuous values.
- `CLUSTERERS` contains models that group rows without a target label.

The dictionary keys are the names shown to the user. The values are lambda functions that create a
fresh model when called. For example:

```python
CLASSIFIERS["Logistic Regression"]()
```

creates a new `LogisticRegression` instance.

### Why the values use `lambda`

A lambda is a small anonymous function. In this file it acts as a factory or blueprint, not as the
model itself. The model is instantiated only when the application calls the selected dictionary
value during benchmarking.

If the file stored `LogisticRegression(max_iter=1000)` directly, that constructor would run while
the module was imported and the same already-created estimator object would be reused. Using a
lambda avoids that: each call creates a separate fresh estimator with its own parameters and
learned state.(lambda k for number of clusters as we dont know intially)

The main benefit is correct model isolation and lazy construction, not primarily saving memory.
Scikit-learn estimators are generally lightweight before fitting, but reusing one fitted estimator
could transfer learned state between experiments. In QML Forge, each selected model is created
separately, and training one model does not transfer its fitted parameters, learned coefficients,
trees, or other state to another model.

The file does more than create dictionaries: it imports model classes, defines the factory
dictionaries, and conditionally adds XGBoost factories when the optional `xgboost` package is
available. If XGBoost is not installed, the built-in scikit-learn models remain available.
