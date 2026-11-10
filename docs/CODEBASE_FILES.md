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

## `core/cleaning.py`

This file contains the current replayable data-cleaning operations and the
`CleaningPipeline` class.

### The `OPS` registry

`OPS` is a dictionary that maps an operation's string name to the corresponding Python function:

```python
OPS = {
    "strip_whitespace": strip_whitespace,
    "impute": impute,
}
```

The actual file builds this dictionary from the function objects automatically. When the
application receives a saved step such as:

```python
{"op": "strip_whitespace", "params": {}}
```

it looks up `OPS["strip_whitespace"]` and calls the returned function. This allows cleaning steps
to be selected dynamically and replayed from their names rather than writing a separate `if`
statement for every operation.

`OPS` does not create the JSON file. It is the runtime lookup registry. The `CleaningPipeline`
stores operation names and parameters in `log`, and `to_json()` serializes that log into JSON.
The JSON contains the recipe for the cleaning process, not the DataFrame itself.

### Current cleaning operations

Each operation receives a DataFrame and returns a cleaned copy. Examples below show the intended
effect.

#### `standardize_columns`

Converts column names to lowercase `snake_case`:

```python
df = pd.DataFrame(columns=["First Name", "Annual Salary ($)"])
cleaned = standardize_columns(df)
# columns: ["first_name", "annual_salary"]
```

#### `strip_whitespace`

Removes leading and trailing whitespace from object/string columns:

```python
df = pd.DataFrame({"name": [" Alice ", "Bob  "]})
cleaned = strip_whitespace(df)
# name: ["Alice", "Bob"]
```

#### `standardize_case`

Changes selected text columns to lowercase, uppercase, or title case:

```python
df = pd.DataFrame({"city": ["new york", "LONDON"]})
cleaned = standardize_case(df, ["city"], case="title")
# city: ["New York", "London"]
```

#### `drop_duplicates`

Removes repeated rows and resets the index:

```python
df = pd.DataFrame({"id": [1, 1, 2], "score": [10, 10, 20]})
cleaned = drop_duplicates(df)
# rows: (1, 10), (2, 20)
```

#### `drop_columns`

Deletes selected columns:

```python
df = pd.DataFrame({"name": ["A"], "temporary_flag": [True]})
cleaned = drop_columns(df, ["temporary_flag"])
# columns: ["name"]
```

#### `to_numeric`

Removes non-numeric characters such as currency symbols and commas, then converts values:

```python
df = pd.DataFrame({"price": ["$1,200.50", "$30.00"]})
cleaned = to_numeric(df, ["price"])
# price: [1200.50, 30.00]
```

Values that cannot be converted become missing values (`NaN`).

#### `parse_dates`

Converts selected columns to pandas datetime values:

```python
df = pd.DataFrame({"created": ["2026-01-15", "not a date"]})
cleaned = parse_dates(df, ["created"])
# created: [Timestamp("2026-01-15"), NaT]
```

#### `impute`

Fills missing values using the mean, median, or first mode:

```python
df = pd.DataFrame({"age": [20, None, 40]})
cleaned = impute(df, ["age"], strategy="median")
# age: [20, 30, 40]
```

#### `drop_missing_rows`

Removes rows missing values in selected columns:

```python
df = pd.DataFrame({"name": ["A", "B"], "score": [10, None]})
cleaned = drop_missing_rows(df, ["score"])
# remaining row: ("A", 10)
```

#### `clip_outliers`

Caps numeric values to the IQR bounds:

```python
df = pd.DataFrame({"score": [10, 11, 12, 13, 100]})
cleaned = clip_outliers(df, ["score"], k=1.5)
# the extreme value is capped instead of deleting its row
```

The bounds are calculated as `Q1 - k * IQR` and `Q3 + k * IQR`, where
`IQR = Q3 - Q1`.

#### `encode`

Converts categorical columns to numeric values:

```python
df = pd.DataFrame({"color": ["red", "blue", "red"]})
one_hot = encode(df, ["color"], method="one_hot")
# creates columns such as color_blue and color_red

ordinal = encode(df, ["color"], method="ordinal")
# replaces categories with category codes
```

The current implementation has 11 operations:
`standardize_columns`, `strip_whitespace`, `standardize_case`, `drop_duplicates`,
`drop_columns`, `to_numeric`, `parse_dates`, `impute`, `drop_missing_rows`,
`clip_outliers`, and `encode`.

### `CleaningPipeline`

`CleaningPipeline` tracks the original DataFrame, the current working DataFrame, and the audit
log:

```python
pipeline = CleaningPipeline(original_df)
pipeline.apply("strip_whitespace")
pipeline.apply("impute", cols=["age"], strategy="median")
```

- `original` is a protected copy used as the replay starting point.
- `df` is the current working copy shown to the user and passed to task preparation.
- `log` records every operation and its parameters.
- `apply()` looks up the operation in `OPS`, applies it to the current working DataFrame, and
  appends the step to the audit log.
- `undo()` removes the last log entry, then replays the remaining steps from a fresh copy of the
  original DataFrame.
- `replay()` applies a supplied sequence of logged steps from the original, or from an optional
  starting DataFrame.
- `to_json()` exports the ordered operation recipe:

```json
[
  { "op": "strip_whitespace", "params": {} },
  { "op": "impute", "params": { "cols": ["age"], "strategy": "median" } }
]
```

Cleaning never intentionally mutates the original stored dataset. The downloadable cleaned CSV
is generated from the current working copy; machine learning uses that working copy in memory.

## Future cleaning milestone: additional operations and research

The following items are proposed for a future cleaning milestone. They are documented for
planning and research; they are not currently registered in `OPS` or exposed in the UI.

### `standardize_date_format`

Parse date columns and convert them to a consistent representation such as `YYYY-MM-DD`.
Research should decide whether the operation should preserve datetime values for modeling or
export strings only.

Reference implementation:

```python
def standardize_date_format(df, cols, date_format="%Y-%m-%d"):
    out = df.copy()
    for c in cols:
        # Convert to datetime objects first, then format as unified strings
        dt_series = pd.to_datetime(out[c], errors="coerce")
        out[c] = dt_series.dt.strftime(date_format)
    return out
```

### `parse_key_value_string`

Parse values such as `"age:25; role:admin"` and expand them into separate columns.

Reference implementation:

```python
def parse_key_value_string(df, col, pair_sep=";", kv_sep=":", drop_original=False):
    out = df.copy()

    def parse_cell(val):
        if pd.isna(val) or not isinstance(val, str):
            return {}
        pairs = val.split(pair_sep)
        kv_dict = {}
        for pair in pairs:
            if kv_sep in pair:
                k, v = pair.split(kv_sep, 1)
                kv_dict[k.strip()] = v.strip()
        return kv_dict

    # Expand extracted dictionaries into a new DataFrame block
    extracted_df = out[col].apply(parse_cell).apply(pd.Series)

    # Merge extracted columns back into main DataFrame
    out = pd.concat([out, extracted_df], axis=1)

    if drop_original:
        out = out.drop(columns=[col])

    return out
```

Research questions:

- **Performance:** `.apply(pd.Series)` iterates in Python and can become slow for 100k+ rows.
  Benchmark it against vectorized `str.extractall()` and parsing valid JSON with pandas or
  `pyarrow`.
- **Schema consistency:** decide between a predefined set of expected keys and dynamic key
  discovery. Missing keys should become clean `NaN` values without unnecessarily converting
  numeric columns to generic object dtype.
- **Type inference:** evaluate automatic conversion of extracted strings into numbers and booleans.

### Additional proposed operations

**`drop_outliers_zscore`**: remove rows whose numeric values exceed a configurable number of
standard deviations, such as `+/- 3`.

```python
def drop_outliers_zscore(df, cols, threshold=3.0):
    out = df.copy()
    for c in cols:
        mean = out[c].mean()
        std = out[c].std()
        if std > 0:
            z_scores = (out[c] - mean) / std
            out = out[z_scores.abs() <= threshold]
    return out.reset_index(drop=True)
```

**`scale_features`**: apply Min-Max scaling or standardization to selected numeric columns.
This may overlap with the existing leakage-safe model pipeline, so its placement must be
decided carefully.

```python
def scale_features(df, cols, method="minmax"):
    out = df.copy()
    for c in cols:
        if method == "minmax":
            minimum, maximum = out[c].min(), out[c].max()
            if maximum > minimum:
                out[c] = (out[c] - minimum) / (maximum - minimum)
        elif method == "standard":
            mean, std = out[c].mean(), out[c].std()
            if std > 0:
                out[c] = (out[c] - mean) / std
    return out
```

**`clean_text_regex`**: remove HTML, special characters, or custom unwanted patterns from text
columns using a regular expression.

```python
def clean_text_regex(df, cols, pattern=r"[^a-zA-Z0-9\s]", replacement=""):
    out = df.copy()
    for c in cols:
        out[c] = out[c].astype(str).str.replace(
            pattern, replacement, regex=True
        ).str.strip()
    return out
```

**`collapse_rare_categories`**: replace categories below a frequency threshold with `"Other"` to
limit high-cardinality one-hot encoding.

```python
def collapse_rare_categories(df, cols, threshold=0.05, fill_value="Other"):
    out = df.copy()
    for c in cols:
        frequencies = out[c].value_counts(normalize=True)
        rare_labels = frequencies[frequencies < threshold].index
        out[c] = out[c].replace(rare_labels, fill_value)
    return out
```

**`bin_numeric`**: convert a continuous column into configured intervals, such as age ranges.

```python
def bin_numeric(df, col, bins, labels=None, new_col_name=None):
    out = df.copy()
    target_col = new_col_name or f"{col}_binned"
    out[target_col] = pd.cut(out[col], bins=bins, labels=labels)
    return out
```

**`extract_date_features`**: derive year, month, day, day-of-week, and weekend indicators from
datetime columns.

```python
def extract_date_features(df, cols, drop_original=False):
    out = df.copy()
    for c in cols:
        dt_col = pd.to_datetime(out[c], errors="coerce")
        out[f"{c}_year"] = dt_col.dt.year
        out[f"{c}_month"] = dt_col.dt.month
        out[f"{c}_day"] = dt_col.dt.day
        out[f"{c}_dayofweek"] = dt_col.dt.dayofweek
        out[f"{c}_is_weekend"] = dt_col.dt.dayofweek.isin([5, 6]).astype(int)
        if drop_original:
            out = out.drop(columns=[c])
    return out
```

**`rename_columns`**: rename columns using an explicit mapping such as
`{"old_name": "new_name"}`.

```python
def rename_columns(df, mapping):
    return df.rename(columns=mapping)
```

The above section was created for readbility purposes and the below section is for much eaiser implmentation purposes.
Example reference implementations for the proposed operations:

```python
def drop_outliers_zscore(df, cols, threshold=3.0):
    out = df.copy()
    for c in cols:
        mean = out[c].mean()
        std = out[c].std()
        if std > 0:
            z_scores = (out[c] - mean) / std
            out = out[z_scores.abs() <= threshold]
    return out.reset_index(drop=True)


def scale_features(df, cols, method="minmax"):
    out = df.copy()
    for c in cols:
        if method == "minmax":
            minimum, maximum = out[c].min(), out[c].max()
            if maximum > minimum:
                out[c] = (out[c] - minimum) / (maximum - minimum)
        elif method == "standard":
            mean, std = out[c].mean(), out[c].std()
            if std > 0:
                out[c] = (out[c] - mean) / std
    return out


def clean_text_regex(df, cols, pattern=r"[^a-zA-Z0-9\s]", replacement=""):
    out = df.copy()
    for c in cols:
        out[c] = out[c].astype(str).str.replace(
            pattern, replacement, regex=True
        ).str.strip()
    return out


def collapse_rare_categories(df, cols, threshold=0.05, fill_value="Other"):
    out = df.copy()
    for c in cols:
        frequencies = out[c].value_counts(normalize=True)
        rare_labels = frequencies[frequencies < threshold].index
        out[c] = out[c].replace(rare_labels, fill_value)
    return out


def bin_numeric(df, col, bins, labels=None, new_col_name=None):
    out = df.copy()
    target_col = new_col_name or f"{col}_binned"
    out[target_col] = pd.cut(out[col], bins=bins, labels=labels)
    return out


def extract_date_features(df, cols, drop_original=False):
    out = df.copy()
    for c in cols:
        dt_col = pd.to_datetime(out[c], errors="coerce")
        out[f"{c}_year"] = dt_col.dt.year
        out[f"{c}_month"] = dt_col.dt.month
        out[f"{c}_day"] = dt_col.dt.day
        out[f"{c}_dayofweek"] = dt_col.dt.dayofweek
        out[f"{c}_is_weekend"] = dt_col.dt.dayofweek.isin([5, 6]).astype(int)
        if drop_original:
            out = out.drop(columns=[c])
    return out


def rename_columns(df, mapping):
    return df.rename(columns=mapping)
```

Before adding these operations, each should receive tests for normal input, missing values,
invalid parameters, mixed data types, and replay/undo behavior. Operations that learn statistics
from data, especially scaling and outlier detection, should also be reviewed for cross-validation
leakage before becoming part of the persisted cleaning recipe.

## `core/config.py`

This file centralizes environment loading and application-wide configuration values. Other modules
import these constants instead of repeating limits throughout the codebase.

### Finding the project root

The module defines:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
```

The expression works from the location of `config.py`, not from the directory where the user
happens to start Streamlit or Python:

1. `__file__` is the path of the currently executing `config.py` file.
2. `Path(__file__)` turns that path into a `pathlib.Path` object.
3. `.resolve()` converts it to an absolute, normalized path and removes relative path shortcuts
   such as `.` and `..`.
4. The first `.parent` moves from `core/config.py` to the `core/` directory.
5. The second `.parent` moves from `core/` to the repository root, `QML-Forge/`.

This lets the application reliably look for `.env` at the repository root even when it is started
from another working directory.

### Loading `.env`

When `core.config` is imported, `_load_local_env()` runs automatically. It:

- checks whether the repository-root `.env` file exists;
- reads it as UTF-8 text;
- processes it line by line;
- ignores blank lines and lines beginning with `#`;
- splits each remaining assignment at the first `=`;
- removes surrounding single or double quotes from the value; and
- adds the value to `os.environ` with `os.environ.setdefault()`.

`setdefault()` means an environment variable that was already supplied by the operating system
is preserved. This allows deployment configuration or a shell variable to take precedence over a
local `.env` value. The `.env` file is local configuration and must not be committed because it
may contain database or API credentials.

### Global limits and defaults

The module defines these shared settings:

```python
MAX_UPLOAD_MB = 50
QUANTUM_DEFAULT_ROWS = 100
QUANTUM_MAX_ROWS = 300
MAX_QUBITS = 8
DEFAULT_SEED = 0
```

- `MAX_UPLOAD_MB`: maximum accepted CSV size for upload and URL/Kaggle CSV parsing.
- `QUANTUM_DEFAULT_ROWS`: initial number of rows suggested for a quantum experiment.
- `QUANTUM_MAX_ROWS`: largest quantum sample the UI allows.
- `MAX_QUBITS`: maximum number of simulated quantum wires/qubits allowed by the UI and readiness
  guidance.
- `DEFAULT_SEED`: default random seed used for reproducible sampling and model experiments.

It also defines:

```python
DATA_DIR = Path(os.getenv("QMLFORGE_DATA_DIR", "data"))
```

`QMLFORGE_DATA_DIR` can override the default `data/` directory. This directory is used for
application data such as uploaded CSV files and the default SQLite database.
