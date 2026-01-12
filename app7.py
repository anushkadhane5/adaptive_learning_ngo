import streamlit as st
from datetime import date

# ---- IMPORT PAGES ----
from materials import materials_page
from practice import practice_page
from admin import admin_page
from auth import auth_page
from dashboard import dashboard_page

# ---- DATABASE ----
from database import init_db, cursor, conn

# =========================================================
# INIT DATABASE
# =========================================================
init_db()

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Sahay | Peer Learning Matchmaking",
    layout="wide"
)

# =========================================================
# GLOBAL UI STYLES
# =========================================================
st.markdown("""
<style>

/* Typography */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(135deg, #f5f7fa, #eef1f5);
}

@media (prefers-color-scheme: dark) {
    .stApp {
        background: linear-gradient(135deg, #121212, #1c1c1c);
    }
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
    border-right: 1px solid rgba(200,200,200,0.3);
}

@media (prefers-color-scheme: dark) {
    section[data-testid="stSidebar"] {
        background: rgba(20,20,20,0.9);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
}

/* Sidebar header */
.sidebar-header {
    padding: 1.2rem;
    border-radius: 16px;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: white;
    margin-bottom: 1rem;
}

/* Navigation button */
.nav-btn {
    padding: 0.65rem 0.9rem;
    margin-bottom: 0.4rem;
    border-radius: 12px;
    font-weight: 500;
    transition: 0.2s ease;
}

.nav-btn:hover {
    background: rgba(99,102,241,0.12);
}

.nav-active {
    background: rgba(99,102,241,0.2);
    border-left: 4px solid #4f46e5;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.92);
    border-radius: 18px;
    padding: 1.6rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.06);
    margin-bottom: 1.6rem;
}

@media (prefers-color-scheme: dark) {
    .card {
        background: rgba(30,30,30,0.9);
        box-shadow: 0 12px 30px rgba(0,0,0,0.35);
    }
}

/* Buttons */
.stButton > button {
    border-radius: 12px;
    padding: 0.6rem 1.2rem;
    font-weight: 500;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE INIT
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "stage" not in st.session_state:
    st.session_state.stage = 1
if "profile" not in st.session_state:
    st.session_state.profile = {}
if "current_match" not in st.session_state:
    st.session_state.current_match = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

SUBJECTS = ["Mathematics", "English", "Science"]

# =========================================================
# AUTH GATE
# =========================================================
if not st.session_state.logged_in:
    auth_page()
    st.stop()

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:

    st.markdown(f"""
    <div class="sidebar-header">
        <h3 style="margin:0;">Sahay</h3>
        <p style="margin:0;font-size:0.85rem;opacity:0.9;">
            {st.session_state.user_name}
        </p>
    </div>
    """, unsafe_allow_html=True)

    nav_items = {
        "Dashboard": "📊",
        "Matchmaking": "🔗",
        "Learning Materials": "📚",
        "Practice": "✏️",
        "Admin": "⚙️"
    }

    for page_name, icon in nav_items.items():
        active = "nav-active" if st.session_state.page == page_name else ""
        st.markdown(
            f"<div class='nav-btn {active}'>{icon} {page_name}</div>",
            unsafe_allow_html=True
        )
        if st.button(page_name, key=f"nav_{page_name}", use_container_width=True):
            st.session_state.page = page_name
            st.rerun()

    st.divider()

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = ""
        st.session_state.stage = 1
        st.session_state.profile = {}
        st.session_state.current_match = None
        st.rerun()

page = st.session_state.page

# =========================================================
# DATABASE LOADERS
# =========================================================
def load_users():
    cursor.execute("""
        SELECT 
            a.name,
            p.role,
            p.grade,
            p.class,
            p.time,
            p.strong_subjects,
            p.weak_subjects,
            p.teaches
        FROM profiles p
        JOIN auth_users a ON a.id = p.user_id
    """)
    rows = cursor.fetchall()

    mentors = []
    for r in rows:
        mentors.append({
            "name": r[0],
            "role": r[1],
            "grade": r[2],
            "class": r[3],
            "time": r[4],
            "strong_subjects": r[5].split(",") if r[5] else [],
            "weak_subjects": r[6].split(",") if r[6] else [],
            "teaches": r[7].split(",") if r[7] else []
        })
    return mentors

# =========================================================
# MATCHING LOGIC
# =========================================================
def calculate_match_score(mentee, mentor):
    score = 0
    reasons = []

    for weak in mentee.get("weak_subjects", []):
        if weak in mentor.get("teaches", mentor.get("strong_subjects", [])):
            score += 50
            reasons.append(f"{weak} match")

    if mentor["time"] == mentee["time"]:
        score += 20
        reasons.append("Same time")

    if mentor["grade"] == mentee["grade"]:
        score += 10
        reasons.append("Same grade")

    return score, reasons


def find_best_mentor(mentee, mentors):
    best, best_score, best_reasons = None, -1, []

    for mentor in mentors:
        if mentor["name"] == mentee["name"]:
            continue
        score, reasons = calculate_match_score(mentee, mentor)
        if score > best_score:
            best, best_score, best_reasons = mentor, score, reasons

    return (best, best_score, best_reasons) if best_score >= 15 else (None, 0, [])

# =========================================================
# PAGE ROUTING
# =========================================================
if page == "Dashboard":
    dashboard_page()

elif page == "Matchmaking":
    st.markdown("""
    <div class="card">
        <h2>Peer Learning Matchmaking</h2>
        <p>Find the best mentor based on compatibility.</p>
    </div>
    """, unsafe_allow_html=True)

    mentors = load_users()

    if st.session_state.stage == 1:
        with st.form("profile_form"):
            role = st.radio("Role", ["Student", "Teacher"], horizontal=True)
            grade = st.selectbox("Grade", [f"Grade {i}" for i in range(1, 11)])
            time_slot = st.selectbox("Time Slot", ["4-5 PM", "5-6 PM", "6-7 PM"])

            strong, weak, teaches = [], [], []
            if role == "Student":
                strong = st.multiselect("Strong Subjects", SUBJECTS)
                weak = st.multiselect("Weak Subjects", SUBJECTS)
            else:
                teaches = st.multiselect("Subjects You Teach", SUBJECTS)

            if st.form_submit_button("Save Profile & Find Match"):
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

                st.session_state.profile = {
                    "role": role,
                    "grade": grade,
                    "class": int(grade.split()[-1]),
                    "time": time_slot,
                    "strong_subjects": strong,
                    "weak_subjects": weak,
                    "teaches": teaches
                }
                st.session_state.stage = 2
                st.rerun()

    elif st.session_state.stage == 2:
        mentee = {"name": st.session_state.user_name, **st.session_state.profile}
        mentor, score, reasons = find_best_mentor(mentee, mentors)

        if mentor:
            st.markdown(f"""
            <div class="card">
                <h3>Match Found</h3>
                <p><strong>Mentor:</strong> {mentor['name']}</p>
                <p><strong>Score:</strong> {score}</p>
                <p>{", ".join(reasons)}</p>
            </div>
            """, unsafe_allow_html=True)

            st.session_state.current_match = {
                "mentor": mentor["name"],
                "mentee": mentee["name"]
            }

            if st.button("Start Session", type="primary"):
                st.session_state.stage = 3
                st.rerun()

    elif st.session_state.stage == 3:
        st.text_area("Session Notes", height=220)
        if st.button("End Session"):
            st.session_state.stage = 4
            st.rerun()

    elif st.session_state.stage == 4:
        rating = st.slider("Rate Session", 1, 5)
        if st.button("Submit Rating"):
            cursor.execute("""
                INSERT INTO ratings (mentor, mentee, rating, session_date)
                VALUES (?, ?, ?, ?)
            """, (
                st.session_state.current_match["mentor"],
                st.session_state.current_match["mentee"],
                rating,
                date.today()
            ))
            conn.commit()
            st.session_state.stage = 1
            st.success("Feedback saved")

elif page == "Learning Materials":
    materials_page()

elif page == "Practice":
    practice_page()

elif page == "Admin":
    admin_key = st.text_input("Admin Access Key", type="password")
    if admin_key == "ngo-admin-123":
        admin_page()
    else:
        st.warning("Unauthorized access")
