####################
# User Homepage (1_Home.py)
####################
from datetime import date
import random

import streamlit as st

from auth import require_user, logout_button
from db import (
    add_person,
    get_counts,
    get_or_create_today_draw,
)
from ui_theme import (
    inject_theme,
    render_brand_header,
)


favicon_path = "assets/favicon.png"


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Home",
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
st.success(
    f"Logged in as {current_user.display_name}"
)


# -------------------------------------------------
# BRANDING
# -------------------------------------------------

render_brand_header()


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


def get_daily_quote() -> dict:
    """
    Return one stable quote for the current date.

    The quote changes from day to day,
    but does not change when the page refreshes.
    """

    rng = random.Random(
        date.today().isoformat()
    )

    return rng.choice(QUOTES)


# -------------------------------------------------
# PAGE-SPECIFIC STYLES
# -------------------------------------------------

st.markdown(
    """
<style>

/* --------------------------------
   Section headings
-------------------------------- */

.section-title {
    font-size: 1.65rem;
    font-weight: 800;
    margin-top: 1.2rem;
    margin-bottom: 0.25rem;
}

.section-subtitle {
    opacity: 0.67;
    margin-top: 0;
    margin-bottom: 1rem;
}


/* --------------------------------
   Today's connections
-------------------------------- */

.connection-wrap {
    display: flex;
    gap: 1rem;
    margin-top: 0.8rem;
}

.connection-card {
    flex: 1;
    padding: 1.1rem 1.2rem;
    border-radius: 16px;

    background: rgba(121, 201, 197, 0.22);
    border: 1px solid rgba(63, 154, 174, 0.35);

    box-shadow: 0 8px 18px rgba(63, 154, 174, 0.08);
}

.connection-type {
    font-size: 0.9rem;
    font-weight: 600;
    opacity: 0.68;
    margin-bottom: 0.2rem;
}

.connection-name {
    font-size: 1.55rem;
    font-weight: 750;
}


/* --------------------------------
   Quote
-------------------------------- */

.daily-quote {
    margin: 1.7rem auto 0.5rem auto;
    max-width: 600px;

    text-align: center;
    font-style: italic;
    line-height: 1.6;

    color: #6F4F3D;
}

.daily-quote-author {
    margin-top: 0.35rem;
    font-size: 0.85rem;
    color: #8A6A4A;
}


/* --------------------------------
   Your people
-------------------------------- */

.people-total {
    margin-top: 0.25rem;
    margin-bottom: 1.2rem;

    font-size: 1.05rem;
    opacity: 0.78;
}


/* --------------------------------
   Progress cards
-------------------------------- */

.progress-card {
    margin-bottom: 1rem;
    padding: 1rem 1.1rem;

    border-radius: 14px;

    background: rgba(255, 255, 255, 0.38);
    border: 1px solid rgba(31, 41, 55, 0.12);
}

.progress-heading {
    display: flex;
    justify-content: space-between;
    align-items: baseline;

    margin-bottom: 0.55rem;
}

.progress-name {
    font-size: 1.05rem;
    font-weight: 750;
}

.progress-count {
    font-size: 0.92rem;
    opacity: 0.68;
}

.progress-track {
    width: 100%;
    height: 10px;

    background: rgba(63, 154, 174, 0.12);

    border-radius: 999px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;

    background: #79C9C5;

    border-radius: 999px;
}


/* --------------------------------
   Edit area
-------------------------------- */

.change-title {
    margin-bottom: 0.25rem;
    font-weight: 700;
}

.change-text {
    opacity: 0.67;
    margin-top: 0;
    margin-bottom: 0.75rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# FIRST-TIME / EMPTY-LIST ONBOARDING
# -------------------------------------------------

@st.dialog("Welcome to InTouch")
def first_people_dialog(
    needs_friend: bool,
    needs_family: bool,
) -> None:

    if needs_friend and needs_family:

        st.write(
            "Let’s get your people started with one friend "
            "and one family member."
        )

    elif needs_friend:

        st.write(
            "Your family list is ready. "
            "Let’s add your first friend."
        )

    elif needs_family:

        st.write(
            "Your friends list is ready. "
            "Let’s add your first family member."
        )


    with st.form("first_people_form"):

        friend_name = ""
        family_name = ""


        if needs_friend:

            friend_name = st.text_input(
                "Your first friend",
                placeholder="Enter their name",
            )


        if needs_family:

            family_name = st.text_input(
                "Your first family member",
                placeholder="Enter their name",
            )


        submitted = st.form_submit_button(
            "Get started",
            icon=":material/person_add:",
            use_container_width=True,
            type="primary",
        )


        if submitted:

            if (
                needs_friend
                and not friend_name.strip()
            ):

                st.error(
                    "Please enter a friend."
                )

                return


            if (
                needs_family
                and not family_name.strip()
            ):

                st.error(
                    "Please enter a family member."
                )

                return


            try:

                if needs_friend:

                    add_person(
                        current_user.id,
                        friend_name,
                        "Friend",
                    )


                if needs_family:

                    add_person(
                        current_user.id,
                        family_name,
                        "Family",
                    )


            except ValueError as e:

                st.error(str(e))

                return


            st.rerun()


# -------------------------------------------------
# ONBOARDING CHECK
# -------------------------------------------------

counts = get_counts(
    current_user.id
)


needs_friend = (
    counts["Friend"]["total"] == 0
)

needs_family = (
    counts["Family"]["total"] == 0
)


if needs_friend or needs_family:

    first_people_dialog(
        needs_friend=needs_friend,
        needs_family=needs_family,
    )

    # Don't attempt a daily draw until both
    # lists contain at least one person.
    st.stop()


# -------------------------------------------------
# TODAY'S CONNECTIONS
# -------------------------------------------------

today_result = get_or_create_today_draw(
    current_user.id
)


# The draw may have changed remaining counts,
# so refresh them after loading today's pair.
counts = get_counts(
    current_user.id
)


st.markdown(
    """
<div class="section-title">
Today's connections
</div>
""",
    unsafe_allow_html=True,
)


st.markdown(
    f"""
<div class="connection-wrap">
<div class="connection-card">
<div class="connection-type">Friend</div>
<div class="connection-name">{today_result.friend}</div>
</div>
<div class="connection-card">
<div class="connection-type">Family</div>
<div class="connection-name">{today_result.family}</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# QUOTE OF THE DAY
# -------------------------------------------------

quote = get_daily_quote()


st.markdown(
    f"""
<div class="daily-quote">
“{quote['text']}”
<div class="daily-quote-author">— {quote['author']}</div>
</div>
""",
    unsafe_allow_html=True,
)


st.divider()


# -------------------------------------------------
# YOUR PEOPLE
# -------------------------------------------------

friend_total = counts["Friend"]["total"]
friend_remaining = counts["Friend"]["remaining"]
friend_reached = (
    friend_total - friend_remaining
)


family_total = counts["Family"]["total"]
family_remaining = counts["Family"]["remaining"]
family_reached = (
    family_total - family_remaining
)


friend_progress = (
    (friend_reached / friend_total) * 100
    if friend_total
    else 0
)


family_progress = (
    (family_reached / family_total) * 100
    if family_total
    else 0
)


st.markdown(
    """
<div class="section-title">
Your people
</div>
""",
    unsafe_allow_html=True,
)


st.markdown(
    f"""
<div class="people-total">
{friend_total} friends · {family_total} family members
</div>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# FRIEND PROGRESS
# -------------------------------------------------

st.markdown(
    f"""
<div class="progress-card">
<div class="progress-heading">
<span class="progress-name">Friends</span>
<span class="progress-count">{friend_reached} of {friend_total} reached</span>
</div>
<div class="progress-track">
<div class="progress-fill" style="width: {friend_progress}%"></div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------
# FAMILY PROGRESS
# -------------------------------------------------

st.markdown(
    f"""
<div class="progress-card">
<div class="progress-heading">
<span class="progress-name">Family</span>
<span class="progress-count">{family_reached} of {family_total} reached</span>
</div>
<div class="progress-track">
<div class="progress-fill" style="width: {family_progress}%"></div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


st.divider()


# -------------------------------------------------
# EDIT LISTS
# -------------------------------------------------

st.markdown(
    """
<div class="change-title">
Need to make a change?
</div>
<div class="change-text">
Add someone new, remove someone, or update your lists.
</div>
""",
    unsafe_allow_html=True,
)


if st.button(
    "Edit Friends & Family",
    icon=":material/edit_square:",
    use_container_width=False,
):

    st.switch_page(
        "pages/2_Edit.py"
    )

# -------------------------------------------------
# ACCOUNT
# -------------------------------------------------

st.divider()

logout_button()