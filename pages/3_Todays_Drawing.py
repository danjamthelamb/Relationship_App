####################
# Today's Drawing (3_Todays_Drawing.py)
####################
import base64
import random
from pathlib import Path

import streamlit as st

from auth import require_user
from db import get_or_create_today_draw, get_counts
from ui_theme import inject_theme


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def img_to_data_url(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def pick_quote(
    quotes: list[dict],
    avoid: dict | None = None,
) -> dict:
    """
    Pick a random quote and try not to repeat
    the current one.
    """

    if not quotes:
        return {
            "text": "",
            "author": "",
        }

    if avoid and len(quotes) > 1:
        pool = [
            quote
            for quote in quotes
            if quote != avoid
        ]

        return random.choice(pool)

    return random.choice(quotes)


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

favicon_path = "assets/favicon.png"

st.set_page_config(
    page_title="Today",
    page_icon=favicon_path,
    layout="centered",
)


# -------------------------------------------------
# THEME
# -------------------------------------------------

inject_theme()


# -------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------

current_user = require_user()


# -------------------------------------------------
# USER-SPECIFIC SESSION KEYS
# -------------------------------------------------

# draw_key = f"today_draw_{current_user.id}"
quote_key = f"today_quote_{current_user.id}"


# -------------------------------------------------
# QUOTES
# -------------------------------------------------

QUOTES = [
    {
        "text": "Attention is the rarest and purest form of generosity.",
        "author": "Simone Weil",
    },
    {
        "text": "No act of kindness, no matter how small, is ever wasted.",
        "author": "Aesop",
    },
    {
        "text": "To love is to attend.",
        "author": "Simone Weil",
    },
]


# -------------------------------------------------
# STYLES
# -------------------------------------------------

st.markdown(
    """
<style>

.hero {
    max-width: 720px;
    margin: 0 auto;
}


.muted {
    opacity: 0.65;
}


.center {
    text-align: center;
}


.result-wrap {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
    margin-bottom: 2.5rem;
}


.result-card {
    flex: 1;
    padding: 1rem 1.2rem;
    border-radius: 16px;
    box-shadow: 0 8px 18px rgba(63, 154, 174, 0.10);

    background: rgba(121, 201, 197, 0.22);
    border: 1px solid rgba(63, 154, 174, 0.35);
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


.brand-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    margin-top: 0.25rem;
    margin-bottom: 0.75rem;
}


.brand-row img {
    height: 34px;
    width: auto;
}


.brand-name {
    font-size: 1.8rem;
    font-weight: 900;
    letter-spacing: -0.02em;
}


.brand-in {
    color: #3F9AAE;
}


.brand-touch {
    color: #F96E5B;
}


.hello-callout {
    margin-top: 1.8rem;
    font-style: italic;
    font-size: 1.05rem;
    line-height: 1.6;

    color: #6F4F3D;
    font-weight: 500;
    text-align: center;
}


.hello-author {
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: #8A6A4A;
    font-weight: 400;
}

</style>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# BRANDING
# -------------------------------------------------

logo_url = img_to_data_url("assets/logo_icon.png")

st.markdown(
    f"""
<div class="brand-row">
<img src="{logo_url}" />
<span class="brand-name"><span class="brand-in">In</span><span class="brand-touch">Touch</span></span>
</div>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# PAGE CONTENT
# -------------------------------------------------

st.markdown(
    "<div class='hero'>",
    unsafe_allow_html=True,
)


left, center, right = st.columns([1, 6, 1])

with center:
    st.title("Today’s connections")


# -------------------------------------------------
# CHECK LISTS
# -------------------------------------------------

counts = get_counts(current_user.id)

if (
    counts["Friend"]["total"] == 0
    or counts["Family"]["total"] == 0
):
    st.warning(
        "You need at least **1 Friend** and "
        "**1 Family** person before drawing."
    )

    if st.button(
        "✏️ Add people",
        type="primary",
    ):
        st.switch_page("pages/2_Edit.py")

    st.stop()


# -------------------------------------------------
# INITIAL DRAW
# -------------------------------------------------

# if draw_key not in st.session_state:
#     st.session_state[draw_key] = draw_friend_and_family(
#         current_user.id
#     )

result = get_or_create_today_draw(
    current_user.id
)

if quote_key not in st.session_state:
    st.session_state[quote_key] = pick_quote(
        QUOTES
    )


# result = st.session_state[draw_key]
quote = st.session_state[quote_key]


# -------------------------------------------------
# RESULTS
# -------------------------------------------------

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


# -------------------------------------------------
# QUOTE
# -------------------------------------------------

st.markdown(
    f"""
<div class="hello-callout">
“{quote['text']}”
<div class="hello-author">— {quote['author']}</div>
</div>
""",
    unsafe_allow_html=True,
)


st.divider()


# -------------------------------------------------
# REMAINING COUNTS
# -------------------------------------------------

counts2 = get_counts(current_user.id)

st.markdown(
    f"""
<p class="center muted">
Remaining this cycle —
Friends: {counts2['Friend']['remaining']}
·
Family: {counts2['Family']['remaining']}
</p>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# DRAW AGAIN
# -------------------------------------------------

left, center, right = st.columns([1, 2, 1])

with center:

    if st.button(
        "Draw again",
        use_container_width=True,
        type="primary",
    ):

        st.session_state[draw_key] = (
            draw_friend_and_family(
                current_user.id
            )
        )

        st.session_state[quote_key] = pick_quote(
            QUOTES,
            avoid=st.session_state.get(
                quote_key
            ),
        )

        st.rerun()


# -------------------------------------------------
# BACK BUTTON STYLES
# -------------------------------------------------

back_url = img_to_data_url("assets/back_3.png")


st.markdown(
    """
<style>

.back-wrap {
    margin-top: 0.25rem;
}


a.back-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;

    padding: 0.45rem 0.85rem;
    border-radius: 12px;

    background: rgba(255, 255, 255, 0.65);
    border: 1px solid rgba(31, 41, 55, 0.20);
    box-shadow: 0 6px 14px rgba(63, 154, 174, 0.10);

    color: #1F2937;
    font-weight: 700;
    text-decoration: none;

    transition:
        transform 120ms ease,
        box-shadow 120ms ease;
}


a.back-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 18px rgba(63, 154, 174, 0.14);
}


a.back-btn img {
    height: 18px;
    width: auto;
    display: block;
}

</style>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# BACK TO HOME
# -------------------------------------------------

if st.button(
    "Back to Home",
    icon=":material/undo:",
    use_container_width=True,
):
    st.switch_page("pages/1_Home.py")


st.markdown(
    "</div>",
    unsafe_allow_html=True,
)