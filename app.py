####################
# App Configuration (app.py)
####################
import streamlit as st

from auth import require_user, logout_button
from ui_theme import inject_theme, render_brand_header


APP_NAME = "InTouch"
favicon_path = "assets/favicon.png"


# -------------------------------------------------
# Page config MUST come first
# -------------------------------------------------
st.set_page_config(
    page_title=APP_NAME,
    page_icon=favicon_path,
    layout="centered",
)


# -------------------------------------------------
# Theme
# -------------------------------------------------
inject_theme()


# -------------------------------------------------
# Authentication
# -------------------------------------------------
current_user = require_user()


st.success(
    f"Logged in as {current_user.display_name}"
)

st.write(
    f"Email: {current_user.email}"
)

st.write(
    "InTouch user ID:",
    current_user.id,
)


logout_button()


# -------------------------------------------------
# Landing page styles
# -------------------------------------------------
st.markdown(
    """
<style>

.hero {
    max-width: 720px;
    margin: 0 auto;
    text-align: center;
}


.tagline {
    margin-top: 0;
    font-style: italic;
    opacity: 0.85;
}


.body {
    opacity: 0.92;
    line-height: 1.6;
    margin-top: 1rem;
}


.bullet-wrap {
    max-width: 520px;
    margin: 1.1rem auto;
    padding: 0.9rem 1.2rem;
    border-radius: 14px;

    background: rgba(121, 201, 197, 0.22);
    border: 1px solid rgba(63, 154, 174, 0.35);

    text-align: left;
}


.bullet-wrap ul {
    list-style-type: disc;
    list-style-position: outside;
    padding-left: 1.2rem;
    margin: 0;
}


.bullet-wrap li {
    margin: 0.4rem 0;
}


.closing {
    margin-top: 1rem;
    opacity: 0.90;
}


/* Landing page primary CTA */
.stButton > button[kind="primary"] {
    background-color: #F96E5B;
    color: #222831 !important;
    border-radius: 14px;
    font-weight: 900;
    letter-spacing: 0.02em;
}


.stButton > button[kind="primary"] * {
    color: #222831 !important;
    font-weight: 700 !important;
    font-size: 1.09rem !important;
    letter-spacing: 0.08em;
}


.stButton > button[kind="primary"]:hover,
.stButton > button[kind="primary"]:active {
    color: #222831 !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# Branding
# -------------------------------------------------
render_brand_header(centered=True)


# -------------------------------------------------
# Hero section
# -------------------------------------------------
st.markdown(
    f"""
<div class="hero">

<p class="tagline">
A gentle way to stay connected.
</p>

<p class="body">
<strong>{APP_NAME}</strong> helps people stay meaningfully connected —
<br>
without relying on memory, guilt, or social media noise.
</p>

<p class="body">
Instead of asking <em>“Who should I text today?”</em>
<br>
{APP_NAME} gently chooses for you.
</p>

<div class="bullet-wrap">
<ul>
<li>One friend</li>
<li>One family member</li>
<li>No repeats until everyone has been reached</li>
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
    if st.button(
        "Get started!",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page("pages/1_Home.py")