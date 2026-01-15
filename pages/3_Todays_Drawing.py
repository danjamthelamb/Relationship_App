import streamlit as st
from db import draw_friend_and_family, get_counts, init_db

st.set_page_config(page_title="Draw Today", page_icon="🎲", layout="centered")
init_db()

st.title("Draw names for today")

counts = get_counts()
if counts["Friend"]["total"] == 0 or counts["Family"]["total"] == 0:
    st.warning("You need at least **1 Friend** and **1 Family** person before drawing.")
    st.page_link("pages/2_Edit.py", label="Add people now", use_container_width=True)
    st.stop()

st.caption(
    "Rule: each relationship list is siloed — names are drawn once per cycle, then that list resets."
)

if "last_draw" not in st.session_state:
    st.session_state["last_draw"] = None

col1, col2 = st.columns(2)
with col1:
    if st.button("Draw now", use_container_width=True):
        st.session_state["last_draw"] = draw_friend_and_family()

with col2:
    st.page_link("pages/1_Home.py", label="⬅️ Back to Home", use_container_width=True)

st.divider()

result = st.session_state["last_draw"]
if result:
    st.subheader("Text these people:")
    st.markdown(f"### Friend: **{result.friend}**")
    st.markdown(f"### Family: **{result.family}**")

    counts2 = get_counts()
    st.caption(
        f"Remaining this cycle — Friends: {counts2['Friend']['remaining']} | Family: {counts2['Family']['remaining']}"
    )
else:
    st.info("Click **Draw now** to pick one Friend and one Family member.")
