import streamlit as st
from db import get_counts, init_db
from ui_theme import inject_theme

image_path = "assets/logo_icon.png"
favicon_path = "assets/favicon.png"

st.set_page_config(page_title="Home", page_icon=favicon_path, layout="centered")
inject_theme()
init_db()

# --- tighten global vertical spacing a bit (tasteful) ---
st.markdown(
    """
<style>
/* Reduce top padding so things feel less floaty */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Slightly tighten divider spacing */
hr {
    margin-top: 1.25rem;
    margin-bottom: 1.25rem;
}
</style>
""",
    unsafe_allow_html=True,
)

a, b = st.columns([2, 10], vertical_alignment="center")

with a:
    st.image(image_path, width=100)   # ⬅️ was 48
with b:
    st.title("InTouch")


st.header("Summary")

counts = get_counts()

# Metrics (keep or remove later — but they belong above the CTA)
col1, col2 = st.columns(2)
with col1:
    st.metric("Friends", counts["Friend"]["total"])
    st.metric("Friends remaining", counts["Friend"]["remaining"])
with col2:
    st.metric("Family", counts["Family"]["total"])
    st.metric("Family remaining", counts["Family"]["remaining"])

# Top rule
st.divider()

# --- Big centered Draw button (real button, centered text) ---
left, center, right = st.columns([1, 2, 1])
with center:
    if st.button("Draw names for today", use_container_width=True, type="primary"):
        st.switch_page("pages/3_Todays_Drawing.py")

# Bottom rule (balanced)
st.divider()

# --- subtle edit link ---
st.caption("Need to update your lists?")

c1, c2 = st.columns([1, 10], vertical_alignment="center")
with c1:
    st.image("assets/draw_3.png", width=35)
with c2:
    if st.button("Edit Friends & Family", use_container_width=False):
        st.switch_page("pages/2_Edit.py")


