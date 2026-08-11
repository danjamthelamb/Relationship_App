####################
# Edit People (2_Edit.py)
####################
import pandas as pd
import streamlit as st

from auth import require_user
from db import (
    get_people_df,
    upsert_people,
    add_person,
    reset_drawn,
    reset_prev,
)
from ui_theme import inject_theme


# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Edit People",
    page_icon="✏️",
    layout="centered",
)


inject_theme()


# ---------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------

current_user = require_user()


# ---------------------------------------------------
# STYLES
# ---------------------------------------------------

st.markdown(
    """
    <style>
      [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------
# ADD NEW PERSON DIALOG
# ---------------------------------------------------

@st.dialog("Add new person")
def add_person_dialog():

    with st.form("add_person_form"):

        name = st.text_input(
            "Name",
            placeholder="Enter their name",
        )

        relationship = st.selectbox(
            "Relationship",
            ["Friend", "Family"],
        )

        submitted = st.form_submit_button(
            "Add person",
            icon=":material/person_add:",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():
                st.error("Please enter a name.")
                return

            try:
                add_person(
                    current_user.id,
                    name,
                    relationship,
                )

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
    use_container_width=True,
):
    add_person_dialog()


# ---------------------------------------------------
# PEOPLE TABLE
# ---------------------------------------------------

# Keep the COMPLETE user dataset.
all_people_df = get_people_df(current_user.id)


filter_choice = st.segmented_control(
    "Show",
    options=["All", "Friends", "Family"],
    default="All",
)


# Create a filtered COPY only for display.
if filter_choice == "Friends":
    display_df = all_people_df[
        all_people_df["relationship"] == "Friend"
    ].copy()

elif filter_choice == "Family":
    display_df = all_people_df[
        all_people_df["relationship"] == "Family"
    ].copy()

else:
    display_df = all_people_df.copy()


if display_df.empty:
    display_df = pd.DataFrame(
        columns=[
            "id",
            "name",
            "relationship",
            "drawn",
        ]
    )


edited = st.data_editor(
    display_df,
    num_rows="fixed",
    use_container_width=True,
    hide_index=True,
    column_order=[
        "name",
        "relationship",
    ],
    column_config={
        "name": st.column_config.TextColumn(
            "Name",
            required=True,
        ),
        "relationship": st.column_config.SelectboxColumn(
            "Relationship",
            options=["Friend", "Family"],
            required=True,
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
        use_container_width=True,
    ):

        edited2 = edited.copy()

        if not edited2.empty:
            edited2["drawn"] = edited2["drawn"].astype(int)

        # Start with the complete dataset.
        updated_df = all_people_df.copy()

        # Replace only the rows that were visible/editable.
        for _, edited_row in edited2.iterrows():

            row_id = int(edited_row["id"])

            updated_df.loc[
                updated_df["id"] == row_id,
                ["name", "relationship", "drawn"],
            ] = [
                edited_row["name"],
                edited_row["relationship"],
                edited_row["drawn"],
            ]

        upsert_people(
            current_user.id,
            updated_df,
        )

        st.success("Saved!")
        st.rerun()


with col2:

    if st.button(
        "Back to Home",
        icon=":material/undo:",
        use_container_width=True,
    ):
        st.switch_page("pages/1_Home.py")


# ---------------------------------------------------
# RESET CONTACT CYCLE
# ---------------------------------------------------

with st.expander(
    "Reset contact cycle",
    expanded=False,
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
            disabled=not confirm,
        ):

            reset_drawn(
                current_user.id,
                "Friend",
            )

            reset_prev(
                current_user.id,
                "Friend",
            )

            st.success("Friends reset.")
            st.rerun()


    with c2:

        if st.button(
            "Reset Family",
            disabled=not confirm,
        ):

            reset_drawn(
                current_user.id,
                "Family",
            )

            reset_prev(
                current_user.id,
                "Family",
            )

            st.success("Family reset.")
            st.rerun()


    with c3:

        if st.button(
            "Reset All",
            disabled=not confirm,
        ):

            reset_drawn(
                current_user.id,
                None,
            )

            reset_prev(
                current_user.id,
                None,
            )

            st.success("All reset.")
            st.rerun()