import streamlit as st

from db import User, get_or_create_user, init_db


def require_user() -> User:
    """
    Require a logged-in Google user and return
    the corresponding InTouch user record.
    """

    # Safe to call repeatedly; ensures the DB/schema exists.
    init_db()

    if not st.user.is_logged_in:
        st.title("InTouch")
        st.write("Sign in to continue.")

        if st.button("Sign in with Google"):
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