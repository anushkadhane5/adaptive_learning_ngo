import streamlit as st
import time
from datetime import timedelta
from database import cursor, conn

SUBJECTS = ["Mathematics", "English", "Science"]
TIME_SLOTS = ["4-5 PM", "5-6 PM", "6-7 PM"]

# =========================================================
# HELPERS
# =========================================================
def calculate_streak(dates):
    if not dates:
        return 0

    dates = sorted(set(dates), reverse=True)
    streak = 1
    for i in range(len(dates) - 1):
        if dates[i] - dates[i + 1] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


# =========================================================
# DASHBOARD PAGE
# =========================================================
def dashboard_page():

    # -----------------------------------------------------
    # CSS: ICONS, CHIPS, ANIMATIONS
    # -----------------------------------------------------
    st.markdown("""
    <style>
    .fade-in {
        animation: fadeIn 0.6s ease-in;
    }
    @keyframes fadeIn {
        from {opacity:0; transform:translateY(6px);}
        to {opacity:1; transform:translateY(0);}
    }

    .hover-card:hover {
        transform: translateY(-4px);
        transition: 0.2s ease;
        box-shadow: 0 16px 40px rgba(0,0,0,0.12);
    }

    /* SVG icons */
    .icon {
        width:18px;
        height:18px;
        vertical-align:middle;
        margin-right:6px;
        background-color: currentColor;
        mask-size: contain;
        mask-repeat: no-repeat;
        mask-position: center;
        -webkit-mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        -webkit-mask-position: center;
    }
    .icon-user {
        mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><circle cx='12' cy='8' r='4'/><path d='M4 20c0-4 4-6 8-6s8 2 8 6'/></svg>");
    }
    .icon-star {
        mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M12 2l3 7h7l-5.5 4.5L18 21l-6-3.5L6 21l1.5-7.5L2 9h7z'/></svg>");
    }
    .icon-alert {
        mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M12 2l10 20H2L12 2z'/></svg>");
    }
    .icon-edit {
        mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M3 21l3-1 12-12-2-2L4 18l-1 3z'/></svg>");
    }

    /* Subject chips */
    .subject-chip {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 6px;
        margin-top: 4px;
    }
    .chip-strong {
        background: rgba(34,197,94,0.15);
        color: #15803d;
    }
    .chip-weak {
        background: rgba(239,68,68,0.15);
        color: #b91c1c;
    }

    @media (prefers-color-scheme: dark) {
        .chip-strong {
            background: rgba(34,197,94,0.25);
            color: #4ade80;
        }
        .chip-weak {
            background: rgba(239,68,68,0.25);
            color: #f87171;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------
    # HERO
    # -----------------------------------------------------
    st.markdown(f"""
    <div class="card fade-in" style="background:linear-gradient(135deg,#6366f1,#4f46e5);color:white;">
        <h2>Welcome back, {st.session_state.user_name}</h2>
        <p>Track your learning, mentoring, and impact — all in one place.</p>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------
    # PROFILE FETCH
    # -----------------------------------------------------
    cursor.execute("""
        SELECT role, grade, time, strong_subjects, weak_subjects, teaches
        FROM profiles
        WHERE user_id = ?
    """, (st.session_state.user_id,))
    profile = cursor.fetchone()

    edit_mode = st.session_state.get("edit_profile", False)

    # =====================================================
    # PROFILE SETUP / EDIT
    # =====================================================
    if not profile or edit_mode:
        st.markdown("""
        <div class="card fade-in">
            <h3><span class="icon icon-edit"></span>Profile Setup</h3>
            <p>Update your learning details anytime.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("profile_form"):
            role = st.radio("Role", ["Student", "Teacher"], horizontal=True)
            grade = st.selectbox("Grade", [f"Grade {i}" for i in range(1, 11)])
            time_slot = st.selectbox("Available Time Slot", TIME_SLOTS)

            strong, weak, teaches = [], [], []

            if role == "Student":
                strong = st.multiselect("Strong Subjects", SUBJECTS)
                weak = st.multiselect("Weak Subjects", SUBJECTS)
            else:
                teaches = st.multiselect("Subjects You Teach", SUBJECTS)

            submitted = st.form_submit_button("Save Profile")

        if submitted:
            cursor.execute("DELETE FROM profiles WHERE user_id = ?", (st.session_state.user_id,))
            cursor.execute("""
                INSERT INTO profiles
                (user_id, role, grade, class, time, strong_subjects, weak_subjects, teaches)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                st.session_state.user_id,
                role,
                grade,
                int(grade.split()[-1]),
                time_slot,
                ",".join(strong),
                ",".join(weak),
                ",".join(teaches)
            ))
            conn.commit()

            st.session_state.edit_profile = False
            st.success("Profile saved successfully.")
            st.rerun()

        return

    # =====================================================
    # DASHBOARD VIEW
    # =====================================================
    role, grade, time_slot, strong, weak, teaches = profile
    strong_list = strong.split(",") if strong else []
    weak_list = weak.split(",") if weak else []
    teach_list = teaches.split(",") if teaches else []

    strong_html = "".join(
        f"<span class='subject-chip chip-strong'>{s}</span>"
        for s in (strong_list or teach_list)
    ) or "<span>—</span>"

    weak_html = "".join(
        f"<span class='subject-chip chip-weak'>{w}</span>"
        for w in weak_list
    ) or "<span>—</span>"

    # -----------------------------------------------------
    # PROFILE CARD
    # -----------------------------------------------------
    st.markdown(f"""
    <div class="card hover-card fade-in">
        <h3><span class="icon icon-user"></span>Your Profile</h3>
        <p><strong>Role:</strong> {role}</p>
        <p><strong>Grade:</strong> {grade}</p>
        <p><strong>Time Slot:</strong> {time_slot}</p>

        <p><span class="icon icon-star"></span><strong>Strong Subjects:</strong><br>{strong_html}</p>
        <p><span class="icon icon-alert"></span><strong>Weak Subjects:</strong><br>{weak_html}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Edit Profile"):
        st.session_state.edit_profile = True
        st.rerun()

    # -----------------------------------------------------
    # SESSION DATA
    # -----------------------------------------------------
    cursor.execute("""
        SELECT mentor, rating, session_date
        FROM ratings
        WHERE mentor = ? OR mentee = ?
    """, (st.session_state.user_name, st.session_state.user_name))

    rows = cursor.fetchall()
    session_dates = [r[2] for r in rows]

    streak = calculate_streak(session_dates)
    total_sessions = len(rows)
    avg_rating = round(sum(r[1] for r in rows) / total_sessions, 2) if total_sessions else "—"

    # -----------------------------------------------------
    # STATS
    # -----------------------------------------------------
    st.markdown("### Your Progress")

    c1, c2, c3, c4 = st.columns(4)
    time.sleep(0.2)

    c1.metric("Day Streak", streak)
    c2.metric("Sessions", total_sessions)
    c3.metric("Avg Rating", avg_rating)
    c4.metric("Consistency", f"{min(streak/30*100,100):.0f}%")

    st.progress(min(streak / 30, 1.0))

    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------
    st.divider()
    st.markdown("### Recent Sessions")

    if rows:
        history = [{
            "Partner": r[0],
            "Rating": r[1],
            "Date": r[2].strftime("%d %b %Y")
        } for r in rows[-10:][::-1]]

        st.dataframe(history, use_container_width=True)
    else:
        st.info("No sessions yet — start matchmaking to begin your journey.")
