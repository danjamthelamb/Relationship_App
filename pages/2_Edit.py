import streamlit as st
import pandas as pd
from db import get_people_df, init_db, upsert_people, reset_drawn, reset_prev
from ui_theme import inject_theme

st.set_page_config(page_title="Edit People", page_icon="✏️", layout="centered")
inject_theme()

st.markdown(
    """
    <style>
      [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

init_db()

st.title("Edit Friends & Family")
st.caption("Edit names, switch relationship, add new rows, or delete by removing a row.")

df = get_people_df()

if df.empty:
    df = pd.DataFrame(
        [{"id": 0, "name": "", "relationship": "Friend", "drawn": 0}]
    )

edited = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "name": st.column_config.TextColumn("Name", required=True),
        "relationship": st.column_config.SelectboxColumn(
            "Relationship", options=["Friend", "Family"], required=True
        ),
        "drawn": st.column_config.CheckboxColumn(
            "Drawn", help="Internal cycle status. You can change it, but usually you shouldn’t need to."
        ),
    },
)

col1, col2 = st.columns(2)
with col1:
    if st.button("Save changes", icon=":material/save:", use_container_width=True):
        # normalize checkbox True/False -> 1/0
        edited2 = edited.copy()
        edited2["drawn"] = edited2["drawn"].astype(int)
        upsert_people(edited2)
        st.success("Saved!")
        st.rerun()

with col2:
    # st.page_link("pages/1_Home.py", label="Back to Home", icon=":material/undo:", use_container_width=True)
    if st.button("Back to Home", icon=":material/undo:", use_container_width=True):
        st.switch_page("pages/1_Home.py")

with st.expander("Reset contact cycle", expanded=False):
    st.warning("This sets selected people back to *untexted* (drawn = 0).")

    confirm = st.checkbox("I understand this will reset progress.")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Reset Friends", disabled=not confirm):
            reset_drawn("Friend"); reset_prev("Friend"); st.success("Friends reset."); st.rerun()
    with c2:
        if st.button("Reset Family", disabled=not confirm):
            reset_drawn("Family"); reset_prev("Family"); st.success("Family reset."); st.rerun()
    with c3:
        if st.button("Reset All", disabled=not confirm):
            reset_drawn(None); reset_prev(None); st.success("All reset."); st.rerun()
