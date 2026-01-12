import streamlit as st
from practice_data import PRACTICE_DATA
from streak import update_streak
from database import cursor


def practice_page():

    # -------------------------------------------------
    # AUTH GUARD (CORRECT WAY)
    # -------------------------------------------------
    if not st.session_state.get("user_id"):
        st.warning("Please log in to access practice.")
        return

    # -------------------------------------------------
    # FETCH PROFILE FROM DB
    # -------------------------------------------------
    cursor.execute("""
        SELECT role, class
        FROM profiles
        WHERE user_id = ?
    """, (st.session_state.user_id,))
    profile = cursor.fetchone()

    if not profile:
        st.warning("Please complete your profile first.")
        return

    role, user_class = profile

    st.subheader("Practice Questions")

    # -------------------------------------------------
    # CLASS HANDLING
    # -------------------------------------------------
    if role == "Student":
        st.info(f"Class: {user_class}")
    else:
        user_class = st.selectbox(
            "Select Class",
            sorted(PRACTICE_DATA.keys())
        )

    if user_class not in PRACTICE_DATA:
        st.warning("Practice not available for this class yet.")
        return

    # -------------------------------------------------
    # SUBJECT
    # -------------------------------------------------
    subject = st.selectbox(
        "Select Subject",
        list(PRACTICE_DATA[user_class].keys())
    )

    # -------------------------------------------------
    # TOPIC
    # -------------------------------------------------
    topic = st.selectbox(
        "Select Topic",
        list(PRACTICE_DATA[user_class][subject].keys())
    )

    questions = PRACTICE_DATA[user_class][subject][topic]

    st.divider()
    st.markdown("### Answer the following questions")

    # -------------------------------------------------
    # QUESTIONS
    # -------------------------------------------------
    user_answers = []

    for i, q in enumerate(questions):
        ans = st.radio(
            f"Q{i + 1}. {q['q']}",
            q["options"],
            key=f"practice_q_{i}"
        )
        user_answers.append(ans)

    # -------------------------------------------------
    # SUBMIT
    # -------------------------------------------------
    if st.button("Submit Practice"):
        score = 0

        for i, q in enumerate(questions):
            if user_answers[i] == q["answer"]:
                score += 1

        st.success(f"Your Score: {score} / {len(questions)}")

        update_streak()

        if score == len(questions):
            st.balloons()
