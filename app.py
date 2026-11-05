import streamlit as st

from core.ui import setup_page

setup_page("Home")
st.caption("Clean a CSV, benchmark reproducible classical models, and optionally simulate quantum models.")
st.markdown(
    """
Use the pages in the sidebar to work through QML Forge:

1. **Upload & Clean** — upload a CSV, load a public URL, or import a selectable CSV from Kaggle.
2. **Define Task** — choose classification, regression, or clustering.
3. **Train & Compare** — select models, configure preprocessing, and save a benchmark version.
4. **History** — inspect, compare, label, revert, or delete saved datasets and versions.
"""
)
