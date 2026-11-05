# QML Forge

**Upload a CSV. Clean it. Run classical and quantum ML. Keep every version.**

QML Forge is a web workbench where anyone can drop in a CSV, pick data-cleaning and optimization
options, choose which machine learning algorithms to run (or accept a recommended set), and read the
results. Every run is saved as an immutable _version_ in a database, so you can compare versions or
revert to an earlier setup and try different options without losing anything.

Author: Talha Munir Saeed

> Working name. Alternatives considered: QubitClean, Qlarity, QML Forge, CleanQ. Rename is a
> find-and-replace on this word, so decide whenever you like.

## How it works

1. **Upload** a CSV (preview + automatic profiling).
   You can also load a public CSV URL, including direct GitHub raw-data links. URL downloads use
   the same 50 MB, encoding, delimiter, and public-host validation as local uploads.
   Kaggle datasets are available through the Website selector when Kaggle API credentials are set
   in `.env`; QML Forge accepts a Kaggle dataset page URL and requires exactly one CSV in that dataset.
2. **Clean**: choose options (missing values, duplicates, types, outliers, encoding...). Each step is logged.
3. **Optimize**: feature selection, dimensionality reduction, hyperparameter search, class balancing.
4. **Choose algorithms**: pick manually, or press _Recommended_ for a rule-based shortlist.
   Quantum models (quantum-kernel SVM, variational classifier/regressor) can be toggled on.
5. **Run and read results**: leaderboard, metrics, charts, export.
6. **Version history**: every run is stored. Compare two versions, or **revert** to an old one
   (this creates a new version that points back to its parent, so nothing is ever overwritten).

## Quick start

    git clone https://github.com/Talha-Munir-Saeed3/QML-Forge.git
    cd QML-Forge
    pip install -r requirements.txt
    streamlit run app.py

Data is stored locally in `data/` (SQLite database + uploaded files). Switch to PostgreSQL by setting
`QMLFORGE_DB_URL`.

Copy `.env.example` to `.env` for local configuration. The `.env` file is ignored by git; never put
database passwords in tracked files. The app validates CSV size (50 MB), encoding, and delimiter
before storing an upload. Quantum models are off by default, simulated, and capped at 300 sampled
rows and 8 qubits.

## Documentation

| File                                         | Contents                                                          |
| -------------------------------------------- | ----------------------------------------------------------------- |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional and non-functional requirements, scope, open questions |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, data flow, design decisions                           |
| [docs/DATABASE.md](docs/DATABASE.md)         | Schema, versioning and revert semantics                           |
| [docs/ROADMAP.md](docs/ROADMAP.md)           | Phased delivery plan                                              |

## Honest note on the quantum part

Quantum models run on a classical simulator and are best on small datasets (a few hundred rows,
up to ~8 qubits). QML Forge does not claim quantum advantage; it lets you measure, on your own data,
when a quantum model helps and when it does not.
