import base64
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent


def img_to_data_url(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def inject_theme() -> None:
    st.markdown(
        """
<style>

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


hr {
    margin-top: 1.25rem;
    margin-bottom: 1.25rem;
}

</style>
""",
        unsafe_allow_html=True,
    )


def render_brand_header(centered: bool = False) -> None:
    logo_url = img_to_data_url("assets/logo_icon.png")

    justify = "center" if centered else "flex-start"

    st.markdown(
        f"""
<div class="brand-row" style="justify-content: {justify};">
<img src="{logo_url}" />
<span class="brand-name"><span class="brand-in">In</span><span class="brand-touch">Touch</span></span>
</div>
""",
        unsafe_allow_html=True,
    )