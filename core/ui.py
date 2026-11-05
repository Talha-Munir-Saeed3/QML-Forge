import hashlib

import pandas as pd
import streamlit as st

from .classical_models import CLASSIFIERS, CLUSTERERS, REGRESSORS
from .cleaning import CleaningPipeline
from .config import DATA_DIR
from .db import Repository
from .features import build_xy
from .upload import parse_csv_bytes

try:
    from .quantum_models import QUANTUM_CLASSIFIERS, QUANTUM_REGRESSORS
except ImportError:
    QUANTUM_CLASSIFIERS, QUANTUM_REGRESSORS = {}, {}


def repository():
    return Repository(data_dir=DATA_DIR)


def setup_page(title):
    st.set_page_config(page_title=f"QML Forge · {title}", layout="wide")
    repo = repository()
    ensure_project(repo)
    project_sidebar(repo)
    st.title(title)
    return repo


def ensure_project(repo):
    if "project_id" not in st.session_state:
        projects = repo.projects()
        st.session_state.project_id = (
            projects[0]["id"] if projects else repo.create_project("Default project")
        )


def project_sidebar(repo):
    with st.sidebar:
        projects = repo.projects()
        project_names = {p["name"]: p["id"] for p in projects}
        current_name = next(
            (name for name, pid in project_names.items()
             if pid == st.session_state.project_id),
            next(iter(project_names)),
        )
        chosen = st.selectbox(
            "Project", list(project_names),
            index=list(project_names).index(current_name),
        )
        st.session_state.project_id = project_names[chosen]
        new_project = st.text_input("New project name")
        if st.button("Create project") and new_project.strip():
            st.session_state.project_id = repo.create_project(new_project.strip())
            st.rerun()


def register_dataset(repo, filename, raw):
    digest = hashlib.sha256(raw).hexdigest()
    if st.session_state.get("upload_digest") == digest:
        return
    frame, raw = parse_csv_bytes(raw)
    existing = {d["sha256"] for d in repo.datasets(st.session_state.project_id)}
    dataset_id = repo.add_dataset(
        st.session_state.project_id, filename, raw, len(frame), len(frame.columns)
    )
    if digest in existing:
        st.warning("This dataset is already uploaded to the selected project; using the existing dataset.")
    st.session_state.update(
        upload_digest=digest, dataset_id=dataset_id, raw_df=frame, fname=filename,
        cp=CleaningPipeline(frame),
    )


def task_data(cp, task, target):
    if task == "clustering":
        return pd.get_dummies(cp.df.select_dtypes(exclude=["datetime"]), dtype=float), None
    return build_xy(cp.df, target, task)


def models_for(task, use_quantum):
    classical = {"classification": CLASSIFIERS, "regression": REGRESSORS,
                 "clustering": CLUSTERERS}[task]
    quantum = (
        QUANTUM_CLASSIFIERS if task == "classification" else QUANTUM_REGRESSORS
        if task == "regression" else {}
    ) if use_quantum else {}
    return classical, quantum
