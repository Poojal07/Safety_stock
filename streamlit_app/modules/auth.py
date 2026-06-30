"""
modules/auth.py
---------------
Authentication module for Safety Stock Automation System.

Handles login, session state, password hashing.
Designed to be swapped with a database backend in future.
"""

import hashlib
import json
from pathlib import Path

import streamlit as st

# Path to local credential store
USERS_FILE = Path(__file__).parent.parent / "config" / "users.json"


# ── Credential helpers ────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Return SHA-256 hex digest of the given password."""
    return hashlib.sha256(password.encode()).hexdigest()


def _load_users() -> dict:
    """Load user records from the local JSON credential store.

    Future: replace this body with a database query.
    """
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def verify_credentials(username: str, password: str) -> dict | None:
    """Verify username and password.

    Returns the user record dict on success, None on failure.
    Future: replace with database lookup.
    """
    users = _load_users()
    user  = users.get(username.strip().lower())
    if user and user["password_hash"] == _hash_password(password):
        return user
    return None


# ── Session state helpers ─────────────────────────────────────────────────────

def init_session() -> None:
    """Initialise all session state keys on first load."""
    defaults = {
        "authenticated"   : False,
        "username"        : None,
        "user_name"       : None,
        "role"            : None,
        "prediction_ready": False,
        "prediction_df"   : None,
        "historical_df"   : None,
        "active_page"     : "Dashboard",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def login_user(username: str, user_record: dict) -> None:
    st.session_state["authenticated"] = True
    st.session_state["username"]      = username
    st.session_state["user_name"]     = user_record.get("name", username)
    st.session_state["role"]          = user_record.get("role", "viewer")


def logout_user() -> None:
    for key in ["authenticated", "username", "user_name", "role",
                "prediction_ready", "prediction_df", "historical_df"]:
        st.session_state[key] = None
    st.session_state["authenticated"]  = False
    st.session_state["active_page"]    = "Dashboard"


# ── Login page renderer ───────────────────────────────────────────────────────

def render_login() -> None:
    """Render the full-screen login page."""

    # Full-page centered layout with animated gradient background, floating shapes, and glassmorphism overrides
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Perfect full screen viewport locks */
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #070a12, #0d162d, #090e1f, #05070d) !important;
        background-size: 400% 400% !important;
        animation: gradientBG 15s ease infinite !important;
        min-height: 100vh !important;
    }
    
    .main {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        min-height: 100vh !important;
        overflow-y: auto !important;
    }
    
    .main .block-container {
        max-width: 440px !important;
        padding: 40px 20px !important;
        margin: auto !important;
        background: transparent !important;
    }
    
    /* Background glows styling */
    .background-glows {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
        overflow: hidden;
        pointer-events: none;
    }
    .glow-circle {
        position: absolute;
        border-radius: 50%;
        filter: blur(90px);
        opacity: 0.22;
        mix-blend-mode: screen;
    }
    .glow-1 {
        top: 15%;
        left: 10%;
        width: 320px;
        height: 320px;
        background: #1f6feb;
        animation: float1 20s ease-in-out infinite alternate;
    }
    .glow-2 {
        bottom: 15%;
        right: 10%;
        width: 380px;
        height: 380px;
        background: #bc8cff;
        animation: float2 24s ease-in-out infinite alternate;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes float1 {
        0% { transform: translate(0, 0) scale(1); }
        100% { transform: translate(70px, 50px) scale(1.15); }
    }
    @keyframes float2 {
        0% { transform: translate(0, 0) scale(1.1); }
        100% { transform: translate(-60px, -50px) scale(0.85); }
    }
    @keyframes slideUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    @keyframes logoPulse {
        0%, 100% { transform: scale(1); box-shadow: 0 8px 20px rgba(31, 111, 235, 0.35); }
        50% { transform: scale(1.05); box-shadow: 0 8px 30px rgba(31, 111, 235, 0.65); }
    }
    
    .login-logo {
        width: 72px;
        height: 72px;
        background: linear-gradient(135deg, #1F6FEB, #388BFD);
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        margin: 0 auto 20px auto;
        box-shadow: 0 8px 20px rgba(31, 111, 235, 0.35);
        animation: logoPulse 3s infinite ease-in-out;
    }
    
    .login-title {
        font-size: 24px;
        font-weight: 800;
        color: #F0F6FC;
        text-align: center;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    
    .login-subtitle {
        font-size: 11px;
        color: #8B949E;
        text-align: center;
        margin-bottom: 28px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    /* Inputs overrides */
    .stTextInput > label {
        color: #8B949E !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        margin-bottom: 6px !important;
    }
    .stTextInput > div > div > input {
        background: rgba(13, 17, 23, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        color: #F0F6FC !important;
        padding: 12px 14px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1F6FEB !important;
        box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.2) !important;
        background: rgba(13, 17, 23, 0.9) !important;
    }
    
    /* Form wrapper styled as the card itself */
    div[data-testid="stForm"] {
        background: rgba(22, 27, 34, 0.45) !important;
        backdrop-filter: blur(25px) saturate(200%) !important;
        -webkit-backdrop-filter: blur(25px) saturate(200%) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px !important;
        padding: 40px 32px !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 
                    0 0 40px rgba(31, 111, 235, 0.05),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        animation: slideUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
        width: 100% !important;
        max-width: 440px !important;
        margin: 0 auto !important;
    }
    
    /* Button custom overrides */
    .stButton > button {
        background: linear-gradient(135deg, #1F6FEB 0%, #388BFD 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.25) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        cursor: pointer !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(31, 111, 235, 0.45) !important;
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
    }
    
    /* Checkbox Alignment */
    .stCheckbox > label {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        margin-top: 8px !important;
        margin-bottom: 24px !important;
    }
    .stCheckbox label p {
        color: #8B949E !important;
        font-size: 13.5px !important;
    }
    </style>
    
    <div class="background-glows">
        <div class="glow-circle glow-1"></div>
        <div class="glow-circle glow-2"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; max-width: 440px; margin: 0 auto;">
        <div class="login-logo">📦</div>
        <div class="login-title">Safety Stock Automation</div>
        <div class="login-subtitle">SCM Integrated Demand Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username...")
        password = st.text_input("Password", type="password", placeholder="Enter your password...")
        remember = st.checkbox("Remember Session", value=True)
        
        # TODO Add Lottie Loading Animation placeholder
        submitted = st.form_submit_button(
            "🔐  Sign In",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            user_record = verify_credentials(username, password)
            if user_record:
                login_user(username.strip().lower(), user_record)
                st.success(f"Welcome back, {user_record['name']}!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

    st.markdown("""
    <div style="text-align: center; max-width: 440px; margin: 20px auto 0 auto;">
        <hr style="border-color:rgba(255,255,255,0.06); margin: 0 0 16px 0;">
        <p style="color:#8B949E; font-size:12px; margin: 0;">
            Default credentials: <code>admin</code> / <code>admin</code> or <code>manager</code> / <code>manager</code>
        </p>
    </div>
    """, unsafe_allow_html=True)
