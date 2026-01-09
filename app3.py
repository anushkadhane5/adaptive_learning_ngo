import streamlit as st
from ratings import show_rating_ui
from matching import find_matches
import time

st.markdown("""
<style>
/* =========================
   DROPDOWN BOX (CLOSED)
========================= */
div[data-baseweb="select"] > div {
    background-color: #0b3c5d !important;  /* Dark blue */
    border-radius: 10px;
    border: 1px solid #1e5aa8;
}

/* Selected value text */
div[data-baseweb="select"] span {
    color: white !important;
    font-weight: 500;
}

/* Dropdown arrow */
div[data-baseweb="select"] svg {
    fill: white !important;
}

/* =========================
   DROPDOWN MENU (OPEN)
========================= */
div[data-baseweb="menu"] {
    background-color: #0b3c5d !important;
    border-radius: 10px;
    border: 1px solid #1e5aa8;
}

/* Options text */
div[data-baseweb="option"] {
    color: white !important;
    background-color: #0b3c5d !important;
}

/* Hovered option */
div[data-baseweb="option"]:hover {
    background-color: #1e5aa8 !important;
    color: white !important;
}

/* Selected option */
div[data-baseweb="option"][aria-selected="true"] {
    background-color: #2563eb !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)
