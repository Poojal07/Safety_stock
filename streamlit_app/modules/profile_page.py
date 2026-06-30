"""
modules/profile_page.py
-----------------------
Enterprise User Profile & Account Settings.
"""

import hashlib
import json
from pathlib import Path
import streamlit as st

from modules.utils import inject_global_css, section_header, kpi_card

USERS_FILE = Path(__file__).parent.parent / "config" / "users.json"


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def render_profile_page() -> None:
    inject_global_css()

    st.markdown("## 👤 User Profile Management")
    st.markdown(
        '<p style="color:#8B949E;margin-top:-8px;font-size:14px;">Manage user credentials, security keys, and access permissions.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1.5, 2.5])

    with col1:
        # Profile avatar and metadata details
        user_name = st.session_state.get("user_name", "User")
        role = st.session_state.get("role", "viewer").upper()
        username = st.session_state.get("username", "—")
        
        names = user_name.split()
        initials = "".join([n[0] for n in names[:2]]).upper() if names else "U"
        
        st.markdown(f"""
        <div class="kpi-card" style="text-align:center; padding:32px 24px;">
            <div style="background:rgba(31, 111, 235, 0.12); width:80px; height:80px; border-radius:50%;
                        display:flex; align-items:center; justify-content:center; color:#58A6FF;
                        font-weight:800; font-size:32px; border:2px solid rgba(31, 111, 235, 0.3);
                        margin:0 auto 16px auto; box-shadow: 0 0 15px rgba(31, 111, 235, 0.2);">
                {initials}
            </div>
            <h3 style="margin:0; color:#F0F6FC; font-size:18px;">{user_name}</h3>
            <p style="color:#8B949E; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; margin:4px 0 16px 0;">
                {role}
            </p>
            <div style="border-top:1px solid rgba(255,255,255,0.06); padding-top:16px; text-align:left; font-size:12.5px; line-height:1.6;">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="color:#8B949E;">Username:</span>
                    <span style="color:#F0F6FC; font-weight:600;">{username}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="color:#8B949E;">Last Login:</span>
                    <span style="color:#F0F6FC; font-weight:600;">Recent Session</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="color:#8B949E;">App Access:</span>
                    <span style="color:#3FB950; font-weight:600;">Active</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#8B949E;">Permissions:</span>
                    <span style="color:#58A6FF; font-weight:600;">{role} Role</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪  Logout from Application", use_container_width=True, type="secondary"):
            from modules.auth import logout_user
            logout_user()
            st.rerun()

    with col2:
        section_header("Security Credentials Update")
        
        with st.form("profile_change_pw_form"):
            current_pw = st.text_input("Current Security Password", type="password", placeholder="Enter current password...")
            new_pw     = st.text_input("New Security Password",     type="password", placeholder="At least 6 characters...")
            confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="Repeat new password...")
            submitted  = st.form_submit_button("🔒 Update Account Password", type="primary")

        if submitted:
            if not current_pw or not new_pw or not confirm_pw:
                st.markdown('<div class="insight-box insight-urgent" style="padding:8px 12px; font-size:12.5px;">❌ All password fields are required.</div>', unsafe_allow_html=True)
            elif new_pw != confirm_pw:
                st.markdown('<div class="insight-box insight-urgent" style="padding:8px 12px; font-size:12.5px;">❌ New password and confirmation do not match.</div>', unsafe_allow_html=True)
            elif len(new_pw) < 6:
                st.markdown('<div class="insight-box insight-urgent" style="padding:8px 12px; font-size:12.5px;">❌ New password must be at least 6 characters.</div>', unsafe_allow_html=True)
            else:
                try:
                    users = json.loads(USERS_FILE.read_text())
                    user  = users.get(username)
                    if user and user["password_hash"] == _hash(current_pw):
                        users[username]["password_hash"] = _hash(new_pw)
                        USERS_FILE.write_text(json.dumps(users, indent=2))
                        st.markdown('<div class="insight-box insight-success" style="padding:8px 12px; font-size:12.5px;">✅ Security password updated successfully.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="insight-box insight-urgent" style="padding:8px 12px; font-size:12.5px;">❌ Current password is incorrect.</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="insight-box insight-urgent" style="padding:8px 12px; font-size:12.5px;">❌ Error: {str(e)}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Enterprise Account Policy")
        st.markdown("""
        <div style="background:rgba(22, 27, 34, 0.4); border:1px solid rgba(255,255,255,0.05); border-radius:10px; padding:16px 20px; font-size:12.5px; line-height:1.5; color:#8B949E;">
            📌 <b>Authentication Notice:</b> Your account is registered under corporate directory credentials. Password updates are synchronized locally. Profile picture sync is disabled for local mode. For future Active Directory integration, check the Settings panel.
        </div>
        """, unsafe_allow_html=True)
