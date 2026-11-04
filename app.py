import hashlib

import numpy as np
import pandas as pd
import streamlit as st

from core.classical_models import CLASSIFIERS, REGRESSORS, CLUSTERERS
from core.cleaning import CleaningPipeline
from core.config import (DATA_DIR, DEFAULT_SEED, MAX_QUBITS,
                         QUANTUM_DEFAULT_ROWS, QUANTUM_MAX_ROWS)
from core.db import Repository
from core.evaluation import evaluate, evaluate_clustering, qubit_sweep, sample_for_quantum, PRIMARY
from core.features import build_xy, quantum_readiness
from core.pipelines import classical_pipeline, quantum_pipeline
from core.optimization import hyperparameter_search
from core.recommend import recommend
from core.upload import fetch_csv_url, parse_csv_bytes

try:
    from core.quantum_models import QUANTUM_CLASSIFIERS, QUANTUM_REGRESSORS
except ImportError:
    QUANTUM_CLASSIFIERS, QUANTUM_REGRESSORS = {}, {}

st.set_page_config(page_title="QML Forge", layout="wide")
repo = Repository(data_dir=DATA_DIR)
st.title("QML Forge")
st.caption("Clean a CSV, benchmark reproducible classical models, and optionally simulate quantum models.")


def task_data(cp, task, target):
    if task == "clustering":
        return pd.get_dummies(cp.df.select_dtypes(exclude=["datetime"]), dtype=float), None
    return build_xy(cp.df, target, task)


def models_for(task, use_quantum):
    classical = {"classification": CLASSIFIERS, "regression": REGRESSORS,
                 "clustering": CLUSTERERS}[task]
    quantum = (QUANTUM_CLASSIFIERS if task == "classification" else QUANTUM_REGRESSORS
               if task == "regression" else {}) if use_quantum else {}
    return classical, quantum


if "project_id" not in st.session_state:
    projects = repo.projects()
    st.session_state.project_id = projects[0]["id"] if projects else repo.create_project("Default project")

with st.sidebar:
    projects = repo.projects()
    project_names = {p["name"]: p["id"] for p in projects}
    current_name = next((name for name, pid in project_names.items()
                         if pid == st.session_state.project_id), projects[0]["name"])
    chosen = st.selectbox("Project", list(project_names), index=list(project_names).index(current_name))
    st.session_state.project_id = project_names[chosen]
    new_project = st.text_input("New project name")
    if st.button("Create project") and new_project.strip():
        st.session_state.project_id = repo.create_project(new_project.strip())
        st.rerun()

tab_clean, tab_task, tab_train, tab_history = st.tabs(
    ["1 · Clean data", "2 · Define task", "3 · Train & compare", "4 · History"])

with tab_clean:
    upload_tab, url_tab = st.tabs(["Upload file", "Load from URL"])
    upload = upload_tab.file_uploader("Upload CSV", type=["csv"])
    dataset_input = None
    if upload:
        dataset_input = (upload.name, upload.getvalue())
    with url_tab:
        source_url = st.text_input(
            "Public CSV URL",
            placeholder="https://raw.githubusercontent.com/.../data.csv",
            help="Use a direct public CSV link, such as a GitHub raw URL. The URL must use HTTP(S).",
        )
        load_url = st.button("Load CSV from URL")
    if load_url and source_url:
        try:
            frame, raw, filename = fetch_csv_url(source_url)
            dataset_input = (filename, raw)
        except ValueError as exc:
            st.error(str(exc))
    if dataset_input:
        filename, raw = dataset_input
        digest = hashlib.sha256(raw).hexdigest()
        if st.session_state.get("upload_digest") != digest:
            try:
                frame, raw = parse_csv_bytes(raw)
                existing = {d["sha256"] for d in repo.datasets(st.session_state.project_id)}
                dataset_id = repo.add_dataset(st.session_state.project_id, filename, raw,
                                              len(frame), len(frame.columns))
                if digest in existing:
                    st.warning("This dataset is already uploaded to the selected project; using the existing dataset.")
                st.session_state.update(upload_digest=digest, dataset_id=dataset_id,
                                        raw_df=frame, fname=filename)
                st.session_state.cp = CleaningPipeline(frame)
            except ValueError as exc:
                st.error(str(exc))
    cp = st.session_state.get("cp")
    if cp is None:
        st.info("Upload a CSV to begin.")
    else:
        left, right = st.columns([3, 2])
        with left:
            st.write(f"**{cp.df.shape[0]} rows × {cp.df.shape[1]} columns**")
            st.dataframe(cp.df.head(100), use_container_width=True)
            st.dataframe(pd.DataFrame({"dtype": cp.df.dtypes.astype(str),
                                       "missing": cp.df.isna().sum(),
                                       "missing_%": (cp.df.isna().mean() * 100).round(1),
                                       "unique": cp.df.nunique()}), use_container_width=True)
        with right:
            st.subheader("Cleaning steps")
            cols = list(cp.df.columns)
            num = list(cp.df.select_dtypes("number").columns)
            obj = list(cp.df.select_dtypes(exclude="number").columns)
            op = st.selectbox("Operation", [
                "standardize_columns", "strip_whitespace", "standardize_case", "drop_duplicates",
                "drop_columns", "to_numeric", "parse_dates", "impute", "drop_missing_rows",
                "clip_outliers", "encode"])
            params = {}
            if op == "standardize_case":
                params = {"cols": st.multiselect("Columns", obj),
                          "case": st.selectbox("Case", ["lower", "upper", "title"])}
            elif op in ("drop_columns", "to_numeric", "parse_dates", "drop_missing_rows"):
                params = {"cols": st.multiselect("Columns", cols)}
            elif op == "impute":
                params = {"cols": st.multiselect("Columns", cols),
                          "strategy": st.selectbox("Strategy", ["median", "mean", "mode"])}
            elif op == "clip_outliers":
                params = {"cols": st.multiselect("Numeric columns", num),
                          "k": st.slider("IQR multiplier", 1.0, 3.0, 1.5, 0.1)}
            elif op == "encode":
                params = {"cols": st.multiselect("Columns", obj),
                          "method": st.selectbox("Method", ["one_hot", "ordinal"])}
            c1, c2 = st.columns(2)
            if c1.button("Apply", type="primary"):
                cp.apply(op, **params)
                st.rerun()
            if c2.button("Undo last") and cp.log:
                cp.undo()
                st.rerun()
            st.json(cp.log)
            st.download_button("Download cleaned CSV", cp.df.to_csv(index=False), "cleaned.csv")

with tab_task:
    cp = st.session_state.get("cp")
    if cp is None:
        st.info("Upload data first.")
    else:
        task = st.radio("Task", ["classification", "regression", "clustering"], horizontal=True)
        target = None if task == "clustering" else st.selectbox("Target column", list(cp.df.columns))
        X, y = task_data(cp, task, target)
        st.session_state.update(task=task, target=target, X=X, y=y)
        q, notes = quantum_readiness(X, task, MAX_QUBITS, QUANTUM_MAX_ROWS)
        st.session_state.suggested_q = q
        st.write(f"**Feature matrix:** {X.shape[0]} rows × {X.shape[1]} features")
        for note in notes:
            st.write("• " + note)

with tab_train:
    if "X" not in st.session_state:
        st.info("Define the task first.")
    else:
        X, y, task = st.session_state.X, st.session_state.y, st.session_state.task
        use_quantum = st.checkbox("Use quantum models", value=False)
        if use_quantum:
            st.info("Quantum models are simulated classically and trained on a capped sample; this does not claim quantum advantage.")
        classical, quantum = models_for(task, use_quantum)
        default_picks = st.session_state.pop("recommended", list(classical)[:4])
        picked = st.multiselect("Classical models", list(classical),
                                default=[n for n in default_picks if n in classical],
                                key="classical_picks")
        qpicked = st.multiselect("Quantum models", list(quantum),
                                 default=[n for n in default_picks if n in quantum],
                                 key="quantum_picks")
        if st.button("Use recommended"):
            rec = recommend(task, len(X), X.shape[1],
                            np.bincount(y) / len(y) if y is not None and task == "classification" else None,
                            float(X.isna().mean().mean()), 0)
            st.session_state.recommended = [r["name"] for r in rec
                                            if r["name"] in classical or r["name"] in quantum]
            st.rerun()
        if st.session_state.get("recommended"):
            st.caption("Recommended: " + ", ".join(st.session_state.recommended))
        n_q = st.slider("Qubits", 2, MAX_QUBITS, min(st.session_state.get("suggested_q", 2), MAX_QUBITS))
        cv = st.slider("CV folds", 2, 5, 3)
        cap = st.slider("Quantum sample rows", 20, QUANTUM_MAX_ROWS, QUANTUM_DEFAULT_ROWS)
        same_sample = st.checkbox("Also run classical models on the same sample", value=True) if use_quantum else False
        scaler = st.selectbox("Scaler", ["standard", "minmax", "none"])
        pca = st.number_input("PCA components (0 = automatic)", min_value=0, value=0)
        search_mode = st.selectbox("Hyperparameter search", ["none", "grid", "random"])
        search_budget = st.number_input("Random search iterations", 1, 30, 8)
        optimization = {"scaler": scaler, "pca_components": pca or None,
                        "feature_selection": "none", "search": search_mode,
                        "n_iter": search_budget}
        if st.button("Run benchmark", type="primary"):
            run_X, run_y = sample_for_quantum(X, y, cap, task, DEFAULT_SEED) if use_quantum else (X, y)
            jobs = [(n, False) for n in picked] + [(n, True) for n in qpicked]
            if use_quantum and same_sample:
                jobs = [(n, False) for n in picked] + [(n, True) for n in qpicked]
            rows = []
            for name, is_q in jobs:
                try:
                    current_X, current_y = ((run_X, run_y) if is_q or (use_quantum and same_sample)
                                            else (X, y))
                    est = quantum[name](n_q) if is_q else classical[name](3) if task == "clustering" else classical[name]()
                    pipe = (quantum_pipeline(est, n_q, current_X.shape[1], optimization, task)
                            if is_q else classical_pipeline(est, optimization, task))
                    if not is_q and task != "clustering":
                        pipe = hyperparameter_search(pipe, search_mode, search_budget, cv, DEFAULT_SEED)
                    result = (evaluate_clustering(pipe, current_X) if task == "clustering"
                              else evaluate(pipe, current_X, current_y, task, cv, DEFAULT_SEED))
                    rows.append({"model": name, "type": "quantum" if is_q else "classical",
                                 "rows_used": len(current_X), **result})
                except Exception as exc:
                    rows.append({"model": name, "type": "quantum" if is_q else "classical",
                                 "rows_used": len(run_X), "error": str(exc)[:300]})
            results = pd.DataFrame(rows)
            st.session_state.results = results
            algorithms = [{"name": n, "quantum": q} for n, q in jobs]
            version_id = repo.save_version(st.session_state.project_id, st.session_state.dataset_id,
                task, st.session_state.target, st.session_state.cp.log, optimization,
                algorithms, DEFAULT_SEED, cv)
            repo.record_run(version_id, results.to_dict("records"), len(run_X))
            st.success(f"Saved immutable version {version_id}.")
        results = st.session_state.get("results")
        if results is not None:
            key = PRIMARY[task]
            st.dataframe(results.sort_values(key, ascending=False, na_position="last")
                         if key in results else results, use_container_width=True)
        if use_quantum and task == "classification" and qpicked:
            with st.expander("Experiment: accuracy vs number of qubits"):
                top = st.slider("Maximum sweep qubits", 2, MAX_QUBITS, min(MAX_QUBITS, n_q + 2))
                if st.button("Run qubit sweep"):
                    sweep_X, sweep_y = sample_for_quantum(X, y, cap, task, DEFAULT_SEED)
                    with st.spinner("Simulating circuits..."):
                        st.dataframe(qubit_sweep(sweep_X, sweep_y, range(2, top + 1), cv),
                                     use_container_width=True)

with tab_history:
    history = repo.history(st.session_state.project_id)
    if not history:
        st.info("No benchmark versions yet.")
    else:
        st.dataframe(pd.DataFrame(history), use_container_width=True)
        ids = {f"v{h['version_no']} — {h.get('label') or 'unlabelled'}": h["id"] for h in history}
        selected = st.selectbox("Open version", list(ids))
        version_id = ids[selected]
        version = repo.get_version(version_id)
        st.json({k: version[k] for k in ("task", "target", "cleaning_steps", "optimization", "algorithms", "seed", "cv_folds")})
        c1, c2 = st.columns(2)
        label = c1.text_input("Label", value=version["label"] or "")
        notes = c2.text_area("Notes", value=version["notes"] or "")
        if st.button("Save label/notes"):
            repo.update_version_metadata(version_id, label, notes)
            st.rerun()
        if st.button("Revert this version"):
            repo.revert_to(version_id)
            st.session_state.cp.replay(version["cleaning_steps"])
            st.success("Created a new child version and replayed its cleaning steps.")
        results = repo.results_for(version_id)
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        compare_with = st.selectbox("Compare with", [x for x in ids if x != selected])
        if st.button("Compare versions"):
            comparison = repo.compare(version_id, ids[compare_with])
            st.json(comparison["settings_diff"])
            left = pd.DataFrame(comparison["models_a"].values()).add_prefix("a_")
            right = pd.DataFrame(comparison["models_b"].values()).add_prefix("b_")
            st.dataframe(pd.concat([left.reset_index(drop=True), right.reset_index(drop=True)],
                                   axis=1), use_container_width=True)
        if st.checkbox("I understand deletion removes this dataset and its versions") and st.button("Delete dataset"):
            repo.delete_dataset(version["dataset_id"])
            st.session_state.clear()
            st.rerun()
