import streamlit as st
from groq import Groq
from supabase import create_client, Client
import time
from datetime import datetime

# =========================================================
# 1. APP CONFIGURATION & STYLING
# =========================================================
st.set_page_config(
    page_title="Sahay: Peer Learning Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS FOR "GREAT UI" ---
st.markdown("""
<style>
    /* 1. Main Background & Text Color */
    .stApp {
        background-color: #f8f9fa;
        color: #000000; /* Force black text */
    }
    
    /* 2. Fix Input Labels (They turn white in dark mode) */
    .stMarkdown, .stSelectbox label, .stTextInput label {
        color: #31333F !important;
    }

    /* 3. Header Styling */
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* 4. Chat Bubbles */
    .chat-bubble-me {
        background-color: #dcf8c6;
        color: #000;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0 5px auto; /* Push to right */
        max-width: 70%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        display: block;
    }
    
    .chat-bubble-partner {
        background-color: #ffffff;
        color: #000;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        margin: 5px 0;
        max-width: 70%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        display: block;
    }
    
    .chat-bubble-ai {
        background-color: #e0e7ff;
        border: 1px solid #6366f1;
        color: #312e81;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        max-width: 80%;
        font-style: italic;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. BACKEND CONNECTIONS
# =========================================================
# Supabase Setup
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("❌ Database Connection Failed. Please check Streamlit Secrets.")
    st.stop()

# Groq AI Setup
ai_client = None
if "GROQ_API_KEY" in st.secrets:
    try:
        ai_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: pass

# =========================================================
# 3. HELPER FUNCTIONS (LOGIC LAYER)
# =========================================================

def upload_file(file_obj, match_id):
    """Uploads file to Supabase Storage 'chat-files' bucket"""
    try:
        # Unique Filename: match_id/timestamp_clean_name
        clean_name = file_obj.name.replace(" ", "_")
        file_path = f"{match_id}/{int(time.time())}_{clean_name}"
        bucket = "chat-files"
        
        supabase.storage.from_(bucket).upload(
            file_path, 
            file_obj.getvalue(),
            {"content-type": file_obj.type}
        )
        return supabase.storage.from_(bucket).get_public_url(file_path)
    except Exception as e:
        st.toast(f"Upload Failed: {str(e)}")
        return None

def calculate_match_score(me, candidate):
    """The 'Brain' of the Matchmaking System"""
    score = 0
    
    # Safe Data Extraction
    my_lang = set(x.strip() for x in (me.get('languages') or "").split(',') if x.strip())
    their_lang = set(x.strip() for x in (candidate.get('languages') or "").split(',') if x.strip())
    
    # 1. Language Barrier (CRITICAL)
    if not my_lang.intersection(their_lang): return 0
    score += 20 

    # 2. Subject Match
    my_subs = set(x.strip() for x in (me.get('subjects') or "").split(',') if x.strip())
    their_subs = set(x.strip() for x in (candidate.get('subjects') or "").split(',') if x.strip())
    if my_subs.intersection(their_subs): score += 40
    else: return 0 # Must share at least one subject

    # 3. Grade Logic (Seniority Bonus)
    try:
        my_g = int(me['grade'].split(" ")[1])
        their_g = int(candidate['grade'].split(" ")[1])
        diff = their_g - my_g
        
        if me['role'] == "Student":
            if diff > 0: score += 30      # Senior Mentor is best
            elif diff == 0: score += 15   # Peer is okay
        else:
            if diff < 0: score += 30      # Teacher wants junior student
    except: pass 

    # 4. Topic Specific Bonus
    my_topic = (me.get('specific_topics') or "").lower()
    their_topic = (candidate.get('specific_topics') or "").lower()
    if my_topic and their_topic:
        if my_topic in their_topic or their_topic in my_topic:
            score += 25

    return score

def find_best_match(my_profile):
    opposite = "Teacher" if my_profile['role'] == "Student" else "Student"
    
    # Fetch Waitlist
    response = supabase.table("profiles").select("*")\
        .eq("role", opposite)\
        .eq("time_slot", my_profile['time_slot'])\
        .eq("status", "waiting")\
        .execute()
    
    candidates = response.data
    if not candidates: return None

    # Score Everyone
    best = None
    high_score = 0
    for p in candidates:
        s = calculate_match_score(my_profile, p)
        if s > high_score:
            high_score = s
            best = p
    return best

def save_profile(data):
    # Format lists for DB
    data['subjects'] = ", ".join(data['subjects'])
    data['languages'] = ",".join(data['languages'])
    try:
        supabase.table("profiles").insert(data).execute()
        return True
    except: return False

def create_match_record(p1, p2):
    # Ensure ID is always Alphabetical (Alice-Bob, never Bob-Alice)
    names = sorted([p1, p2])
    m_id = f"{names[0]}-{names[1]}"
    try:
        check = supabase.table("matches").select("*").eq("match_id", m_id).execute()
        if not check.data:
            supabase.table("matches").insert({ "match_id": m_id, "mentor": p1, "mentee": p2 }).execute()
            # Mark as matched
            supabase.table("profiles").update({"status": "matched"}).eq("name", p1).execute()
            supabase.table("profiles").update({"status": "matched"}).eq("name", p2).execute()
    except: pass
    return m_id

# =========================================================
# 4. MAIN APP LOGIC
# =========================================================

# Session State Init
if "stage" not in st.session_state: st.session_state.stage = 1
if "user_name" not in st.session_state: st.session_state.user_name = ""

# --- HEADER ---
st.markdown("<h1>🎓 Sahay <span style='font-size: 20px; color: #666;'>| Peer Learning Ecosystem</span></h1>", unsafe_allow_html=True)

# -------------------------------------------
# STAGE 1: REGISTRATION & PROFILE
# -------------------------------------------
if st.session_state.stage == 1:
    with st.container():
        st.markdown("### 👋 Join a Session")
        st.write("Connect with a peer or mentor who speaks your language.")
        
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                role = st.radio("I want to:", ["Learn (Student)", "Teach (Mentor)"], horizontal=True)
                # Map back to simple strings
                role_str = "Student" if "Learn" in role else "Teacher"
                
                name = st.text_input("My Full Name", placeholder="e.g. Rahul Sharma")
                languages = st.multiselect("Languages I speak", ["English", "Hindi", "Marathi", "Tamil", "Bengali", "Telugu"])
            
            with col2:
                grade = st.selectbox("Current Grade", [f"Grade {i}" for i in range(5, 13)])
                time_slot = st.selectbox("Preferred Time", ["4-5 PM", "5-6 PM", "6-7 PM"])
                
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                subjects = st.multiselect("Subjects", ["Mathematics", "Science", "English", "History", "Physics", "Chemistry"])
            with c2:
                topics = st.text_input("Specific Topic Focus", placeholder="e.g. Algebra, Thermodynamics, Grammar")

            submitted = st.form_submit_button("Find My Match 🚀", type="primary", use_container_width=True)

            if submitted:
                if name and subjects and languages:
                    profile = {
                        "role": role_str, "name": name, "grade": grade, 
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
                    st.error("⚠️ Please fill in Name, Languages, and Subjects.")

# -------------------------------------------
# STAGE 2: MATCHMAKING
# -------------------------------------------
elif st.session_state.stage == 2:
    st.markdown("### 🔍 Analyzing Peers...")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.info(f"Looking for the best match for **{st.session_state.user_name}** in the **{st.session_state.profile['time_slot']}** slot.")
        
        # Auto-refresh button centered
        if st.button("🔄 Click to Search Now", type="primary", use_container_width=True):
            with st.spinner("Running compatibility algorithm..."):
                time.sleep(1) # Fake delay for UX
                match = find_best_match(st.session_state.profile)
                
            if match:
                st.balloons()
                st.success(f"🎉 Match Found! You are connected with **{match['name']}**")
                
                # Create Session
                m_id = create_match_record(st.session_state.user_name, match['name'])
                st.session_state.match_id = m_id
                st.session_state.partner_name = match['name']
                
                time.sleep(1.5)
                st.session_state.stage = 3
                st.rerun()
            else:
                st.warning("⏳ No perfect match yet. Please wait or tell your friend to join!")

# -------------------------------------------
# STAGE 3: LIVE SESSION ROOM
# -------------------------------------------
elif st.session_state.stage == 3:
    # Top Bar
    st.markdown(f"""
    <div style='background: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;'>
        <h3 style='margin:0;'>🔴 Live: {st.session_state.user_name} & {st.session_state.partner_name}</h3>
        <span style='background: #dcf8c6; padding: 5px 10px; border-radius: 20px; font-size: 0.9em;'>Connected</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_chat, col_tools = st.columns([3, 1])
    
    # --- LEFT: CHAT INTERFACE ---
    with col_chat:
        # Load Messages
        try:
            msgs = supabase.table("messages").select("*").eq("match_id", st.session_state.match_id).order("created_at").execute().data
        except: msgs = []

        # Chat Display Container
        with st.container(height=500, border=True):
            if not msgs:
                st.caption("Start the conversation by saying hello! 👋")
            
            for m in msgs:
                # Determine Style
                if m['sender'] == st.session_state.user_name:
                    # My Message
                    st.markdown(f"<div class='chat-bubble-me'>{m['message']}</div>", unsafe_allow_html=True)
                    if m.get('file_url'):
                        st.markdown(f"<div style='float:right; clear:both; margin-bottom:10px;'><a href='{m['file_url']}' target='_blank'>📎 View Shared File</a></div>", unsafe_allow_html=True)
                elif m['sender'] == "AI Bot":
                    # AI Message
                    st.markdown(f"<div class='chat-bubble-ai'>🤖 <b>Sahay AI:</b> {m['message'].replace('🤖 ', '')}</div>", unsafe_allow_html=True)
                else:
                    # Partner Message
                    st.markdown(f"<div class='chat-bubble-partner'><b>{m['sender']}:</b> {m['message']}</div>", unsafe_allow_html=True)
                    if m.get('file_url'):
                        st.markdown(f"<div style='float:left; clear:both; margin-bottom:10px;'><a href='{m['file_url']}' target='_blank'>📎 View Shared File</a></div>", unsafe_allow_html=True)

        # Message Input
        with st.form("chat_input", clear_on_submit=True):
            col_in, col_btn = st.columns([5, 1])
            with col_in:
                msg_txt = st.text_input("Type a message...", label_visibility="collapsed")
            with col_btn:
                sent = st.form_submit_button("Send ➤")
            
            if sent and msg_txt:
                supabase.table("messages").insert({
                    "match_id": st.session_state.match_id, "sender": st.session_state.user_name, "message": msg_txt
                }).execute()
                st.rerun()

    # --- RIGHT: TOOLS PANEL ---
    with col_tools:
        with st.container(border=True):
            st.markdown("#### 🛠️ Tools")
            
            if st.button("🔄 Refresh Chat", use_container_width=True):
                st.rerun()
            
            st.markdown("---")
            st.markdown("**📂 Share File**")
            up_file = st.file_uploader("Upload Image/PDF", key="u", label_visibility="collapsed")
            if up_file and st.button("Upload & Send", use_container_width=True):
                with st.spinner("Uploading..."):
                    url = upload_file(up_file, st.session_state.match_id)
                    if url:
                        supabase.table("messages").insert({
                            "match_id": st.session_state.match_id,
                            "sender": st.session_state.user_name,
                            "message": "📄 *Sent a file*",
                            "file_url": url,
                            "file_type": up_file.type
                        }).execute()
                        st.success("Sent!")
                        st.rerun()

            st.markdown("---")
            st.markdown("**🤖 AI Tutor**")
            if st.button("✨ Ask Llama 3 for Hint", type="primary", use_container_width=True):
                if ai_client:
                    try:
                        # Context: Last 3 messages
                        context_msgs = [m['message'] for m in msgs[-3:] if m['message'] and "Sent a file" not in m['message']]
                        context = " ".join(context_msgs) if context_msgs else "No context."
                        
                        # Call Groq
                        completion = ai_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "You are a helpful academic tutor. Provide a short, encouraging hint (max 1 sentence) based on the students' conversation."},
                                {"role": "user", "content": f"Conversation Context: {context}"}
                            ],
                            temperature=0.7, max_tokens=100
                        )
                        reply = completion.choices[0].message.content
                        
                        supabase.table("messages").insert({
                            "match_id": st.session_state.match_id, "sender": "AI Bot", "message": f"🤖 {reply}"
                        }).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI Error: {e}")
                else:
                    st.error("AI Key Missing")

            st.markdown("---")
            if st.button("🛑 End Session", type="secondary", use_container_width=True):
                st.session_state.stage = 1
                st.rerun()
