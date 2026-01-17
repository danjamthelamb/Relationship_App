import base64
import streamlit as st
from db import get_counts, init_db
from ui_theme import inject_theme
from pathlib import Path

image_path = "assets/logo_icon.png"
favicon_path = "assets/favicon.png"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def img_to_data_url(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/png;base64,{b64}"

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

.brand-row{
  display: flex;
  align-items: center;
  gap: 0.9rem;           /* slightly more breathing room */
  margin-bottom: 1.2rem;
}

.brand-row img{
  height: 72px;          /* down from 100px — more balanced */
  width: auto;
}

.brand-name{
  font-size: 3.2rem;     /* THIS is the main change */
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1;        /* keeps it tight vertically */
}

.brand-in{
  color: #3F9AAE;
}

.brand-touch{
  color: #F96E5B;
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

logo_url = img_to_data_url("assets/logo_icon.png")

st.markdown(
    f"""
    <div class="brand-row">
        <img src="{logo_url}" />
        <span class="brand-name">
            <span class="brand-in">In</span><span class="brand-touch">Touch</span>
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)


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

# c1, c2 = st.columns([1, 18], vertical_alignment="center")
# with c1:
#     st.image("assets/edit_1.png", width=35)
# with c2:
#     if st.button("Edit Friends & Family", use_container_width=False):
#         st.switch_page("pages/2_Edit.py")


if st.button("Edit Friends & Family", icon=":material/edit_square:", use_container_width=False):
    st.switch_page("pages/2_Edit.py")