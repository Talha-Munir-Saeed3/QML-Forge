# QML Forge: Product Requirements Document (PRD)

| | |
|---|---|
| **Product** | QML Forge |
| **Author** | Talha Munir Saeed |
| **Status** | Draft for review |
| **Repository** | https://github.com/Talha-Munir-Saeed3/QML-Forge |
| **Related docs** | [REQUIREMENTS.md](REQUIREMENTS.md) (numbered requirements), [USER_FLOW.md](USER_FLOW.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DATABASE.md](DATABASE.md), [ROADMAP.md](ROADMAP.md) |

This PRD says **what we are building and why**. `REQUIREMENTS.md` holds the detailed, numbered requirements (FR-x / NFR-x) that this document refers to.

---

## 1. Summary

QML Forge is a web app where someone uploads a CSV file, chooses how to clean and optimize the data, picks machine learning algorithms to run (or accepts a recommended set), and reads the results. Every run is saved as a version in a database, so the user can compare runs or go back to an earlier setup and try different options. Quantum machine learning models are available as an optional toggle, run on a simulator, and are always shown next to classical baselines.

## 2. Problem

- Beginners and analysts spend most of their time cleaning data and re-running the same experiments by hand.
- Trying many algorithms means writing code, and changing options means losing track of what produced which result.
- People curious about quantum machine learning have no simple, honest way to try it on their own data and see how it compares to ordinary models.

## 3. Goals and non-goals

### Goals
1. Let a non-programmer go from CSV to model results in under 5 minutes.
2. Make every experiment reproducible and recoverable: settings, seed, and metrics are saved, and nothing is overwritten.
3. Cover the main ML families (classification, regression, clustering) with a fair, side-by-side comparison.
4. Offer quantum models as an optional experiment, not as a claim of advantage.
5. Work as a strong portfolio project: clean architecture, tests, docs, and a live demo.

### Non-goals (for now)
- Real quantum hardware execution.
- Deep learning, image, text, or time-series pipelines.
- Large-scale or streaming data (files over 50 MB).
- Fully automatic AutoML; the user stays in control of choices.
- Multi-tenant cloud hosting (see Phase 4 in the roadmap).

## 4. Target users

| Persona | Description | Main need |
|---------|-------------|-----------|
| **Student / learner** (primary) | Learning ML, comfortable with spreadsheets, little coding | Try algorithms and see how options change results |
| **Analyst** | Has real business CSVs, limited ML time | Quick cleaning, a trustworthy model comparison, and exportable results |
| **QML-curious developer** | Knows ML, wants to test quantum models | A fair classical-vs-quantum benchmark on their own data |

## 5. User stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|-----------|
| US-1 | user | upload a CSV and see a preview and column summary | I understand my data before changing it |
| US-2 | user | choose cleaning options and see each step logged | I know exactly what happened to my data and can undo it |
| US-3 | user | choose optimization options (scaling, feature selection, PCA, tuning) | I can improve model quality without writing code |
| US-4 | user | select algorithms myself or use a recommended set | I control the experiment, or get a sensible default |
| US-5 | user | turn quantum models on or off | I can try them without slowing down normal runs |
| US-6 | user | see a leaderboard with metrics and charts | I can tell which model works best and by how much |
| US-7 | user | have every run saved automatically | I never lose a result |
| US-8 | user | browse older versions and compare two of them | I can see what changed and whether it helped |
| US-9 | user | revert to an older version and run it again with different options | I can branch from any earlier setup |
| US-10 | user | export results and the cleaned data | I can use them in reports or other tools |
| US-11 | user | delete a dataset and everything that depends on it | I stay in control of my data |

## 6. Features and scope

Priorities match `REQUIREMENTS.md` (M = must, S = should, C = could).

| Area | Feature | Priority | Requirements |
|------|---------|----------|--------------|
| Upload | CSV upload, preview, column profile, duplicate detection | M / S | FR-1 to FR-3 |
| Cleaning | Logged, undoable cleaning steps | M | FR-4 to FR-6 |
| Optimization | Scaling, PCA, feature selection, hyperparameter search | M / S | FR-8 to FR-11 |
| Algorithms | Manual multi-select, recommended preset, quantum toggle | M / S | FR-14 to FR-17 |
| Results | Leaderboard, charts, export, qubit sweep | M / S | FR-18 to FR-21 |
| Versions | Auto-save, history, compare, revert, delete | M / S | FR-23 to FR-29 |
| Accounts | Login and sharing | C | FR-30, FR-31 |

### Quantum behavior (decision)
- The quantum toggle is **off by default**.
- When on, quantum models train on a **sample of about 100 rows** (adjustable up to 300) and up to 8 qubits.
- The user can also run classical models on the **same sample** for a fair comparison.
- The app states clearly that quantum models are simulated and does not claim quantum advantage.

### Versioning behavior (decision)
- A version is **immutable**: only its label and notes can change afterwards.
- **Revert** loads an old version's settings back into the app; running creates a **new** version whose parent is the old one.
- The database stores cleaning **steps**, not cleaned data. Cleaned data is rebuilt from the raw file plus the steps.

## 7. Success metrics

| Metric | Target |
|--------|--------|
| Time from upload to first results (demo dataset) | Under 5 minutes for a first-time user |
| Reproducibility | Re-running a version with the same seed reproduces its metrics |
| Test coverage of `core/` | 80% or higher |
| Cleaning a 100k-row CSV | Under 5 seconds |
| Data loss bugs in version history | Zero known |
| Portfolio readiness | README with screenshots, working demo, CI passing |

## 8. Assumptions and constraints

- Runs locally first (Streamlit + SQLite); PostgreSQL is a configuration change.
- Python 3.10 to 3.12.
- Quantum models use PennyLane's simulator, which limits data size and qubit count.
- Uploaded files are stored on the local disk and are never executed or unpickled.

## 9. Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Quantum simulation is slow | Users give up waiting | Row and qubit caps, progress bar, toggle off by default |
| Quantum models score worse than classical ones | The project looks weak | Present it as an honest benchmark; this is a real finding |
| Scope grows too large | Project never ships | Build in the roadmap phases; MVP first |
| Config format changes break old versions | Revert fails | Store `schema_version` and library versions with each version |
| Messy or huge CSVs | Crashes | Size limit, encoding fallback, clear error messages |

## 10. Release plan

Follows [ROADMAP.md](ROADMAP.md):
1. **MVP:** database connected to the UI, version history, revert.
2. **v1:** optimization options, recommended preset, compare view, charts.
3. **v1.1:** Docker, report export, polish.
4. **v2:** accounts and hosted deployment.

## 11. Open questions

1. Single-user local tool first, or a hosted multi-user app from the start?
2. How long should uploaded files be kept (forever, or N days)?
3. Should "Recommended" stay rule-based, or learn from past runs?
4. Who is the main audience: learners or analysts with real data?
5. Should the project be public on GitHub from day one?
