import streamlit as st
from db import draw_friend_and_family, get_counts, init_db
from ui_theme import inject_theme

st.set_page_config(page_title="Today", page_icon="🎲", layout="centered")
inject_theme()
init_db()

# ---- Styles (match landing page cards) ----
st.markdown(
    """
<style>
.hero {
    max-width: 720px;
    margin: 0 auto;
}

.center {
    text-align: center;
}

.result-wrap {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.result-card {
    flex: 1;
    padding: 1rem 1.2rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
}

.result-title {
    font-weight: 600;
    opacity: 0.85;
    margin-bottom: 0.25rem;
}

.result-name {
    font-size: 1.5rem;
    font-weight: 700;
}

.muted {
    opacity: 0.75;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<div class='hero'>", unsafe_allow_html=True)

st.title("Today’s names")

counts = get_counts()
if counts["Friend"]["total"] == 0 or counts["Family"]["total"] == 0:
    st.warning("You need at least **1 Friend** and **1 Family** person before drawing.")
    if st.button("✏️ Add people", type="primary"):
        st.switch_page("pages/2_Edit.py")
    st.stop()

# ---- Draw once on first load ----
if "today_draw" not in st.session_state:
    st.session_state["today_draw"] = draw_friend_and_family()

result = st.session_state["today_draw"]

# ---- Centered header ----
st.markdown(
    "<h3 class='center'>Text these people</h3>",
    unsafe_allow_html=True,
)

# ---- Results (card layout) ----
st.markdown(
    f"""
<div class="result-wrap">
    <div class="result-card">
        <div class="result-title">Friend:</div>
        <div class="result-name">{result.friend}</div>
    </div>
    <div class="result-card">
        <div class="result-title">Family:</div>
        <div class="result-name">{result.family}</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

counts2 = get_counts()
st.markdown(
    f"<p class='center muted'>Remaining this cycle — "
    f"Friends: {counts2['Friend']['remaining']} | "
    f"Family: {counts2['Family']['remaining']}</p>",
    unsafe_allow_html=True,
)

st.divider()

# ---- Controls ----
left, center, right = st.columns([1, 2, 1])
with center:
    if st.button("Draw again", use_container_width=True):
        st.session_state["today_draw"] = draw_friend_and_family()
        st.rerun()

if st.button("⬅️ Back to Home"):
    st.switch_page("pages/1_Home.py")

st.markdown("</div>", unsafe_allow_html=True)
