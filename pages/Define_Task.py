import streamlit as st

from core.config import MAX_QUBITS, QUANTUM_MAX_ROWS
from core.features import quantum_readiness
from core.ui import setup_page, task_data

setup_page("Define Task")
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
