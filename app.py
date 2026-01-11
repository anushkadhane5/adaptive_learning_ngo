import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import time

# =========================================================
# CONFIGURATION
# =========================================================
st.set_page_config(page_title="Sahay: Precision Match", layout="wide")

# 1. SETUP SUPABASE
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"❌ Supabase Error: {e}")
    st.stop()

# 2. SETUP AI
ai_available = False
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        ai_available = True
    except: pass

# =========================================================
# 🧠 ROBUST MATCHING ALGORITHM (FIXED)
# =========================================================
def calculate_match_score(me, candidate):
    score = 0
    log = [] 

    # --- FIX: SAFE STRING HANDLING ---
    # Retrieve values and ensure they are strings (handle None/Null from DB)
    my_lang_str = me.get('languages') or ""
    cand_lang_str = candidate.get('languages') or ""
    
    my_subj_str = me.get('subjects') or ""
    cand_subj_str = candidate.get('subjects') or ""
    
    my_topic_str = me.get('specific_topics') or ""
    cand_topic_str = candidate.get('specific_topics') or ""
    # ---------------------------------

    # 1. LANGUAGE CHECK
    my_langs = set(x.strip() for x in my_lang_str.split(',') if x.strip())
    their_langs = set(x.strip() for x in cand_lang_str.split(',') if x.strip())
    
    # If no common language, score is 0
    if not my_langs.intersection(their_langs):
        return 0, ["No common language"]
    score += 20 

    # 2. SUBJECT MATCH
    my_subs = set(x.strip() for x in my_subj_str.split(',') if x.strip())
    their_subs = set(x.strip() for x in cand_subj_str.split(',') if x.strip())
    
    common_subs = my_subs.intersection(their_subs)
    if common_subs:
        score += 40
        log.append(f"Matches on: {', '.join(common_subs)}")
    else:
        return 0, ["No common subject"]

    # 3. GRADE LOGIC
    try:
        my_grade = int(me['grade'].split(" ")[1])
        their_grade = int(candidate['grade'].split(" ")[1])
        grade_diff = their_grade - my_grade

        if me['role'] == "Student":
            if grade_diff > 0: score += 30 # Senior is best
            elif grade_diff == 0: score += 15 # Peer is okay
        else:
            if grade_diff < 0: score += 30 # Teacher wants junior
    except:
        pass 

    # 4. TOPIC BONUS
    if my_topic_str and cand_topic_str:
        if my_topic_str.lower() in cand_topic_str.lower() or cand_topic_str.lower() in my_topic_str.lower():
            score += 25
            log.append("Exact topic match! (+25)")

    return score, log

def find_best_match(my_profile):
    opposite_role = "Teacher" if my_profile['role'] == "Student" else "Student"
    
    # Fetch candidates
    response = supabase.table("profiles").select("*")\
        .eq("role", opposite_role)\
        .eq("time_slot", my_profile['time_slot'])\
        .eq("status", "waiting")\
        .execute()
    
    candidates = response.data
    if not candidates: return None

    best_candidate = None
    highest_score = 0
    
    for person in candidates:
        score, reasons = calculate_match_score(my_profile, person)
        if score > highest_score:
            highest_score = score
            best_candidate = person

    return best_candidate

# =========================================================
# DATABASE HELPERS
# =========================================================
def save_profile(data):
    # Join lists to strings
    data['subjects'] = ", ".join(data['subjects'])
    data['languages'] = ",".join(data['languages'])
    try:
        supabase.table("profiles").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"DB Error: {e}")
        return False

def create_match_record(p1, p2):
    names = sorted([p1, p2])
    match_id = f"{names[0]}-{names[1]}"
    try:
        check = supabase.table("matches").select("*").eq("match_id", match_id).execute()
        if not check.data:
            supabase.table("matches").insert({
                "match_id": match_id, "mentor": p1, "mentee": p2
            }).execute()
            # Mark users as matched
            supabase.table("profiles").update({"status": "matched"}).eq("name", p1).execute()
            supabase.table("profiles").update({"status": "matched"}).eq("name", p2).execute()
    except: pass
    return match_id

# =========================================================
# APP UI
# =========================================================
if "stage" not in st.session_state: st.session_state.stage = 1
if "user_name" not in st.session_state: st.session_state.user_name = ""

st.title("Sahay: Precision Matchmaking 🎯")

# ---------------------------------------------------------
# STAGE 1: PROFILE
# ---------------------------------------------------------
if st.session_state.stage == 1:
    st.header("Step 1: Your Profile")
    
    col1, col2 = st.columns(2)
    with col1:
        role = st.radio("I am a:", ["Student", "Teacher"])
        name = st.text_input("Full Name")
        languages = st.multiselect("Languages I speak", ["English", "Hindi", "Marathi", "Tamil", "Bengali"])
    with col2:
        grade = st.selectbox("Grade", [f"Grade {i}" for i in range(5, 13)])
        time_slot = st.selectbox("Time Slot", ["4-5 PM", "5-6 PM", "6-7 PM"])
        
    st.subheader("Academic Details")
    c1, c2 = st.columns(2)
    with c1:
        subjects = st.multiselect("Subjects", ["Math", "Science", "English", "History", "Physics"])
    with c2:
        topics = st.text_input("Specific Topics? (e.g. Algebra, Thermodynamics)")

    if st.button("Find Match", type="primary"):
        if name and subjects and languages:
            profile = {
                "role": role, "name": name, "grade": grade, 
                "time_slot": time_slot, "subjects": subjects,
                "languages": languages, "specific_topics": topics,
                "status": "waiting"
            }
            if save_profile(profile):
                st.session_state.profile = profile
                st.session_state.user_name = name
                st.session_state.stage = 2
                st.rerun()
        else:
            st.warning("Please fill Name, Subjects & Languages")

# ---------------------------------------------------------
# STAGE 2: SEARCH
# ---------------------------------------------------------
elif st.session_state.stage == 2:
    st.header("Step 2: Analysis")
    st.info(f"Looking for the best match...")
    
    if st.button("🔄 Analyze & Match"):
        match = find_best_match(st.session_state.profile)
        
        if match:
            st.success(f"Match Found: **{match['name']}**")
            st.caption(f"Speaks: {match['languages']}")
            
            m_id = create_match_record(st.session_state.user_name, match['name'])
            st.session_state.match_id = m_id
            st.session_state.partner_name = match['name']
            
            time.sleep(1)
            st.session_state.stage = 3
            st.rerun()
        else:
            st.warning("No suitable match found yet. Please wait.")

# ---------------------------------------------------------
# STAGE 3: CHAT
# ---------------------------------------------------------
elif st.session_state.stage == 3:
    st.header(f"Session: {st.session_state.user_name} & {st.session_state.partner_name}")
    
    col_chat, col_tools = st.columns([2, 1])
    
    with col_chat:
        try:
            msgs = supabase.table("messages").select("*").eq("match_id", st.session_state.match_id).order("created_at").execute().data
        except: msgs = []

        with st.container(height=400):
            for m in msgs:
                is_me = m['sender'] == st.session_state.user_name
                with st.chat_message("user" if is_me else "assistant"):
                    st.write(f"**{m['sender']}**: {m['message']}")

        if prompt := st.chat_input("Message..."):
            supabase.table("messages").insert({
                "match_id": st.session_state.match_id, "sender": st.session_state.user_name, "message": prompt
            }).execute()
            st.rerun()
            
    with col_tools:
        if st.button("Refresh Chat"): st.rerun()
        
        # AI Hint (Stable)
        if st.button("🤖 AI Hint"):
            if ai_available:
                try:
                    context = " ".join([m['message'] for m in msgs[-3:]])
                    # Use Robust 1.5-Flash
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    resp = model.generate_content(f"Context: {context}. Give a hint.")
                    supabase.table("messages").insert({
                        "match_id": st.session_state.match_id, "sender": "AI Bot", "message": f"🤖 {resp.text}"
                    }).execute()
                    st.rerun()
                except Exception as e:
                    st.error("AI Busy/Error")
            else:
                st.error("AI Key Missing")

        if st.button("End Session"):
            st.session_state.stage = 1
            st.rerun()
