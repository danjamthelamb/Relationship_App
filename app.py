import streamlit as st
from db import init_db

st.set_page_config(page_title="Who should I text?", page_icon="📩", layout="centered")
init_db()

st.title("📩 Who should I text?")
st.caption("Use the Pages sidebar to navigate.")
st.info("Open **🏠 Home** from the sidebar.")
