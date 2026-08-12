####################
# Edit People (2_Edit.py)
####################
import uuid

import pandas as pd
import streamlit as st

from auth import require_user
from db import (
    get_people_df,
    upsert_people,
    reset_drawn,
    reset_prev,
    set_user_groups,
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
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------
# DRAFT DATA
# ---------------------------------------------------

draft_key = f"people_draft_{current_user.id}"


def load_draft() -> pd.DataFrame:
    df = get_people_df(current_user.id).copy()

    if df.empty:
        df = pd.DataFrame(
            columns=[
                "id",
                "name",
                "relationship",
                "drawn",
                "last_drawn_date",
            ]
        )

    df["last_drawn_date"] = pd.to_datetime(
        df["last_drawn_date"],
        errors="coerce",
    ).dt.date

    df["_draft_id"] = [
        f"db:{person_id}"
        for person_id in df["id"]
    ]

    return df


if draft_key not in st.session_state:
    st.session_state[draft_key] = load_draft()


# ---------------------------------------------------
# ADD NEW PERSON DIALOG
# ---------------------------------------------------

@st.dialog("Add new person")
def add_person_dialog() -> None:

    name = st.text_input(
        "Name",
        placeholder="Enter their name",
    )

    relationship = st.selectbox(
        "Relationship",
        options=[
            "Friend",
            "Family",
        ],
    )


    if st.button(
        "Add person",
        icon=":material/person_add:",
        use_container_width=True,
        type="primary",
    ):

        # ---------------------------------
        # VALIDATION
        # ---------------------------------

        clean_name = name.strip()

        if not clean_name:

            st.error(
                "Please enter a name."
            )

            return


        # ---------------------------------
        # DUPLICATE CHECK
        # ---------------------------------

        draft = st.session_state[
            draft_key
        ]


        duplicate = draft[
            (
                draft["name"]
                .astype(str)
                .str.strip()
                .str.casefold()
                == clean_name.casefold()
            )
            &
            (
                draft["relationship"]
                == relationship
            )
        ]


        if not duplicate.empty:

            st.error(
                f"{clean_name} is already in your "
                f"{relationship} list."
            )

            return


        # ---------------------------------
        # ADD TO DRAFT
        # ---------------------------------

        new_row = pd.DataFrame(
            [
                {
                    "_draft_id": (
                        f"new:{uuid.uuid4()}"
                    ),

                    "id": None,

                    "name": clean_name,

                    "relationship": (
                        relationship
                    ),

                    "drawn": 0,

                    "last_drawn_date": None,
                }
            ]
        )


        st.session_state[
            draft_key
        ] = pd.concat(
            [
                st.session_state[
                    draft_key
                ],
                new_row,
            ],
            ignore_index=True,
        )


        # ---------------------------------
        # ENABLE GROUP ON SAVE
        # ---------------------------------
        # If this group is currently disabled,
        # adding someone to it is treated as
        # intent to start using it again.
        #
        # We do NOT update the database yet.
        # This remains part of the draft until
        # Save changes is clicked.

        if (
            relationship == "Friend"
            and not current_user.use_friends
        ):

            st.session_state[
                "enable_friends_on_save"
            ] = True


        if (
            relationship == "Family"
            and not current_user.use_family
        ):

            st.session_state[
                "enable_family_on_save"
            ] = True


        st.rerun()

@st.dialog("Remove person")
def remove_person_dialog():

    draft = st.session_state[draft_key].copy()

    if draft.empty:
        st.info("There are no people to remove.")
        return

    # Build labels while using _draft_id as the actual unique value.
    person_options = draft["_draft_id"].tolist()

    person_lookup = {
        row["_draft_id"]: (
            f'{row["name"]} — {row["relationship"]}'
        )
        for _, row in draft.iterrows()
    }

    selected_id = st.selectbox(
        "Person",
        person_options,
        format_func=lambda draft_id: person_lookup[draft_id],
    )

    st.warning(
        "This person will only be removed when you save your changes."
    )

    if st.button(
        "Remove person",
        icon=":material/delete:",
        type="primary",
        use_container_width=True,
    ):

        st.session_state[draft_key] = draft[
            draft["_draft_id"] != selected_id
        ].copy()

        st.rerun()


# ---------------------------------------------------
# PAGE
# ---------------------------------------------------

st.title("Update Your Network")

st.caption(
    "Add people or update names and relationships."
)


# ---------------------------------------------------
# ADD / REMOVE PERSON
# ---------------------------------------------------

add_col, remove_col = st.columns(2)

with add_col:
    if st.button(
        "Add new person",
        icon=":material/person_add:",
        use_container_width=True,
    ):
        add_person_dialog()

with remove_col:
    if st.button(
        "Remove person",
        icon=":material/delete:",
        use_container_width=True,
    ):
        remove_person_dialog()


# ---------------------------------------------------
# FILTER
# ---------------------------------------------------

filter_choice = st.segmented_control(
    "Show",
    options=[
        "All",
        "Friends",
        "Family",
    ],
    default="All",
)


# Always work from the temporary draft.
all_people_df = st.session_state[draft_key].copy()


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


# ---------------------------------------------------
# PEOPLE TABLE
# ---------------------------------------------------

edited = st.data_editor(
    display_df,
    num_rows="fixed",
    use_container_width=True,
    hide_index=True,

    column_order=[
        "name",
        "relationship",
        "last_drawn_date",
    ],

    column_config={
        "name": st.column_config.TextColumn(
            "Name",
            required=True,
        ),

        "relationship": st.column_config.SelectboxColumn(
            "Relationship",
            options=[
                "Friend",
                "Family",
            ],
            required=True,
        ),

        "last_drawn_date": st.column_config.DateColumn(
            "Last reached",
            format="localized",
            help="The most recent date this person was drawn.",
        ),
    },

    disabled=[
        "last_drawn_date",
    ],

    key=f"people_editor_{current_user.id}_{filter_choice}",
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

        updated_draft = (
            st.session_state[draft_key].copy()
        )

        # Merge the visible editor rows back into
        # the complete draft.
        for _, edited_row in edited.iterrows():

            draft_id = edited_row["_draft_id"]

            mask = (
                updated_draft["_draft_id"]
                == draft_id
            )

            updated_draft.loc[
                mask,
                [
                    "name",
                    "relationship",
                    "drawn",
                ],
            ] = [
                str(edited_row["name"]).strip(),
                edited_row["relationship"],
                int(edited_row["drawn"]),
            ]

        # Remove blank names before saving.
        updated_draft["name"] = (
            updated_draft["name"]
            .astype(str)
            .str.strip()
        )

        updated_draft = updated_draft[
            updated_draft["name"] != ""
        ].copy()

        try:

            upsert_people(
                current_user.id,
                updated_draft[
                    [
                        "id",
                        "name",
                        "relationship",
                        "drawn",
                    ]
                ],
            )

        except ValueError as e:

            st.error(str(e))
            st.stop()

        # Database is now the source of truth again.
        st.session_state.pop(
            draft_key,
            None,
        )

        st.success("Saved!")

        st.rerun()


with col2:

    if st.button(
        "Back to Home",
        icon=":material/undo:",
        use_container_width=True,
    ):

        # Throw away EVERYTHING that has not
        # been saved to SQLite.
        st.session_state.pop(
            draft_key,
            None,
        )

        st.switch_page(
            "pages/1_Home.py"
        )


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

            # Refresh the draft from the database.
            st.session_state.pop(
                draft_key,
                None,
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

            st.session_state.pop(
                draft_key,
                None,
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

            st.session_state.pop(
                draft_key,
                None,
            )

            st.success("All reset.")
            st.rerun()