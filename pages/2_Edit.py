####################
# Edit People (2_Edit.py)
####################
import streamlit as st
import pandas as pd

from db import (
    get_people_df,
    init_db,
    upsert_people,
    add_person,
    reset_drawn,
    reset_prev,
)

from ui_theme import inject_theme


st.set_page_config(
    page_title="Edit People",
    page_icon="✏️",
    layout="centered"
)

inject_theme()


st.markdown(
    """
    <style>
      [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)


init_db()


# ---------------------------------------------------
# ADD NEW PERSON DIALOG
# ---------------------------------------------------

@st.dialog("Add new person")
def add_person_dialog():

    with st.form("add_person_form"):

        name = st.text_input(
            "Name",
            placeholder="Enter their name"
        )

        relationship = st.selectbox(
            "Relationship",
            ["Friend", "Family"]
        )

        submitted = st.form_submit_button(
            "Add person",
            icon=":material/person_add:",
            use_container_width=True
        )

        if submitted:

            if not name.strip():
                st.error("Please enter a name.")
                return

            try:
                add_person(name, relationship)

            except ValueError as e:
                st.error(str(e))
                return

            st.rerun()


# ---------------------------------------------------
# PAGE
# ---------------------------------------------------

st.title("Update Your Network")

st.caption(
    "Add people or update names and relationships."
)


# ---------------------------------------------------
# ADD PERSON BUTTON
# ---------------------------------------------------

if st.button(
    "Add new person",
    icon=":material/person_add:",
    use_container_width=True
):
    add_person_dialog()


# ---------------------------------------------------
# PEOPLE TABLE
# ---------------------------------------------------

df = get_people_df()


filter_choice = st.segmented_control(
    "Show",
    options=["All", "Friends", "Family"],
    default="All",
)


if filter_choice == "Friends":
    df = df[df["relationship"] == "Friend"]

elif filter_choice == "Family":
    df = df[df["relationship"] == "Family"]


if df.empty:
    df = pd.DataFrame(
        columns=[
            "id",
            "name",
            "relationship",
            "drawn"
        ]
    )


edited = st.data_editor(
    df,
    num_rows="fixed",
    use_container_width=True,
    hide_index=True,
    column_order=[
        "name",
        "relationship"
    ],
    column_config={
        "name": st.column_config.TextColumn(
            "Name",
            required=True
        ),
        "relationship": st.column_config.SelectboxColumn(
            "Relationship",
            options=["Friend", "Family"],
            required=True
        ),
    },
)


# ---------------------------------------------------
# SAVE / BACK
# ---------------------------------------------------

col1, col2 = st.columns(2)


with col1:

    if st.button(
        "Save changes",
        icon=":material/save:",
        use_container_width=True
    ):

        edited2 = edited.copy()

        edited2["drawn"] = edited2["drawn"].astype(int)

        upsert_people(edited2)

        st.success("Saved!")

        st.rerun()


with col2:

    if st.button(
        "Back to Home",
        icon=":material/undo:",
        use_container_width=True
    ):

        st.switch_page("pages/1_Home.py")


# ---------------------------------------------------
# RESET CONTACT CYCLE
# ---------------------------------------------------

with st.expander(
    "Reset contact cycle",
    expanded=False
):

    st.warning(
        "This sets selected people back to untexted."
    )

    confirm = st.checkbox(
        "I understand this will reset progress."
    )


    c1, c2, c3 = st.columns(3)


    with c1:

        if st.button(
            "Reset Friends",
            disabled=not confirm
        ):

            reset_drawn("Friend")
            reset_prev("Friend")

            st.success("Friends reset.")

            st.rerun()


    with c2:

        if st.button(
            "Reset Family",
            disabled=not confirm
        ):

            reset_drawn("Family")
            reset_prev("Family")

            st.success("Family reset.")

            st.rerun()


    with c3:

        if st.button(
            "Reset All",
            disabled=not confirm
        ):

            reset_drawn(None)
            reset_prev(None)

            st.success("All reset.")

            st.rerun()