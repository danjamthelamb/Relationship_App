import streamlit as st
from db import init_db
from ui_theme import inject_theme

APP_NAME = "InTouch"
image_path = "assets/logo_icon.png"
favicon_path = "assets/favicon.png"

# -------------------------------------------------
# Page config MUST come first
# -------------------------------------------------
st.set_page_config(
    page_title=APP_NAME,
    page_icon=favicon_path,
    layout="centered",
)
inject_theme()

l, c, r = st.columns([1, 1, 1])
with c:
    st.image(image_path)

init_db()

# -------------------------------------------------
# Styles
# -------------------------------------------------
st.markdown(
    """
<style>
.hero {
    max-width: 720px;
    margin: 0 auto;
    text-align: center;
}

/* Logo */
.hero img {
    display: block;
    margin: 0 auto 0.25rem auto;
}

/* Title + tagline */
.hero h1 {
    margin-bottom: 0.25rem;
}
.tagline {
    margin-top: 0;
    font-style: italic;
    opacity: 0.85;
}

/* Body text */
.body {
    opacity: 0.92;
    line-height: 1.6;
    margin-top: 1rem;
}

/* Bullet group card */
.bullet-wrap {
    max-width: 520px;
    margin: 1.1rem auto;
    padding: 0.9rem 1.2rem;
    border-radius: 14px;

    background: rgba(121, 201, 197, 0.22);       /* #79C9C5 wash */
    border: 1px solid rgba(63, 154, 174, 0.35);  /* #3F9AAE line */

    text-align: left;
}

.bullet-wrap ul {
    list-style-type: disc;
    list-style-position: outside;
    padding-left: 1.2rem;
    margin: 0;
}

.brand-row img{
  height: 34px;
  width: auto;
}

.brand-name{
  font-size: 4rem;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.brand-in{
  color: #3F9AAE;   /* calm, attentive */
}

.brand-touch{
  color: #F96E5B;   /* warmth, human */
}

.bullet-wrap li {
    margin: 0.4rem 0;
}

/* Closing line */
.closing {
    margin-top: 1rem;
    opacity: 0.90;
}

.app-title{
  font-size: 3rem;
  font-weight: 700;
  line-height: 1.1;
  margin: 0 0 0.25rem 0;
  color: #2E6F7A !important;
  text-shadow: 0 1px 0 rgba(0,0,0,0.06);
}

.stButton > button[kind="primary"] {
    background-color: #F96E5B;   /* coral */
    color: #222831 !important;  /* 👈 Teal text */
    border-radius: 14px;
    font-weight: 900;
    letter-spacing: 0.02em;
}

.stButton > button[kind="primary"] * {
    color: #222831 !important;
    font-weight: 700 !important;     /* use a weight that actually exists */
    font-size: 1.09rem !important;   /* makes it feel bolder immediately */
    letter-spacing: 0.08em;
}

/* Ensure hover/active states stay teal too */
.stButton > button[kind="primary"]:hover,
.stButton > button[kind="primary"]:active {
    color: #222831 !important;
}

</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Hero section (logo + title without anchor icon)
# -------------------------------------------------
st.markdown(
    f"""
<div class="hero">

  <div class="brand-name">
    <span class="brand-in">In</span><span class="brand-touch">Touch</span>
  </div>
  <p class="tagline">A gentle way to stay connected.</p>

  <p class="body">
    <strong>{APP_NAME}</strong> helps people stay meaningfully connected —
    <br>
    without relying on memory, guilt, or social media noise.
  </p>

  <p class="body">
    Instead of asking <em>“Who should I text today?”</em>,
    <br>
    {APP_NAME} gently chooses for you.
  </p>

  <div class="bullet-wrap">
    <ul>
      <li>One friend</li>
      <li>One family member</li>
      <li><strong>No repeats</strong> until everyone has been reached</li>
      <li>No pressure, no feeds, no algorithms</li>
    </ul>
  </div>

  <p class="closing">
    It’s a small daily habit designed to keep real relationships alive —
    <br>
    one message at a time.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# CTA
# -------------------------------------------------
st.divider()

left, center, right = st.columns([1, 2, 1])
with center:
    if st.button("Get started!", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Home.py")
