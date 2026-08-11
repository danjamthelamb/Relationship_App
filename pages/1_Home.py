####################
# User Homepage (1_Home.py)
####################
import base64
from pathlib import Path

import streamlit as st

from auth import require_user
from db import get_counts
from ui_theme import inject_theme


image_path = "assets/logo_icon.png"
favicon_path = "assets/favicon.png"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def img_to_data_url(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/png;base64,{b64}"


# -------------------------------------------------
# Page config MUST come first
# -------------------------------------------------
st.set_page_config(
    page_title="Home",
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


# -------------------------------------------------
# Styles
# -------------------------------------------------
st.markdown(
    """
<style>

/* Reduce top padding so things feel less floaty */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}


.brand-row {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    margin-bottom: 1.2rem;
}


.brand-row img {
    height: 72px;
    width: auto;
}


.brand-name {
    font-size: 3.2rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    line-height: 1;
}


.brand-in {
    color: #3F9AAE;
}


.brand-touch {
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


# -------------------------------------------------
# Branding
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
# Summary
# -------------------------------------------------
st.header("Summary")


counts = get_counts(current_user.id)


col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Friends",
        counts["Friend"]["total"],
    )

    st.metric(
        "Friends remaining",
        counts["Friend"]["remaining"],
    )


with col2:
    st.metric(
        "Family",
        counts["Family"]["total"],
    )

    st.metric(
        "Family remaining",
        counts["Family"]["remaining"],
    )


# -------------------------------------------------
# Draw
# -------------------------------------------------
st.divider()


left, center, right = st.columns([1, 2, 1])

with center:
    if st.button(
        "Draw names for today",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page("pages/3_Todays_Drawing.py")


st.divider()


# -------------------------------------------------
# Edit lists
# -------------------------------------------------
st.caption("Need to update your lists?")


if st.button(
    "Edit Friends & Family",
    icon=":material/edit_square:",
    use_container_width=False,
):
    st.switch_page("pages/2_Edit.py")