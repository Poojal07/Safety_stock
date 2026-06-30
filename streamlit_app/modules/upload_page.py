"""
modules/upload_page.py
----------------------
Upload Monthly Data page — file upload + pipeline execution with
business-friendly progress messages.
"""

import time
import pandas as pd
import streamlit as st
from pathlib import Path

from modules.utils import inject_global_css, section_header, kpi_card, fmt_currency
from modules.pipeline import run_pipeline, get_prediction_path, prediction_exists


def _validate_consumption(file) -> tuple[bool, str, pd.DataFrame | None]:
    try:
        df = pd.read_excel(file)
        
        # 1. Check there are exactly two columns
        if len(df.columns) < 2:
            return False, "Monthly demand column missing", None
        elif len(df.columns) > 2:
            return False, "More than one month column detected", None
            
        # 2. Check material_id exists (case-insensitive)
        cols = [str(c).strip().lower() for c in df.columns]
        if "material_id" not in cols:
            return False, "Material ID column missing", None
            
        # Get actual column references
        material_col_idx = cols.index("material_id")
        month_col = df.columns[1 - material_col_idx]
        
        # 3. Check second column contains numeric demand values
        non_null_demand = df[month_col].dropna()
        if len(non_null_demand) == 0:
            return False, "Demand values are invalid (column is empty)", None
            
        numeric_series = pd.to_numeric(non_null_demand, errors='coerce')
        if numeric_series.isnull().any():
            return False, "Demand values are invalid (contains non-numeric entries)", None
            
        # 4. Display detected metrics
        msg = (
            f"✔ Material ID detected<br>"
            f"✔ Forecast Month Detected: {month_col}<br>"
            f"✔ {len(df):,} Materials Found<br>"
            f"✔ File Ready for Processing"
        )
        return True, msg, df
    except Exception as e:
        return False, f"Could not read file: {str(e)}", None


def _validate_leadtime(file) -> tuple[bool, str, pd.DataFrame | None]:
    try:
        df = pd.read_excel(file)
        cols = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
        required = ["material_id", "material_lead_time", "moving_price", "unrestricted"]
        missing = [r for r in required if r not in cols]
        if missing:
            return False, f"Column mismatch: missing {', '.join(missing)}", None
            
        msg = (
            f"✔ Lead Time Master detected<br>"
            f"✔ All columns validated successfully<br>"
            f"✔ {len(df):,} Materials Found<br>"
            f"✔ File Ready for Processing"
        )
        return True, msg, df
    except Exception as e:
        return False, f"Could not read file: {str(e)}", None


def render_upload_page() -> None:
    inject_global_css()

    st.markdown("## 📤 Data Integration Suite")
    st.markdown(
        '<p style="color:#8B949E;margin-top:-8px;font-size:14px;">Upload the current month\'s transactional and master datasets to orchestrate next cycle\'s planning.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    section_header("File Upload Controls")

    col1, col2 = st.columns(2)
    
    consumption_valid = False
    leadtime_valid = False
    consumption_df = None
    leadtime_df = None

    with col1:
        st.markdown("""
        <div class="kpi-card" style="padding:20px; background: rgba(22, 27, 34, 0.45); border-color: rgba(255,255,255,0.06); height: 130px; margin-bottom: 12px;">
            <div style="font-size:13px; color:#58A6FF; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:6px;">
                📊 Consumption Ledger
            </div>
            <div style="font-size:12px; color:#8B949E; line-height:1.4;">
                Contains month-over-month material consumption records.<br>
                <span style="color:#F0F6FC; font-weight:600;">Expected headers:</span> <code>material_id</code>, <code>date</code>, <code>demand</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        consumption_file = st.file_uploader(
            "Upload Consumption.xlsx",
            type=["xlsx", "xls"],
            key="consumption_upload",
            label_visibility="collapsed",
        )
        
        if consumption_file:
            ok, msg, df = _validate_consumption(consumption_file)
            if ok:
                st.markdown(f'<div class="insight-box insight-success" style="padding:12px 16px; font-size:13px; font-weight:500; line-height:1.6;">{msg}</div>', unsafe_allow_html=True)
                consumption_valid = True
                consumption_df = df
            else:
                st.markdown(f'<div class="insight-box insight-urgent" style="padding:12px 16px; font-size:13px; font-weight:500; line-height:1.6;">❌ {msg}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="kpi-card" style="padding:20px; background: rgba(22, 27, 34, 0.45); border-color: rgba(255,255,255,0.06); height: 130px; margin-bottom: 12px;">
            <div style="font-size:13px; color:#58A6FF; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:6px;">
                📋 Lead Time Master
            </div>
            <div style="font-size:12px; color:#8B949E; line-height:1.4;">
                Contains lead times, unit prices, and stock balances.<br>
                <span style="color:#F0F6FC; font-weight:600;">Expected headers:</span> <code>material_id</code>, <code>material_lead_time</code>, <code>moving_price</code>, <code>unrestricted</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        leadtime_file = st.file_uploader(
            "Upload LeadTime.xlsx",
            type=["xlsx", "xls"],
            key="leadtime_upload",
            label_visibility="collapsed",
        )
        
        if your_file := leadtime_file:
            ok, msg, df = _validate_leadtime(your_file)
            if ok:
                st.markdown(f'<div class="insight-box insight-success" style="padding:12px 16px; font-size:13px; font-weight:500; line-height:1.6;">{msg}</div>', unsafe_allow_html=True)
                leadtime_valid = True
                leadtime_df = df
            else:
                st.markdown(f'<div class="insight-box insight-urgent" style="padding:12px 16px; font-size:13px; font-weight:500; line-height:1.6;">❌ {msg}</div>', unsafe_allow_html=True)

    # ── Dataset Previews ──────────────────────────────────────────────────────
    if consumption_valid or leadtime_valid:
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Upload Previews</div>', unsafe_allow_html=True)
        
        p1, p2 = st.columns(2)
        with p1:
            if consumption_valid and consumption_df is not None:
                st.markdown("<p style='color:#8B949E; font-size:12px; margin-bottom:4px;'>Consumption Sample (Top 5 rows)</p>", unsafe_allow_html=True)
                st.dataframe(consumption_df.head(5), use_container_width=True, hide_index=True)
        with p2:
            if leadtime_valid and leadtime_df is not None:
                st.markdown("<p style='color:#8B949E; font-size:12px; margin-bottom:4px;'>Lead Time Sample (Top 5 rows)</p>", unsafe_allow_html=True)
                st.dataframe(leadtime_df.head(5), use_container_width=True, hide_index=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Run button ────────────────────────────────────────────────────────────
    both_valid = consumption_valid and leadtime_valid
    run_col, _ = st.columns([2, 3])
    with run_col:
        run_clicked = st.button(
            "▶   Execute Forecasting Engine",
            type="primary",
            use_container_width=True,
            disabled=not both_valid,
        )
        if not both_valid:
            st.caption("Upload and validate both Excel datasets to unlock execution control.")

    # ── Pipeline execution ────────────────────────────────────────────────────
    if run_clicked and both_valid:
        consumption_file.seek(0)
        leadtime_file.seek(0)
        _run_with_progress(
            consumption_file.read(),
            leadtime_file.read(),
        )


def _run_with_progress(consumption_bytes: bytes, leadtime_bytes: bytes) -> None:
    """Execute the pipeline with a beautiful progress UI."""

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    section_header("Pipeline Operations")

    # Container for all progress UI
    progress_container = st.container()

    # TODO: Add Warehouse Animation in background
    # TODO: Add Lottie Loading Animation placeholder
    # TODO: Add Forklift and Moving Boxes Animation during compile

    with progress_container:
        status_text  = st.empty()
        progress_bar = st.progress(0)
        step_display = st.empty()

    completed_steps = []
    failed          = False
    error_msg       = ""

    for progress, label, success, error in run_pipeline(consumption_bytes, leadtime_bytes):
        if not success:
            failed    = True
            error_msg = error
            break

        # Update progress bar
        progress_bar.progress(min(progress, 1.0))

        # Update status message with animation effect
        status_text.markdown(f"""
        <div style="background:rgba(22, 27, 34, 0.55); border:1px solid rgba(31, 111, 235, 0.2); border-radius:12px;
                    padding:22px 24px; text-align:center; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
            <div style="font-size:16px; color:#F0F6FC; font-weight:700; margin-bottom:4px; letter-spacing: -0.3px;">
                🔄 {label}
            </div>
            <div style="font-size:12px; color:#8B949E;">Pipeline script processing active. Please stand by...</div>
        </div>
        """, unsafe_allow_html=True)

        # Track completed steps (only register true milestones)
        if "Running" not in label and "Ready" not in label and label not in completed_steps:
            completed_steps.append(label)

        # Show completed steps list
        if completed_steps:
            steps_html = "".join([
                f'<div style="color:#3FB950; font-size:13px; font-weight:600; padding:4px 0; display:flex; align-items:center; gap:8px;">'
                f'<span style="color:#3FB950;">✓</span> {s}</div>'
                for s in completed_steps
            ])
            step_display.markdown(f"""
            <div style="background:rgba(13, 17, 23, 0.45); border: 1px solid rgba(255,255,255,0.05); border-radius:10px; padding:16px 20px; margin-top:12px;">
                {steps_html}
            </div>
            """, unsafe_allow_html=True)

        time.sleep(0.15)  # brief pause for visual smoothness

    # ── Outcome ───────────────────────────────────────────────────────────────
    if failed:
        progress_bar.progress(0)
        st.error("⚠️ Pipeline execution terminated due to error. Please check validation metrics.")
        with st.expander("Technical Logs & Stacktrace"):
            st.code(error_msg, language="text")
        return

    # Success
    progress_bar.progress(1.0)
    status_text.empty()
    step_display.empty()

    # Load prediction into session state and compute summary stats
    pred_path = get_prediction_path()
    total_m = 0
    total_c = 0.0
    crit_m  = 0
    req_m   = 0
    f_month = "Next Cycle"
    
    if pred_path.exists():
        try:
            df = pd.read_csv(pred_path)
            st.session_state["prediction_df"]    = df
            st.session_state["prediction_ready"] = True
            
            total_m = len(df)
            total_c = df["Order_Cost"].sum() if "Order_Cost" in df.columns else 0.0
            crit_m  = int((df["Inventory_Status"] == "Critical").sum()) if "Inventory_Status" in df.columns else 0
            req_m   = int((df["Order_Quantity"] > 0).sum()) if "Order_Quantity" in df.columns else 0
            date_col = next((c for c in df.columns if "forecast_date" in c.lower()), None)
            if date_col and len(df) > 0:
                f_month = pd.to_datetime(df[date_col].iloc[0]).strftime("%B %Y")
        except Exception:
            pass

    # TODO: Add Lottie warehouse / forklift animation here if needed later.
    # Below is a premium, hardware-accelerated CSS animated checkmark and card container.
    
    st.markdown(f"""<style>
.premium-success-card {{
background: linear-gradient(135deg, rgba(13, 22, 45, 0.6) 0%, rgba(9, 13, 22, 0.8) 100%) !important;
backdrop-filter: blur(25px) saturate(200%) !important;
-webkit-backdrop-filter: blur(25px) saturate(200%) !important;
border: 1px solid rgba(63, 185, 80, 0.25) !important;
border-radius: 20px !important;
padding: 48px 40px !important;
box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), 0 0 30px rgba(63, 185, 80, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
animation: pulseSuccessBorder 4s infinite ease-in-out, slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
width: 100%;
text-align: center;
margin-top: 20px;
}}
@keyframes pulseSuccessBorder {{
0%, 100% {{
border-color: rgba(63, 185, 80, 0.25) !important;
box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), 0 0 30px rgba(63, 185, 80, 0.08);
}}
50% {{
border-color: rgba(63, 185, 80, 0.5) !important;
box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45), 0 0 45px rgba(63, 185, 80, 0.18);
}}
}}
.success-icon-container {{
width: 80px;
height: 80px;
margin: 0 auto 24px auto;
display: flex;
justify-content: center;
align-items: center;
}}
.checkmark-svg {{
width: 72px;
height: 72px;
border-radius: 50%;
display: block;
stroke-width: 3;
stroke: #3FB950;
stroke-miterlimit: 10;
box-shadow: inset 0px 0px 0px #3FB950;
animation: fillCheckmark .4s ease-in-out .4s forwards, scaleCheckmark .3s ease-in-out .9s both;
}}
.checkmark-circle {{
stroke-dasharray: 166;
stroke-dashoffset: 166;
stroke-width: 3;
stroke-miterlimit: 10;
stroke: #3FB950;
fill: none;
animation: strokeCircle .6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}}
.checkmark-check {{
transform-origin: 50% 50%;
stroke-dasharray: 48;
stroke-dashoffset: 48;
animation: strokeCheck .3s cubic-bezier(0.65, 0, 0.45, 1) .8s forwards;
}}
@keyframes strokeCircle {{
100% {{ stroke-dashoffset: 0; }}
}}
@keyframes strokeCheck {{
100% {{ stroke-dashoffset: 0; }}
}}
@keyframes fillCheckmark {{
100% {{ box-shadow: inset 0px 0px 0px 30px rgba(63, 185, 80, 0.08); }}
}}
@keyframes scaleCheckmark {{
0%, 100% {{ transform: none; }}
50% {{ transform: scale3d(1.08, 1.08, 1); }}
}}
</style>
<div class="premium-success-card">
<div class="success-icon-container">
<svg class="checkmark-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
<circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
<path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
</svg>
</div>
<div style="font-size:24px; font-weight:800; color:#3FB950; margin-bottom:12px; letter-spacing: -0.5px;">
Forecast Generated Successfully
</div>
<div style="font-size:13.5px; color:#8B949E; max-width:480px; margin:0 auto 28px auto; line-height:1.5;">
The demand planning algorithms and safety stock buffers have been successfully calculated and synchronized.
</div>
<div style="max-width:480px; margin:0 auto 36px auto; text-align:left; font-size:13.5px; color:#C9D1D9; line-height:1.8;">
<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
<span style="color:#3FB950; font-weight:bold;">✓</span> Forecast Generated Successfully
</div>
<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
<span style="color:#3FB950; font-weight:bold;">✓</span> Prediction.csv Created Successfully
</div>
<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
<span style="color:#3FB950; font-weight:bold;">✓</span> Inventory Planning Completed
</div>
<div style="display:flex; align-items:center; gap:10px;">
<span style="color:#3FB950; font-weight:bold;">✓</span> Business Recommendations Ready
</div>
</div>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; max-width:680px; margin:0 auto; text-align:left; background:rgba(13, 17, 23, 0.45); border:1px solid rgba(255,255,255,0.05); border-radius:12px; padding:20px 24px;">
<div>
<span style="color:#8B949E; font-size:10px; text-transform:uppercase; font-weight:700;">Forecast Month</span><br>
<strong style="color:#F0F6FC; font-size:14px;">{f_month}</strong>
</div>
<div>
<span style="color:#8B949E; font-size:10px; text-transform:uppercase; font-weight:700;">Total Materials Processed</span><br>
<strong style="color:#F0F6FC; font-size:14px;">{total_m:,}</strong>
</div>
<div>
<span style="color:#8B949E; font-size:10px; text-transform:uppercase; font-weight:700;">Materials to Purchase</span><br>
<strong style="color:#F0F6FC; font-size:14px;">{req_m:,}</strong>
</div>
<div>
<span style="color:#8B949E; font-size:10px; text-transform:uppercase; font-weight:700;">Est. Purchase Cost</span><br>
<strong style="color:#F0F6FC; font-size:14px;">{fmt_currency(total_c)}</strong>
</div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
    if st.button("🔮   View Forecast Dashboard", type="primary", use_container_width=True):
        st.session_state["active_page"] = "Forecast"
        st.rerun()
