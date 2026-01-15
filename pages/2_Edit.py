import streamlit as st
import pandas as pd
from db import get_people_df, init_db, upsert_people

st.set_page_config(page_title="Edit People", page_icon="✏️", layout="centered")
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
    if st.button("💾 Save changes", use_container_width=True):
        # normalize checkbox True/False -> 1/0
        edited2 = edited.copy()
        edited2["drawn"] = edited2["drawn"].astype(int)
        upsert_people(edited2)
        st.success("Saved!")
        st.rerun()

with col2:
    st.page_link("pages/1_Home.py", label="⬅️ Back to Home", use_container_width=True)
