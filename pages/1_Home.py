####################
# User Homepage (1_Home.py)
####################
import streamlit as st

from auth import require_user
from db import get_counts, add_person
from ui_theme import inject_theme, render_brand_header


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


# -------------------------------------------------
# BRANDING
# -------------------------------------------------

render_brand_header()


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
            "Let’s get your network started with one friend "
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

            # -------------------------
            # VALIDATION
            # -------------------------

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


            # -------------------------
            # SAVE
            # -------------------------

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
# COUNTS / ONBOARDING CHECK
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


# -------------------------------------------------
# SUMMARY
# -------------------------------------------------

st.header("Summary")


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
# DRAW
# -------------------------------------------------

st.divider()


left, center, right = st.columns(
    [1, 2, 1]
)


with center:

    if st.button(
        "Draw names for today",
        use_container_width=True,
        type="primary",
    ):

        st.switch_page(
            "pages/3_Todays_Drawing.py"
        )


st.divider()


# -------------------------------------------------
# EDIT LISTS
# -------------------------------------------------

st.caption(
    "Need to update your lists?"
)


if st.button(
    "Edit Friends & Family",
    icon=":material/edit_square:",
    use_container_width=False,
):

    st.switch_page(
        "pages/2_Edit.py"
    )