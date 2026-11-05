import pandas as pd
import streamlit as st

from core.ui import register_dataset, setup_page
from core.upload import fetch_csv_url, fetch_kaggle_archive, parse_kaggle_csv

repo = setup_page("Upload & Clean")
upload_tab, url_tab = st.tabs(["Upload file", "Load from URL"])
dataset_input = None

upload = upload_tab.file_uploader("Upload CSV", type=["csv"])
if upload:
    dataset_input = (upload.name, upload.getvalue())

with url_tab:
    source_type = st.selectbox("Website", ["Generic public URL", "Kaggle"])
    source_url = st.text_input(
        "Dataset URL",
        placeholder=("https://www.kaggle.com/datasets/owner/dataset"
                     if source_type == "Kaggle"
                     else "https://raw.githubusercontent.com/.../data.csv"),
        help=("Kaggle uses its API credentials from .env. Generic URLs must directly return CSV content."
              if source_type == "Kaggle"
              else "Use a direct public CSV link, such as a GitHub raw URL."),
    )
    load_url = st.button("Load CSV from URL")

if load_url and source_url:
    try:
        if source_type == "Kaggle":
            archive_bytes, csv_names = fetch_kaggle_archive(source_url)
            st.session_state.kaggle_archive = archive_bytes
            st.session_state.kaggle_files = csv_names
        else:
            _, raw, filename = fetch_csv_url(source_url)
            dataset_input = (filename, raw)
    except ValueError as exc:
        st.error(str(exc))

if source_type == "Kaggle" and st.session_state.get("kaggle_files"):
    selected_file = st.selectbox("CSV file in Kaggle dataset", st.session_state.kaggle_files)
    if st.button("Load selected Kaggle CSV"):
        try:
            _, raw, filename = parse_kaggle_csv(
                st.session_state.kaggle_archive, selected_file
            )
            dataset_input = (filename, raw)
        except ValueError as exc:
            st.error(str(exc))

if dataset_input:
    filename, raw = dataset_input
    try:
        register_dataset(repo, filename, raw)
    except ValueError as exc:
        st.error(str(exc))

cp = st.session_state.get("cp")
if cp is None:
    st.info("Upload a CSV or load one from a URL to begin.")
else:
    left, right = st.columns([3, 2])
    with left:
        m1, m2, m3 = st.columns(3)
        m1.metric("Rows", f"{cp.df.shape[0]:,}")
        m2.metric("Columns", f"{cp.df.shape[1]:,}")
        m3.metric("Cleaning steps", len(cp.log))
        st.write(f"**{cp.df.shape[0]} rows × {cp.df.shape[1]} columns**")
        st.dataframe(cp.df.head(100), width="stretch")
        profile = pd.DataFrame({
            "dtype": cp.df.dtypes.astype(str),
            "missing": cp.df.isna().sum(),
            "missing_%": (cp.df.isna().mean() * 100).round(1),
            "unique": cp.df.nunique(),
        })
        st.dataframe(profile, width="stretch")
        missing = profile["missing_%"].sort_values(ascending=False)
        if missing.max() > 0:
            st.caption("Missing values by column")
            st.bar_chart(missing[missing > 0])
    with right:
        st.subheader("Cleaning steps")
        cols = list(cp.df.columns)
        num = list(cp.df.select_dtypes("number").columns)
        obj = list(cp.df.select_dtypes(exclude="number").columns)
        op = st.selectbox("Operation", [
            "standardize_columns", "strip_whitespace", "standardize_case",
            "drop_duplicates", "drop_columns", "to_numeric", "parse_dates",
            "impute", "drop_missing_rows", "clip_outliers", "encode",
        ])
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
