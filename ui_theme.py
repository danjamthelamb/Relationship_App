import streamlit as st

def inject_theme():
    st.markdown("""
    <style>
    .stButton > button[kind="primary"] {
        background-color: #F96E5B;
        border-radius: 14px;
        font-weight: 700;
    }

    .stButton > button {
        border-radius: 12px;
    }

    .soft-card {
        background: rgba(121, 201, 197, 0.15);
        border: 1px solid rgba(63, 154, 174, 0.25);
        border-radius: 14px;
        padding: 1rem;
    }

    h1, h2, h3 {
        color: #3F9AAE;
    }
    </style>
    """, unsafe_allow_html=True)
