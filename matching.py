# matching.py
import streamlit as st

# -------------------------------------------------
# SAMPLE USERS (replace with DB later)
# -------------------------------------------------
USERS = [
    {
        "name": "Aarav",
        "role": "Mentor",
        "grade": "10",
        "time": "5-6 PM",
        "strong": ["Mathematics"],
        "weak": []
    },
    {
        "name": "Diya",
        "role": "Student",
        "grade": "10",
        "time": "5-6 PM",
        "strong": [],
        "weak": ["Mathematics"]
    },
    {
        "name": "Kabir",
        "role": "Mentor",
        "grade": "9",
        "time": "4-5 PM",
        "strong": ["Science"],
        "weak": []
    },
    {
        "name": "Ananya",
        "role": "Student",
        "grade": "11",
        "time": "6-7 PM",
        "strong": [],
        "weak": ["English"]
    },
    {
        "name": "Riya",
        "role": "Mentor",
        "grade": "11",
        "time": "6-7 PM",
        "strong": ["English"],
        "weak": []
    }
]

SUBJECTS = ["Mathematics", "English", "Science"]
TIME_SLOTS = ["4-5 PM", "5-6 PM", "6-7 PM"]

# -------------------------------------------------
# CORE MATCH SCORE FUNCTION
# -------------------------------------------------
def calculate_compatibility(mentor, mentee):
    score = 0
    reasons = []

    # 1️⃣ Weak ↔ Strong subject match (MOST IMPORTANT)
    for subject in mentee["weak"]:
        if subject in mentor["strong"]:
            score += 50
            reasons.append(f"Strong in {subject} ↔ Weak in {subject}")

    # 2️⃣ Same grade
    if mentor["grade"] == mentee["grade"]:
        score += 25
        reasons.append("Same grade")

    # 3️⃣ Same time slot
    if mentor["time"] == mentee["time"]:
        score += 15
        reasons.append("Same time slot")

    # 4️⃣ Extra subject overlap
    common = set(mentor["strong"]) & set(mentee["weak"])
    if common:
        score += 10

    return score, reasons


# -------------------------------------------------
# MATCHMAKING ENGINE
# -------------------------------------------------
def find_matches(current_user):
    matches = []

    for other in USERS:
        # Do not match with self
        if other["name"] == current_user["name"]:
            continue

        # Opposite roles only
        if current_user["role"] == other["role"]:
            continue

        # Define mentor & mentee
        mentor = other if other["role"] == "Mentor" else current_user
        mentee = current_user if current_user["role"] == "Mentor" else other

        score, reasons = calculate_compatibility(mentor, mentee)

        if score >= 40:
            matches.append({
                "mentor": mentor["name"],
                "mentee": mentee["name"],
                "score": score,
                "reasons": reasons
            })

    # Highest score first
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


# -------------------------------------------------
# STREAMLIT PAGE
# -------------------------------------------------
def matchmaking_page():

    st.markdown("""
    <div class="card">
        <h2>Peer Learning Matchmaking</h2>
        <p>We match learners with complementary strengths, same grade and time.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("profile_form"):
        name = st.text_input("Your Name")
        role = st.radio("Role", ["Student", "Mentor"], horizontal=True)
        grade = st.selectbox("Grade", ["9", "10", "11", "12"])
        time = st.selectbox("Available Time Slot", TIME_SLOTS)

        if role == "Student":
            weak = st.multiselect("Weak Subjects", SUBJECTS)
            strong = []
        else:
            strong = st.multiselect("Strong Subjects", SUBJECTS)
            weak = []

        submitted = st.form_submit_button("Find Compatible Matches")

    if submitted:
        user = {
            "name": name,
            "role": role,
            "grade": grade,
            "time": time,
            "strong": strong,
            "weak": weak
        }

        results = find_matches(user)

        if results:
            st.success(f"Found {len(results)} compatible match(es)")

            for r in results:
                st.markdown(f"""
                <div class="card">
                    <h4>Compatibility Score: {r['score']}%</h4>
                    <strong>Mentor:</strong> {r['mentor']}<br>
                    <strong>Mentee:</strong> {r['mentee']}<br>
                    <strong>Why this match?</strong>
                    <ul>
                        {''.join(f"<li>{reason}</li>" for reason in r['reasons'])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No compatible matches found yet.")
