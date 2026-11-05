import streamlit as st

from core.ui import setup_page

setup_page("Home")
st.subheader("From raw table to trusted benchmark")
st.caption("A focused workspace for cleaning data, comparing models, and keeping every experiment reproducible.")
st.subheader("Start with a dataset")
cards = st.columns(4)
for column, title, body, icon in zip(
    cards,
    ["Upload", "Define", "Benchmark", "Remember"],
    ["Bring a CSV, URL, or Kaggle dataset.",
     "Choose classification, regression, or clustering.",
     "Compare classical and simulated quantum models.",
     "Every run becomes an immutable version."],
    ["01", "02", "03", "04"],
):
    with column:
        st.info(f"**{icon} · {title}**\n\n{body}")
st.write("")
st.page_link("pages/Upload_Clean.py", label="Open Upload & Clean", icon="📥")
st.markdown(
    """
Use the pages in the sidebar to work through QML Forge:

1. **Upload & Clean** — upload a CSV, load a public URL, or import a selectable CSV from Kaggle.
2. **Define Task** — choose classification, regression, or clustering.
3. **Train & Compare** — select models, configure preprocessing, and save a benchmark version.
4. **History** — inspect, compare, label, revert, or delete saved datasets and versions.
"""
)
