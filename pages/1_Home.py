import streamlit as st
from db import get_counts, init_db

st.set_page_config(page_title="Home", page_icon="🏠", layout="centered")
init_db()

st.title("Home")

counts = get_counts()

col1, col2 = st.columns(2)
with col1:
    st.metric("Friends", counts["Friend"]["total"], help="Total Friend names in your list")
    st.metric("Friends remaining", counts["Friend"]["remaining"], help="Undrawn Friends in the current cycle")
with col2:
    st.metric("Family", counts["Family"]["total"], help="Total Family names in your list")
    st.metric("Family remaining", counts["Family"]["remaining"], help="Undrawn Family in the current cycle")

st.divider()

st.subheader("What do you want to do?")

c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/3_Todays_Drawing.py", label="Draw names for today", use_container_width=True)
with c2:
    st.page_link("pages/2_Edit.py", label="Edit Friends & Family", use_container_width=True)
