import numpy as np
import pandas as pd
import streamlit as st

from core.config import DEFAULT_SEED, MAX_QUBITS, QUANTUM_DEFAULT_ROWS, QUANTUM_MAX_ROWS
from core.evaluation import (PRIMARY, evaluate, evaluate_clustering, qubit_sweep,
                              sample_for_quantum)
from core.optimization import hyperparameter_search
from core.pipelines import classical_pipeline, quantum_pipeline
from core.recommend import recommend
from core.ui import models_for, setup_page

repo = setup_page("Train & Compare")
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
    n_q = st.slider("Qubits", 2, MAX_QUBITS,
                    min(st.session_state.get("suggested_q", 2), MAX_QUBITS))
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
        rows = []
        for name, is_q in jobs:
            try:
                current_X, current_y = ((run_X, run_y) if is_q or (use_quantum and same_sample)
                                        else (X, y))
                est = quantum[name](n_q) if is_q else (
                    classical[name](3) if task == "clustering" else classical[name]())
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
        st.subheader("Leaderboard")
        st.dataframe(results.sort_values(key, ascending=False, na_position="last")
                     if key in results else results, width="stretch")
        if key in results:
            chart_data = results[["model", key]].dropna().set_index("model")
            if not chart_data.empty:
                st.subheader(f"{key.replace('_', ' ').title()} comparison")
                st.bar_chart(chart_data)
        if "confusion_matrix" in results:
            st.caption("Confusion matrices are available per classification model in the result details.")
    if use_quantum and task == "classification" and qpicked:
        with st.expander("Experiment: accuracy vs number of qubits"):
            top = st.slider("Maximum sweep qubits", 2, MAX_QUBITS, min(MAX_QUBITS, n_q + 2))
            if st.button("Run qubit sweep"):
                sweep_X, sweep_y = sample_for_quantum(X, y, cap, task, DEFAULT_SEED)
                with st.spinner("Simulating circuits..."):
                    st.dataframe(qubit_sweep(sweep_X, sweep_y, range(2, top + 1), cv),
                                 width="stretch")
