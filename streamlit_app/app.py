"""
app.py
------
Safety Stock Automation System — Streamlit Entry Point

Run with:
    streamlit run app.py

Architecture:
    app.py              ← this file (router + sidebar)
    modules/
        auth.py         ← login, session state
        utils.py        ← CSS, KPI cards, priority mapping
        charts.py       ← all Plotly charts
        pipeline.py     ← subprocess pipeline runner
        dashboard_page.py
        upload_page.py
        forecast_page.py
        download_page.py
        settings_page.py
"""

import streamlit as st

# ── Page config must be the FIRST Streamlit call ─────────────────────────────
st.set_page_config(
    page_title      = "Safety Stock Automation",
    page_icon       = "📦",
    layout          = "wide",
    initial_sidebar_state = "expanded",
)

# ── Module imports (after set_page_config) ────────────────────────────────────
from modules.auth           import init_session, is_authenticated, logout_user, render_login
from modules.utils          import inject_global_css
from modules.dashboard_page import render_dashboard
from modules.historical_page import render_historical_page
from modules.inventory_page import render_inventory_page
from modules.upload_page    import render_upload_page
from modules.forecast_page  import render_forecast_page
from modules.download_page  import render_download_page
from modules.settings_page  import render_settings_page


# ══════════════════════════════════════════════════════════════════════════════
# SESSION INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

init_session()


# ══════════════════════════════════════════════════════════════════════════════
# NOT AUTHENTICATED → SHOW LOGIN
# ══════════════════════════════════════════════════════════════════════════════

if not is_authenticated():
    render_login()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATED → SIDEBAR + MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

inject_global_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # Animated Logo + app name
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;padding:12px 10px;margin-bottom:15px;
                background:linear-gradient(135deg, rgba(31, 111, 235, 0.08), rgba(56, 139, 253, 0.03));
                border-radius:12px;border:1px solid rgba(31, 111, 235, 0.15);
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
        <div style="background:linear-gradient(135deg,#1F6FEB,#388BFD);
                    width:38px;height:38px;border-radius:10px;
                    display:flex;align-items:center;justify-content:center;
                    font-size:18px;flex-shrink:0;box-shadow:0 0 10px rgba(31, 111, 235, 0.3);">📦</div>
        <div>
            <div style="font-weight:800;color:#F0F6FC;font-size:14px;letter-spacing:-0.3px;line-height:1.2;">Safety Stock</div>
            <div style="color:#8B949E;font-size:9px;text-transform:uppercase;font-weight:700;letter-spacing:0.8px;">Intelligence Suite</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Navigation items
    NAV_ITEMS = [
        ("🏠",  "Dashboard",          "Dashboard"),
        ("📈",  "Historical Analytics","Historical"),
        ("📦",  "Inventory Planning",  "Inventory"),
        ("📤",  "Upload Monthly Data","Upload"),
        ("🔮",  "Next Month Forecast","Forecast"),
        ("📥",  "Download Prediction","Download"),
        ("⚙️",  "Settings",           "Settings"),
    ]

    # Forecast badge
    pred_ready = st.session_state.get("prediction_ready", False)

    for icon, label, key in NAV_ITEMS:
        badge = " 🟢" if key == "Forecast" and pred_ready else ""
        is_active = st.session_state.get("active_page") == key
        btn_type  = "primary" if is_active else "secondary"

        if st.button(
            f"{icon}  {label}{badge}",
            key        = f"nav_{key}",
            use_container_width = True,
            type       = btn_type,
        ):
            st.session_state["active_page"] = key
            st.rerun()

    # Notification Center in sidebar
    st.markdown('<div class="divider" style="margin-top:20px;"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px; color:#8B949E; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:8px; padding-left:4px;">
        🔔 Notification Center
    </div>
    """, unsafe_allow_html=True)
    
    if pred_ready:
        st.markdown("""
        <div style="background:rgba(56, 139, 253, 0.04); border:1px solid rgba(56, 139, 253, 0.15); border-radius:6px; padding:6px 12px; font-size:11px; margin-bottom:6px; color:#388BFD; font-weight:500;">
            ✓ Forecast Ingested Successfully
        </div>
        <div style="background:rgba(56, 139, 253, 0.04); border:1px solid rgba(56, 139, 253, 0.15); border-radius:6px; padding:6px 12px; font-size:11px; margin-bottom:6px; color:#388BFD; font-weight:500;">
            ✓ Safety Buffers Synchronized
        </div>
        """, unsafe_allow_html=True)
        # Check critical count
        pred_df = st.session_state.get("prediction_df")
        if pred_df is not None and "Inventory_Status" in pred_df.columns:
            crit_count = (pred_df["Inventory_Status"] == "Critical").sum()
            if crit_count > 0:
                st.markdown(f"""
                <div style="background:rgba(248, 81, 73, 0.04); border:1px solid rgba(248, 81, 73, 0.15); border-radius:6px; padding:6px 12px; font-size:11px; margin-bottom:6px; color:#FF7B72; font-weight:600;">
                    🚨 {crit_count} Critical Risks Found
                </div>
                """, unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(31, 111, 235, 0.04); border:1px solid rgba(31, 111, 235, 0.12); border-radius:6px; padding:6px 12px; font-size:11px; margin-bottom:6px; color:#8B949E;">
            ✓ Requisition Sheet Ready
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size:11px; color:#8B949E; font-style:italic; padding:6px 12px;">
            No active alerts. Execute pipeline to update notifications.
        </div>
        """, unsafe_allow_html=True)

    # Bottom section
    st.markdown('<div class="divider" style="margin-top:15px; margin-bottom:15px;"></div>', unsafe_allow_html=True)

    # User info
    user_name = st.session_state.get("user_name", "User")
    role      = st.session_state.get("role", "viewer").upper()
    
    # Generate initials
    names = user_name.split()
    initials = "".join([n[0] for n in names[:2]]).upper() if names else "U"
    
    st.markdown(f"""
    <div style="background:rgba(22, 27, 34, 0.45);border:1px solid rgba(255,255,255,0.06);
                border-radius:12px;padding:12px;margin-bottom:12px;display:flex;align-items:center;gap:12px;">
        <div style="background:rgba(31, 111, 235, 0.15);width:34px;height:34px;border-radius:50%;
                    display:flex;align-items:center;justify-content:center;color:#58A6FF;
                    font-weight:700;font-size:13px;border:1px solid rgba(31, 111, 235, 0.25);
                    flex-shrink:0;">
            {initials}
        </div>
        <div style="flex-grow:1;min-width:0;">
            <div style="color:#F0F6FC;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {user_name}
            </div>
            <div style="color:#8B949E;font-size:10px;font-weight:700;letter-spacing:0.5px;">
                {role}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪  Logout", use_container_width=True, type="secondary"):
        logout_user()
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════════════

active = st.session_state.get("active_page", "Dashboard")

if   active == "Dashboard"  : render_dashboard()
elif active == "Historical" : render_historical_page()
elif active == "Inventory"  : render_inventory_page()
elif active == "Upload"     : render_upload_page()
elif active == "Forecast"   : render_forecast_page()
elif active == "Download"   : render_download_page()
elif active == "Settings"   : render_settings_page()
else:                         render_dashboard()
