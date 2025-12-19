import streamlit as st

def show_rating_ui():
    st.set_page_config(page_title="Rating", page_icon="⭐")

    st.title("Rate your mentoring experience ⭐")

    if "rating" not in st.session_state:
        st.session_state.rating = 0

    st.write("Click on the stars to rate (1–5):")

    cols = st.columns(5)

    for i in range(5):
        star = "⭐" if i < st.session_state.rating else "☆"
        with cols[i]:
            if st.button(star, key=f"star_{i+1}"):
                st.session_state.rating = i + 1

    if st.button("Submit Rating"):
        if st.session_state.rating > 0:
            points = st.session_state.rating * 10
            st.success(
                f"Thank you! Rating: {st.session_state.rating}/5 ⭐ | "
                f"Mentor earned {points} points 🎯"
            )
        else:
            st.warning("Please select a rating before submitting.")
