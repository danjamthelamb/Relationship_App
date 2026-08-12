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

.feature-grid {
    max-width: 560px;
    margin: 1.6rem auto;

    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.8rem;

    text-align: left;
}


.feature-card {
    padding: 1rem 1.1rem;

    border-radius: 16px;

    background: rgba(121, 201, 197, 0.16);
    border: 1px solid rgba(63, 154, 174, 0.28);

    box-shadow: 0 6px 14px rgba(63, 154, 174, 0.06);
}


.feature-kicker {
    margin-bottom: 0.3rem;

    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;

    color: #3F9AAE;
}


.feature-title {
    margin-bottom: 0.3rem;

    font-size: 1.05rem;
    font-weight: 800;

    color: #1F2937;
}


.feature-copy {
    margin: 0;

    font-size: 0.9rem;
    line-height: 1.45;

    opacity: 0.72;
}


/* Stack gracefully on narrow screens */
@media (max-width: 600px) {
    .feature-grid {
        grid-template-columns: 1fr;
    }
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
<strong>{APP_NAME}</strong> helps people stay meaningfully connected
<br>
without relying on memory, guilt, or social media noise.
</p>

<p class="body">
Instead of asking <em>“Who should I text today?”</em>
<br>
{APP_NAME} gently chooses for you.
</p>

<div class="feature-grid">

<div class="feature-card">
<div class="feature-kicker">Friend</div>
<div class="feature-title">One friend</div>
<p class="feature-copy">
A simple daily nudge toward someone you care about.
</p>
</div>

<div class="feature-card">
<div class="feature-kicker">Family</div>
<div class="feature-title">One family member</div>
<p class="feature-copy">
Keep family connections in the rhythm, too.
</p>
</div>

<div class="feature-card">
<div class="feature-kicker">Thoughtful rotation</div>
<div class="feature-title">No repeats</div>
<p class="feature-copy">
Everyone gets a turn before the list begins again.
</p>
</div>

<div class="feature-card">
<div class="feature-kicker">Keep it simple</div>
<div class="feature-title">No feeds. No pressure.</div>
<p class="feature-copy">
Just a small daily prompt, then get on with your day.
</p>
</div>

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