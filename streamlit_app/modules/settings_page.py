"""
modules/settings_page.py
------------------------
Settings page — Application config, pipeline info, and SCM manual.
"""

from pathlib import Path
import streamlit as st

from modules.utils import inject_global_css, section_header, kpi_card


def render_settings_page() -> None:
    inject_global_css()

    st.markdown("## ⚙️ Administration & Configuration")
    st.markdown(
        '<p style="color:#8B949E;margin-top:-8px;font-size:14px;">Manage global application variables, verify background pipeline paths, and view documentation.</p>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs([
        "⚙️ Application & Theme Settings",
        "🗄️ System & Pipeline Status",
        "ℹ️ System Documentation & Help"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: APPLICATION & THEME SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### ⚙️ System Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="kpi-card" style="padding:20px; margin-bottom:12px; height:200px;">
                <div style="font-weight:700; color:#58A6FF; font-size:14px; margin-bottom:10px;">🎨 Theme Parameters</div>
                <div style="font-size:12.5px; color:#8B949E; line-height:1.6;">
                    <b>Visual Interface:</b> Dark Blue Glassmorphism<br>
                    <b>Background Gradient:</b> HSL Dark Blue Radial<br>
                    <b>Typography Font:</b> Inter, sans-serif (Google Fonts)<br>
                    <b>Card Backdrop:</b> 12px blur filter, 1px white border (rgba 0.08)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="kpi-card" style="padding:20px; height:180px;">
                <div style="font-weight:700; color:#58A6FF; font-size:14px; margin-bottom:10px;">🔌 Future Database Connectors</div>
                <div style="font-size:12.5px; color:#8B949E; line-height:1.5;">
                    Connector configuration placeholders for <b>Azure SQL</b>, <b>PostgreSQL</b>, and <b>Snowflake</b> integrations.<br>
                    <span style="color:#8B949E; font-size:11px; font-style:italic;">Status: Local JSON file mode active.</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="kpi-card" style="padding:20px; margin-bottom:12px; height:200px;">
                <div style="font-weight:700; color:#58A6FF; font-size:14px; margin-bottom:10px;">🏢 Company Information</div>
                <div style="font-size:12.5px; color:#8B949E; line-height:1.6;">
                    <b>Enterprise:</b> Safety Stock Intelligence Suite<br>
                    <b>Client Target:</b> Supply Chain & Operations Division<br>
                    <b>Product Version:</b> Enterprise Edition v1.4.2<br>
                    <b>Developer Org:</b> Deloitte SCM Practice Group
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="kpi-card" style="padding:20px; height:180px;">
                <div style="font-weight:700; color:#58A6FF; font-size:14px; margin-bottom:10px;">🔐 Active Directory / SSO (Coming Soon)</div>
                <div style="font-size:12.5px; color:#8B949E; line-height:1.5;">
                    Future single sign-on (SSO) configurations enabling <b>Microsoft Entra ID</b> and <b>Okta OAuth2</b> integrations.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: SYSTEM & PIPELINE STATUS
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🗄️ Directories & Execution Environments")

        from modules.pipeline import (DEPLOYMENT_ROOT, SCRIPTS_DIR,
                                       MONTHLY_DIR, PREDICTION_FILE)
        from modules.pipeline import prediction_exists

        info = {
            "Deployment Root Directory": str(DEPLOYMENT_ROOT),
            "Pipeline Scripts Location" : str(SCRIPTS_DIR),
            "Monthly Ingestion Directory": str(MONTHLY_DIR),
            "Active Prediction Output"  : str(PREDICTION_FILE),
            "Calculation Run Status"    : "✅ Verified Prediction Available" if prediction_exists() else "❌ Missing predictions.csv",
        }
        for k, v in info.items():
            st.markdown(f"""
            <div style="background:rgba(22, 27, 34, 0.4);border:1px solid rgba(255,255,255,0.05);border-radius:8px;
                        padding:12px 18px;margin-bottom:6px;display:flex;gap:16px;">
                <span style="color:#8B949E;font-size:12px;min-width:200px;font-weight:600;">{k}</span>
                <code style="color:#E6EDF3;font-size:12px;word-break:break-all;">{v}</code>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)
        section_header("Pipeline Scripts Verification")
        scripts = [
            "01_Data_Validation_Cleaning.py",
            "02_Feature_Engineering.py",
            "03_Update_Historical_Data.py",
            "04_SES_Forecasting.py",
            "05_Inventory_Planning.py",
        ]
        for s in scripts:
            path   = SCRIPTS_DIR / s
            exists = "✅ In Place" if path.exists() else "❌ Script Missing"
            st.markdown(f"""
            <div style="background:rgba(22, 27, 34, 0.4);border:1px solid rgba(255,255,255,0.05);border-radius:8px;
                        padding:10px 18px;margin-bottom:4px;display:flex;gap:16px;align-items:center;">
                <span style="min-width:120px; font-size:12px; font-weight:700; color:{'#3FB950' if path.exists() else '#F85149'}">{exists}</span>
                <code style="color:#E6EDF3;font-size:12px;">{s}</code>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: SYSTEM DOCUMENTATION & HELP
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 📖 SCM System Operations Manual")
        
        st.markdown("""
        <div class="kpi-card" style="padding:24px; margin-bottom:16px; line-height:1.6; font-size:13.5px; color:#C9D1D9;">
            <h4 style="margin:0 0 10px 0; color:#58A6FF; font-size:15px;">🌐 Project Overview</h4>
            This platform is an enterprise-grade demand forecasting and safety stock inventory planner.
            By ingestion of client-provided consumption ledger and master lead times, the system auto-calculates optimal reorder parameters to prevent operations stockouts while reducing capital locks.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="kpi-card" style="padding:24px; margin-bottom:16px; line-height:1.6; font-size:13.5px; color:#C9D1D9;">
            <h4 style="margin:0 0 10px 0; color:#58A6FF; font-size:15px;">⚙️ Application Architecture</h4>
            The system operates under a decoupled decoupled client-server architecture:
            <ul>
                <li><b>Frontend Interface:</b> Streamlit-based web dashboard styled using customized CSS overrides.</li>
                <li><b>Analytical Engines:</b> Clean modular Python scripts executing statistical forecast formulations.</li>
                <li><b>Storage:</b> Lightweight, portable Excel/CSV data matrices allowing quick local sync.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(r"""
        <div class="kpi-card" style="padding:24px; margin-bottom:16px; line-height:1.6; font-size:13.5px; color:#C9D1D9;">
            <h4 style="margin:0 0 10px 0; color:#58A6FF; font-size:15px;">🧠 Forecasting Engine (SES model)</h4>
            The demand forecast is calculated using a Single Exponential Smoothing (SES) model with optimal alpha parameter search:
            \[Y_{t+1} = \alpha Y_t + (1-\alpha) S_t\]
            Alpha parameters are calculated dynamically per material code to minimize mean absolute scaled errors (MASE).
        </div>
        """, unsafe_allow_html=True)

        st.markdown(r"""
        <div class="kpi-card" style="padding:24px; margin-bottom:16px; line-height:1.6; font-size:13.5px; color:#C9D1D9;">
            <h4 style="margin:0 0 10px 0; color:#58A6FF; font-size:15px;">🛡️ Safety Stock Formulation</h4>
            Safety stock buffers are established to cover lead time demand volatility:
            \[\text{Safety Stock} = Z \times \sigma_{LT} \times \sqrt{\text{Lead Time}}\]
            Reorder points (ROP) are set as:
            \[\text{ROP} = \text{Lead Time Demand} + \text{Safety Stock}\]
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="kpi-card" style="padding:24px; line-height:1.6; font-size:13.5px; color:#C9D1D9;">
            <h4 style="margin:0 0 10px 0; color:#58A6FF; font-size:15px;">🛠️ Technology Stack</h4>
            <ul>
                <li><b>Framework:</b> Streamlit 1.32+</li>
                <li><b>Visual Libraries:</b> Plotly Express & Plotly Graph Objects</li>
                <li><b>Data Processing:</b> Pandas, Numpy</li>
                <li><b>Statistical Algorithms:</b> Scipy Stats, Statsmodels</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
