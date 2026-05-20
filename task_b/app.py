import streamlit as st
import requests
import uuid
import os

API_URL = os.getenv("API_URL", "http://localhost:8002")

st.set_page_config(
    page_title="Twinn Recommend",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main {
        background: linear-gradient(160deg, #fdfcfb 0%, #f5f0eb 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d2d2d 0%, #1a1a1a 100%);
        border-right: 1px solid #ffffff10;
    }

    button[data-testid="stSidebarNavToggle"] {
        color: #d4a574 !important;
        background: #2d2d2d !important;
        border: 1px solid #d4a57440 !important;
        border-radius: 8px !important;
    }

    button[data-testid="collapsedControl"] {
        color: #d4a574 !important;
        background: #2d2d2d !important;
        border: 1px solid #d4a57440 !important;
        border-radius: 8px !important;
    }

    .hero {
        background: linear-gradient(135deg, #2d2d2d 0%, #4a3728 50%, #2d2d2d 100%);
        padding: 3rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, #d4a57430 0%, transparent 70%);
        border-radius: 50%;
    }

    .hero h1 {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 700;
        color: #f5e6d3;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .hero p {
        color: #c4a882;
        font-size: 1.1rem;
        margin-top: 0.7rem;
        font-weight: 300;
    }

    .hero-badge {
        display: inline-block;
        background: #d4a57420;
        border: 1px solid #d4a57450;
        color: #d4a574;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        margin-bottom: 1rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .chat-user {
        background: linear-gradient(135deg, #2d2d2d, #4a3728);
        border-radius: 18px 18px 4px 18px;
        padding: 1rem 1.3rem;
        margin: 0.7rem 0 0.7rem 3rem;
        color: #f5e6d3;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }

    .chat-assistant {
        background: white;
        border: 1px solid #e8ddd4;
        border-radius: 18px 18px 18px 4px;
        padding: 1rem 1.3rem;
        margin: 0.7rem 3rem 0.7rem 0;
        color: #2d2d2d;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        line-height: 1.7;
    }

    .reasoning-box {
        background: #2d2d2d;
        border-radius: 12px;
        padding: 1.2rem;
        font-size: 0.82rem;
        color: #d4a574;
        font-family: 'Inter', monospace;
        line-height: 1.8;
        border: 1px solid #d4a57420;
    }

    .rec-card {
        background: white;
        border: 1px solid #e8ddd4;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: transform 0.2s;
    }

    .rec-card:hover { transform: translateY(-2px); }

    .rec-card h4 {
        color: #2d2d2d;
        margin: 0 0 0.5rem 0;
        font-family: 'Playfair Display', serif;
        font-size: 1.05rem;
    }

    .rec-rank {
        display: inline-block;
        background: linear-gradient(135deg, #2d2d2d, #4a3728);
        color: #d4a574;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        text-align: center;
        line-height: 28px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }

    .tag {
        display: inline-block;
        background: #f5f0eb;
        color: #4a3728;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.72rem;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
        border: 1px solid #e8ddd4;
    }

    .profile-box {
        background: white;
        border: 1px solid #e8ddd4;
        border-radius: 12px;
        padding: 1.2rem;
        color: #4a3728;
        font-size: 0.88rem;
        line-height: 1.8;
    }

    .sidebar-header {
        color: #d4a574;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    div[data-testid="stButton"] button {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stTextInput input {
        border-radius: 10px;
        border: 1.5px solid #e8ddd4;
        background: white;
        color: #2d2d2d;
        padding: 0.6rem 1rem;
    }

    .stTextInput input:focus {
        border-color: #d4a574;
        box-shadow: 0 0 0 2px #d4a57420;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reasoning_traces" not in st.session_state:
    st.session_state.reasoning_traces = []
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "profile" not in st.session_state:
    st.session_state.profile = {}
if "sample_users" not in st.session_state:
    st.session_state.sample_users = []


def send_message(message: str) -> dict:
    try:
        response = requests.post(f"{API_URL}/chat", json={
            "user_id": st.session_state.user_id,
            "message": message,
            "conversation": st.session_state.conversation,
            "session_id": st.session_state.session_id
        }, timeout=60)
        return response.json()
    except Exception as e:
        return {"response": f"Connection error: {e}", "reasoning_trace": [], "recommendations": []}


# Sidebar
with st.sidebar:
    st.markdown("<div class='sidebar-header'>✦ User Selection</div>", unsafe_allow_html=True)

    if st.button("↻ Get Random Users", use_container_width=True):
        resp = requests.get(f"{API_URL}/sample-users?n=8")
        if resp.status_code == 200:
            st.session_state.sample_users = resp.json().get("users", [])

    if st.session_state.sample_users:
        st.markdown("<div style='color:#a0a0a0; font-size:0.78rem; margin:0.5rem 0'>Select a user:</div>", unsafe_allow_html=True)
        for u in st.session_state.sample_users:
            if st.button(f"◈ {u[:22]}...", key=f"u_{u}", use_container_width=True):
                st.session_state.user_id = u
                st.session_state.selected_user_preview = u
                st.session_state.conversation = []
                st.session_state.messages = []
                st.session_state.reasoning_traces = []
                st.session_state.recommendations = []
                st.session_state.profile = {}
                st.rerun()

    st.divider()
    st.markdown("<div class='sidebar-header'>✦ Manual Entry</div>", unsafe_allow_html=True)
    new_id = st.text_input("User ID", value=st.session_state.get("selected_user_preview", ""), placeholder="paste ID here", label_visibility="collapsed")
    if st.button("Use this ID", use_container_width=True) and new_id:
        st.session_state.user_id = new_id
        st.session_state.conversation = []
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown(f"<div style='color:#888; font-size:0.75rem'>Active: {st.session_state.user_id[:20]}...</div>", unsafe_allow_html=True)

    if st.button("✦ New Session", use_container_width=True):
        st.session_state.conversation = []
        st.session_state.messages = []
        st.session_state.reasoning_traces = []
        st.session_state.recommendations = []
        st.session_state.profile = {}
        st.session_state.user_id = str(uuid.uuid4())
        st.rerun()

# Main layout
col_chat, col_right = st.columns([3, 2])

with col_chat:
    st.markdown("""
    <div class='hero'>
        <div class='hero-badge'>✦ Powered by Twinn AI</div>
        <h1>Make we find you the place wey go sweet your belle</h1>
        <p>Recommendations wey fit you well well. E go jus be like say we don sabi you tey tey!</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align:center; padding: 3rem; color: #a09080;'>
            <div style='font-size:3rem; margin-bottom:1rem'>✦</div>
            <div style='font-family: Playfair Display, serif; font-size:1.3rem; color:#4a3728; margin-bottom:0.5rem'>
                Start a conversation
            </div>
            <div style='font-size:0.9rem'>
                Follow me yarn wetin you dey in the mood for, abi make I kukuma surprise you
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-assistant'>✦ {msg['content']}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_input = st.text_input(
                "Message",
                placeholder="What are you in the mood for tonight?",
                label_visibility="collapsed"
            )
        with col_btn:
            submitted = st.form_submit_button("→", use_container_width=True)

    if submitted and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("✦ Finding the perfect match..."):
            result = send_message(user_input)
        response = result.get("response", "")
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.conversation.append({"role": "user", "content": user_input})
        st.session_state.conversation.append({"role": "assistant", "content": response})
        if result.get("reasoning_trace"):
            st.session_state.reasoning_traces = result["reasoning_trace"]
        if result.get("recommendations"):
            st.session_state.recommendations = result["recommendations"]
        if result.get("profile"):
            st.session_state.profile = result["profile"]
        st.rerun()

with col_right:
    st.markdown("#### 🔬 Agent Reasoning")
    if st.session_state.reasoning_traces:
        trace_items = "".join([f"<div style='margin-bottom:0.4rem'>→ {step}</div>" for step in st.session_state.reasoning_traces])
        st.markdown(f"<div class='reasoning-box'>{trace_items}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='reasoning-box' style='color:#666'>Reasoning trace appears here during recommendations...</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    st.markdown("#### 👁 Taste Profile")
    profile = st.session_state.profile
    if profile and profile.get("favorite_categories"):
        st.markdown(f"""
        <div class='profile-box'>
            <b>Loves:</b> {profile.get('favorite_categories', '—')}<br>
            <b>Budget:</b> {profile.get('price_preference', '—')}<br>
            <b>Cities:</b> {profile.get('preferred_cities', '—')}<br>
            <b>Style:</b> {profile.get('dining_style', '—')}<br>
            <br><i style='color:#888'>{profile.get('personality', '')}</i>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div class='profile-box' style='color:#aaa; text-align:center; padding:2rem'>Profile builds as you chat ✦</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    st.markdown("#### ✦ Top Picks")
    if st.session_state.recommendations:
        for rec in st.session_state.recommendations:
            st.markdown(f"""
            <div class='rec-card'>
                <h4><span class='rec-rank'>{rec.get('rank')}</span>{rec.get('name')}</h4>
                <span class='tag'>📍 {rec.get('city', '—')}</span>
                <span class='tag'>💰 {rec.get('price_range', '—')}</span>
                <br>
                <div style='color:#888; font-size:0.78rem; margin-top:0.4rem'>{str(rec.get('categories', ''))[:80]}</div>
                <div style='color:#4a3728; font-size:0.83rem; margin-top:0.4rem; font-style:italic'>{str(rec.get('reason', ''))[:130]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; color:#aaa; padding:2rem'>✦<br>Picks appear here</div>", unsafe_allow_html=True)
