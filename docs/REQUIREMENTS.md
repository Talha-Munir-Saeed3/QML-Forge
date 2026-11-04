# Requirements

Priority: **M** = must (MVP), **S** = should (v1), **C** = could (later).

## 1. Functional requirements

### Upload and profiling
| ID | Requirement | P |
|----|-------------|---|
| FR-1 | Upload a CSV (up to 50 MB); auto-detect delimiter and encoding; show a preview | M |
| FR-2 | Profile each column: dtype, missing %, unique count, min/max/mean, top values | M |
| FR-3 | Store the file hash (SHA-256); warn if the same dataset was uploaded before | S |

### Cleaning options
| ID | Requirement | P |
|----|-------------|---|
| FR-4 | Offer: standardize column names, trim whitespace, fix casing, drop duplicates/columns, convert to numeric/date, impute (mean/median/mode), drop missing rows, clip outliers (IQR), encode (one-hot/ordinal) | M |
| FR-5 | Preview the effect of a step before applying it | S |
| FR-6 | Undo the last step; every applied step is recorded in an ordered, replayable log | M |
| FR-7 | Suggest cleaning steps automatically (e.g. "column X is 40% missing") | C |

### Optimization options
| ID | Requirement | P |
|----|-------------|---|
| FR-8 | Scaling choice (standard, min-max, none) applied inside the model pipeline to avoid leakage | M |
| FR-9 | Feature selection: variance threshold, correlation filter, mutual information | S |
| FR-10 | Dimensionality reduction: PCA with a chosen number of components (required for quantum models) | M |
| FR-11 | Hyperparameter search: none / grid / random, with a time or trial budget | S |
| FR-12 | Class imbalance handling: class weights or resampling | C |
| FR-13 | Quantum feature selection (QAOA-style) as an experiment | C |

### Algorithm selection
| ID | Requirement | P |
|----|-------------|---|
| FR-14 | Manual multi-select across classification, regression and clustering algorithms | M |
| FR-15 | "Recommended" preset chosen by simple rules (task, rows, feature count, class balance) | S |
| FR-16 | Toggle quantum models on/off; enforce qubit and row limits with clear messages | M |
| FR-17 | Choose cross-validation folds and random seed | M |

### Results
| ID | Requirement | P |
|----|-------------|---|
| FR-18 | Leaderboard with task-appropriate metrics (accuracy/precision/recall/F1, MAE/RMSE/R2, silhouette/Davies-Bouldin) and training time | M |
| FR-19 | Charts: metric bar chart, confusion matrix, feature importance where available | S |
| FR-20 | Export results as CSV/JSON; downloadable cleaned dataset | M |
| FR-21 | Qubit sweep experiment: quantum vs classical accuracy as qubits grow | S |
| FR-22 | PDF/HTML report of a version | C |

### Versioning and persistence
| ID | Requirement | P |
|----|-------------|---|
| FR-23 | Every run creates an immutable *version* storing: dataset reference, cleaning steps, optimization settings, selected algorithms and parameters, seed, library versions | M |
| FR-24 | Store all metrics and per-model parameters in the database | M |
| FR-25 | Version history list with labels, notes, timestamps and parent links | M |
| FR-26 | **Revert**: load any older version's settings back into the UI; running it creates a *new* version whose parent is the old one | M |
| FR-27 | Compare two versions side by side (settings diff + metric diff) | S |
| FR-28 | Archive or delete a version or dataset (and its files) | S |
| FR-29 | Projects: group datasets and versions under a named project | S |

### Accounts (later)
| ID | Requirement | P |
|----|-------------|---|
| FR-30 | User sign-up/login; each user sees only their own projects | C |
| FR-31 | Share a read-only link to a version | C |

## 2. Non-functional requirements
| ID | Requirement |
|----|-------------|
| NFR-1 | **Reproducibility**: re-running a version with the same seed reproduces its metrics (within floating-point tolerance) |
| NFR-2 | **Safety**: validate uploads (extension, size, parsing); never unpickle user-supplied files; escape all displayed values |
| NFR-3 | **Performance**: cleaning a 100k-row CSV responds in under 5 s; classical benchmarks show progress; quantum runs are capped (default 120 rows, max 8 qubits) |
| NFR-4 | **Privacy**: data stays on the host; deleting a dataset removes the file and dependent rows |
| NFR-5 | **Portability**: runs on Windows, macOS, Linux; Docker image provided; SQLite default, PostgreSQL supported |
| NFR-6 | **Testability**: core logic (cleaning, evaluation, repository) is UI-independent, with at least 80% test coverage |
| NFR-7 | **Usability**: a first-time user can go from upload to results in under 5 minutes with no code |
| NFR-8 | **Honesty**: the UI states that quantum models are simulated and shows classical baselines next to them |

## 3. Out of scope (for now)
Real quantum hardware execution, deep learning/image/text data, streaming data, AutoML-level pipeline search, multi-tenant cloud hosting.

## 4. Open questions
1. Single-user local tool first, or multi-user web app from the start?
2. Should uploaded CSVs be kept on disk indefinitely, or deleted after N days?
3. Should "Recommended" be strictly rule-based, or also learn from past runs?
4. Is the target audience students/learners, or analysts with real business data?
