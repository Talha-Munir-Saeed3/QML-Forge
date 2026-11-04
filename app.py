import numpy as np
import pandas as pd
import streamlit as st

from core.cleaning import CleaningPipeline
from core.features import build_xy, quantum_readiness
from core.classical_models import CLASSIFIERS, REGRESSORS, CLUSTERERS
from core.pipelines import classical_pipeline, quantum_pipeline
from core.evaluation import evaluate, evaluate_clustering, qubit_sweep, PRIMARY

try:
    from core.quantum_models import QUANTUM_CLASSIFIERS, QUANTUM_REGRESSORS
    HAS_Q = True
except ImportError:
    HAS_Q, QUANTUM_CLASSIFIERS, QUANTUM_REGRESSORS = False, {}, {}

st.set_page_config(page_title="QML Forge", layout="wide")
st.title("QML Forge")
st.caption("Clean a CSV, then benchmark classical and quantum models on the same data.")

tab_clean, tab_task, tab_train = st.tabs(["1 · Clean data", "2 · Define task", "3 · Train & compare"])

# ---------------------------------------------------------------- 1. CLEAN
with tab_clean:
    up = st.file_uploader("Upload CSV", type="csv")
    if up and st.session_state.get("fname") != up.name:
        st.session_state.cp = CleaningPipeline(pd.read_csv(up))
        st.session_state.fname = up.name
    cp = st.session_state.get("cp")
    if cp is None:
        st.info("Upload a CSV to begin.")
    else:
        left, right = st.columns([3, 2])
        with left:
            st.write(f"**{cp.df.shape[0]} rows × {cp.df.shape[1]} columns**")
            st.dataframe(cp.df.head(100), use_container_width=True)
            prof = pd.DataFrame({"dtype": cp.df.dtypes.astype(str),
                                 "missing": cp.df.isna().sum(),
                                 "missing_%": (cp.df.isna().mean() * 100).round(1),
                                 "unique": cp.df.nunique()})
            st.dataframe(prof, use_container_width=True)
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
            if c2.button("Undo last"):
                cp.undo()
                st.rerun()
            st.subheader("Audit log")
            st.json(cp.log)
            st.download_button("Download cleaned CSV", cp.df.to_csv(index=False), "cleaned.csv")
            st.download_button("Download cleaning log", cp.to_json(), "cleaning_log.json")

# ---------------------------------------------------------------- 2. TASK
with tab_task:
    cp = st.session_state.get("cp")
    if cp is None:
        st.info("Upload data first.")
    else:
        task = st.radio("Task", ["classification", "regression", "clustering"], horizontal=True)
        target = None
        if task != "clustering":
            target = st.selectbox("Target column", list(cp.df.columns), index=len(cp.df.columns) - 1)
        st.session_state.task, st.session_state.target = task, target
        if task == "clustering":
            X, y = pd.get_dummies(cp.df.select_dtypes(exclude=["datetime"]), dtype=float), None
        else:
            X, y = build_xy(cp.df, target, task)
        st.session_state.X, st.session_state.y = X, y
        q, notes = quantum_readiness(X, task)
        st.session_state.suggested_q = q
        st.write(f"**Feature matrix:** {X.shape[0]} rows × {X.shape[1]} features")
        st.subheader("Quantum readiness")
        for n in notes:
            st.write("• " + n)

# ---------------------------------------------------------------- 3. TRAIN
with tab_train:
    if "X" not in st.session_state:
        st.info("Define the task first.")
    else:
        X, y, task = st.session_state.X, st.session_state.y, st.session_state.task
        if task == "classification":
            classical, quantum = CLASSIFIERS, QUANTUM_CLASSIFIERS
        elif task == "regression":
            classical, quantum = REGRESSORS, QUANTUM_REGRESSORS
        else:
            classical, quantum = CLUSTERERS, {}
        picks = st.multiselect("Classical models", list(classical), default=list(classical)[:4])
        qpicks = st.multiselect("Quantum models", list(quantum)) if HAS_Q else []
        if not HAS_Q and task != "clustering":
            st.warning("Install pennylane to enable quantum models.")
        c1, c2, c3, c4 = st.columns(4)
        n_q = c1.slider("Qubits", 2, 8, min(st.session_state.suggested_q, 6))
        cv = c2.slider("CV folds", 2, 5, 3)
        cap = c3.slider("Row cap for quantum", 40, 400, 120)
        k = c4.slider("Clusters (k)", 2, 10, 3) if task == "clustering" else 3

        if st.button("Run benchmark", type="primary"):
            rows = []
            prog = st.progress(0.0)
            jobs = [(n, False) for n in picks] + [(n, True) for n in qpicks]
            for i, (name, is_q) in enumerate(jobs):
                try:
                    Xs, ys = X, y
                    if is_q and len(X) > cap:
                        idx = X.sample(cap, random_state=0).index
                        Xs, ys = X.loc[idx], y.loc[idx]
                    if task == "clustering":
                        pipe = classical_pipeline(classical[name](k))
                        res = evaluate_clustering(pipe, Xs)
                    else:
                        est = quantum[name](n_q) if is_q else classical[name]()
                        pipe = (quantum_pipeline(est, n_q, Xs.shape[1]) if is_q
                                else classical_pipeline(est))
                        res = evaluate(pipe, Xs, ys, task, cv)
                    rows.append({"model": name, "type": "quantum" if is_q else "classical",
                                 "rows_used": len(Xs), **res})
                except Exception as e:
                    rows.append({"model": name, "type": "quantum" if is_q else "classical",
                                 "error": str(e)[:120]})
                prog.progress((i + 1) / len(jobs))
            st.session_state.results = pd.DataFrame(rows)

        res = st.session_state.get("results")
        if res is not None:
            key = PRIMARY[task]
            if key in res:
                asc = False
                res = res.sort_values(key, ascending=asc, na_position="last")
            st.subheader("Leaderboard")
            st.dataframe(res, use_container_width=True)
            if key in res:
                st.bar_chart(res.set_index("model")[key])
            st.download_button("Download results CSV", res.to_csv(index=False), "results.csv")

        if HAS_Q and task == "classification":
            with st.expander("Experiment: accuracy vs number of qubits"):
                top = st.slider("Max qubits", 3, 8, 6)
                if st.button("Run qubit sweep"):
                    idx = X.sample(min(len(X), cap), random_state=0).index
                    with st.spinner("Simulating circuits..."):
                        st.line_chart(qubit_sweep(X.loc[idx], y.loc[idx], range(2, top + 1), cv))
