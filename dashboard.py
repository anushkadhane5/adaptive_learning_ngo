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
    # CSS (STRICTLY HTML ZONE)
    # -----------------------------------------------------
    st.markdown("""
    <style>
    .profile-card {
        display: flex;
        gap: 1.5rem;
        align-items: flex-start;
    }
    .avatar {
        width: 72px;
        height: 72px;
        border-radius: 50%;
        background: linear-gradient(135deg,#6366f1,#4f46e5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        flex-shrink: 0;
    }
    .avatar svg {
        width: 36px;
        height: 36px;
        fill: white;
    }
    .subject-section {
        margin-top: 0.75rem;
    }
    .subject-chip {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 4px 6px 0 0;
    }
    .chip-strong {
        background: rgba(34,197,94,0.18);
        color: #15803d;
    }
    .chip-weak {
        background: rgba(239,68,68,0.18);
        color: #b91c1c;
    }
    @media (prefers-color-scheme: dark) {
        .chip-strong { background: rgba(34,197,94,0.3); color:#4ade80; }
        .chip-weak { background: rgba(239,68,68,0.3); color:#f87171; }
    }
    </style>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------
    # HERO
    # -----------------------------------------------------
    st.markdown(f"""
    <div class="card" style="background:linear-gradient(135deg,#6366f1,#4f46e5);color:white;">
        <h2>Welcome back, {st.session_state.user_name}</h2>
        <p>Your learning journey at a glance.</p>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------
    # PROFILE FETCH
    # -----------------------------------------------------
    cursor.execute("""
        SELECT role, grade, time, strong_subjects, weak_subjects, teaches
        FROM profiles WHERE user_id = ?
    """, (st.session_state.user_id,))
    profile = cursor.fetchone()

    if not profile:
        st.warning("Please complete your profile first.")
        return

    role, grade, time_slot, strong, weak, teaches = profile

    strong_list = strong.split(",") if strong else (teaches.split(",") if teaches else [])
    weak_list = weak.split(",") if weak else []

    strong_html = "".join(
        f"<span class='subject-chip chip-strong'>{s}</span>" for s in strong_list
    ) or "<span>—</span>"

    weak_html = "".join(
        f"<span class='subject-chip chip-weak'>{w}</span>" for w in weak_list
    ) or "<span>—</span>"

    # -----------------------------------------------------
    # PROFILE CARD (SEALED HTML)
    # -----------------------------------------------------
    st.markdown(
        f"""
        <div class="card">
            <div class="profile-card">
                <div class="avatar">
                    <svg viewBox="0 0 24 24">
                        <circle cx="12" cy="8" r="4"/>
                        <path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>
                    </svg>
                </div>

                <div>
                    <h3>Your Profile</h3>
                    <p><strong>Role:</strong> {role}</p>
                    <p><strong>Grade:</strong> {grade}</p>
                    <p><strong>Time Slot:</strong> {time_slot}</p>

                    <div class="subject-section">
                        <strong>Strong Subjects</strong><br>
                        {strong_html}
                    </div>

                    <div class="subject-section">
                        <strong>Weak Subjects</strong><br>
                        {weak_html}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("Edit Profile"):
        st.session_state.edit_profile = True
        st.rerun()
