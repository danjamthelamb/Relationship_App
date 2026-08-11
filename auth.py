####################
# Authentication (auth.py)
####################
import streamlit as st

from db import User, get_or_create_user, init_db
from ui_theme import render_brand_header


def require_user() -> User:
    """
    Require a logged-in Google user and return
    the corresponding InTouch user record.
    """

    init_db()

    if not st.user.is_logged_in:

        render_brand_header()

        st.write("Sign in to continue.")

        if st.button(
            "Sign in with Google",
            use_container_width=True,
            type="primary",
        ):
            st.login()

        st.stop()

    return get_or_create_user(
        auth_provider="google",
        auth_subject=st.user.sub,
        email=st.user.email,
        display_name=st.user.name,
    )


def logout_button() -> None:
    if st.button("Log out"):
        st.logout()