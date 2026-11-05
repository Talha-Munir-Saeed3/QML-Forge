import pandas as pd
import streamlit as st

from core.ui import setup_page

repo = setup_page("History")
history = repo.history(st.session_state.project_id)
if not history:
    st.info("No benchmark versions yet.")
else:
    st.dataframe(pd.DataFrame(history), use_container_width=True)
    ids = {f"v{h['version_no']} — {h.get('label') or 'unlabelled'}": h["id"] for h in history}
    selected = st.selectbox("Open version", list(ids))
    version_id = ids[selected]
    version = repo.get_version(version_id)
    st.json({k: version[k] for k in ("task", "target", "cleaning_steps",
                                     "optimization", "algorithms", "seed", "cv_folds")})
    c1, c2 = st.columns(2)
    label = c1.text_input("Label", value=version["label"] or "")
    notes = c2.text_area("Notes", value=version["notes"] or "")
    if st.button("Save label/notes"):
        repo.update_version_metadata(version_id, label, notes)
        st.rerun()
    if st.button("Revert this version"):
        repo.revert_to(version_id)
        cp = st.session_state.get("cp")
        if cp is not None:
            cp.replay(version["cleaning_steps"])
        st.success("Created a new child version and replayed its cleaning steps.")
    results = repo.results_for(version_id)
    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    compare_options = [x for x in ids if x != selected]
    if compare_options:
        compare_with = st.selectbox("Compare with", compare_options)
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
