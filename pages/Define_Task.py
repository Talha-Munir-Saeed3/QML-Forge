import streamlit as st

from core.config import MAX_QUBITS, QUANTUM_MAX_ROWS
from core.features import quantum_readiness
from core.ui import setup_page, task_data

setup_page("Define Task")
cp = st.session_state.get("cp")
if cp is None:
    st.subheader("Your dataset comes first")
    st.info("Upload a CSV, use a public CSV URL, or select a file from Kaggle before defining the task.")
    st.page_link("pages/Upload_Clean.py", label="Go to Upload & Clean", icon="📥")
else:
    task = st.radio("Task", ["classification", "regression", "clustering"], horizontal=True)
    target = None if task == "clustering" else st.selectbox("Target column", list(cp.df.columns))
    X, y = task_data(cp, task, target)
    st.session_state.update(task=task, target=target, X=X, y=y)
    q, notes = quantum_readiness(X, task, MAX_QUBITS, QUANTUM_MAX_ROWS)
    st.session_state.suggested_q = q
    m1, m2, m3 = st.columns(3)
    m1.metric("Rows", f"{X.shape[0]:,}")
    m2.metric("Features", f"{X.shape[1]:,}")
    m3.metric("Missing values", f"{int(X.isna().sum().sum()):,}")
    st.subheader("Feature shape")
    st.bar_chart(X.dtypes.astype(str).value_counts().rename("columns"))
    st.write(f"**Feature matrix:** {X.shape[0]} rows × {X.shape[1]} features")
    for note in notes:
        st.write("• " + note)
