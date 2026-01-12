import streamlit as st
from database import cursor

def admin_page():
    st.title("Admin Dashboard")
    st.caption("Overview of users, roles, and platform activity")
    st.divider()

    # =================================================
    # TOTAL SIGNUPS
    # =================================================
    st.subheader("Platform Statistics")

    cursor.execute("SELECT COUNT(*) FROM auth_users")
    total_users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) 
        FROM profiles 
        WHERE role='Student'
    """)
    students = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) 
        FROM profiles 
        WHERE role='Teacher'
    """)
    teachers = cursor.fetchone()[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Signups", total_users)
    c2.metric("Students", students)
    c3.metric("Teachers", teachers)

    st.divider()

    # =================================================
    # REGISTERED USERS
    # =================================================
    st.subheader("Registered Users")

    cursor.execute("""
        SELECT 
            a.id,
            a.name,
            a.email,
            p.role,
            p.grade,
            p.class_level,
            p.time,
            p.strong_subjects,
            p.weak_subjects,
            p.teaches
        FROM auth_users a
        LEFT JOIN profiles p ON a.id = p.user_id
        ORDER BY a.id DESC
    """)

    users = cursor.fetchall()

    if not users:
        st.info("No users registered yet.")
        return

    for u in users:
        (
            user_id,
            name,
            email,
            role,
            grade,
            class_level,
            time_slot,
            strong,
            weak,
            teaches
        ) = u

        with st.expander(f"{name}  |  {email}"):
            st.write(f"**User ID:** {user_id}")
            st.write(f"**Role:** {role or 'Not set'}")
            st.write(f"**Grade:** {grade or '—'}")
            st.write(f"**Class Level:** {class_level or '—'}")
            st.write(f"**Time Slot:** {time_slot or '—'}")
            st.write(f"**Strong Subjects:** {strong or '—'}")
            st.write(f"**Weak Subjects:** {weak or '—'}")
            st.write(f"**Teaches:** {teaches or '—'}")

    st.divider()

    # =================================================
    # MENTOR LEADERBOARD
    # =================================================
    st.subheader("Mentor Leaderboard")

    cursor.execute("""
        SELECT mentor, AVG(rating) AS avg_rating, COUNT(*) AS total_sessions
        FROM ratings
        GROUP BY mentor
        ORDER BY avg_rating DESC
    """)

    ratings = cursor.fetchall()

    if not ratings:
        st.info("No ratings yet.")
    else:
        for i, r in enumerate(ratings, 1):
            st.write(
                f"{i}. **{r[0]}** — ⭐ {round(r[1], 2)} "
                f"({r[2]} sessions)"
            )
