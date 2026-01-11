import streamlit as st

def dashboard_page():
    st.title("Dashboard")

    st.write(f"Welcome, {st.session_state.user_name}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Go to Matchmaking"):
            st.session_state.page = "matchmaking"

    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "auth"
