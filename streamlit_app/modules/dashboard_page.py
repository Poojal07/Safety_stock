"""
modules/dashboard_page.py
-------------------------
Main Dashboard — KPI overview and historical analysis charts.
Shown immediately after login.
"""

import pandas as pd
import streamlit as st

from modules.utils import (inject_global_css, kpi_card, section_header,
                            fmt_number, fmt_currency, fmt_compact, add_priority_column)
from modules import charts
from modules.pipeline import get_prediction_path, prediction_exists, DEPLOYMENT_ROOT


def _load_historical() -> pd.DataFrame | None:
    """Try to load the historical dataset from disk."""
    if st.session_state.get("historical_df") is not None:
        return st.session_state["historical_df"]

    hist_path = DEPLOYMENT_ROOT / "Data_SES" / "updated_historical_dataset.csv"
    if hist_path.exists():
        try:
            df = pd.read_csv(hist_path)
            st.session_state["historical_df"] = df
            return df
        except Exception:
            pass
    return None


def _load_prediction() -> pd.DataFrame | None:
    """Try to load the prediction CSV from session state or disk."""
    if st.session_state.get("prediction_df") is not None:
        return st.session_state["prediction_df"]

    pred_path = get_prediction_path()
    if pred_path.exists():
        try:
            df = pd.read_csv(pred_path)
            df = add_priority_column(df)
            st.session_state["prediction_df"]    = df
            st.session_state["prediction_ready"] = True
            return df
        except Exception:
            pass
    return None


def render_dashboard() -> None:
    inject_global_css()

    username = st.session_state.get("user_name", "User")
    st.markdown(f"## 🏠 Executive Command Center")
    st.markdown(
        '<p style="color:#8B949E;margin-top:-8px;font-size:14px;">Welcome back, <b>' + username + '</b>. Here is your enterprise inventory planning overview.</p>',
        unsafe_allow_html=True,
    )

    pred_df = _load_prediction()
    hist_df = _load_historical()

    # ── If no data yet ─────────────────────────────────────────────────────────
    if pred_df is None and hist_df is None:
        st.markdown("""
        <div style="background:rgba(22, 27, 34, 0.45);border:1px dashed rgba(255,255,255,0.08);border-radius:12px;
                    padding:64px 48px;text-align:center;margin-top:24px;backdrop-filter:blur(10px);">
            <div style="font-size:54px;margin-bottom:16px;">📦</div>
            <div style="font-size:22px;font-weight:800;color:#F0F6FC;margin-bottom:10px;">
                No Inventory Data Available
            </div>
            <div style="font-size:14px;color:#8B949E;max-width:420px;margin:0 auto;line-height:1.5;">
                Please upload the client's monthly Excel consumption and lead time files in the 
                <b>Upload Monthly Data</b> section to run the prediction pipeline.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # TOP KPI ROW — from prediction data
    # ══════════════════════════════════════════════════════════════════════════
    if pred_df is not None:
        section_header("Forecast & Operations Summary — Next Cycle")

        total_materials  = len(pred_df)
        total_forecast   = pred_df["forecast_demand"].sum() if "forecast_demand" in pred_df.columns else 0
        order_col        = next((c for c in pred_df.columns if "order_cost" in c.lower()), None)
        total_cost       = pred_df[order_col].sum() if order_col else 0
        order_qty_col    = next((c for c in pred_df.columns if "order_quantity" in c.lower()), None)
        materials_order  = int((pred_df[order_qty_col] > 0).sum()) if order_qty_col else 0
        status_col       = next((c for c in pred_df.columns if "inventory_status" in c.lower()), None)
        critical_count   = int((pred_df[status_col] == "Critical").sum()) if status_col else 0
        ss_col           = next((c for c in pred_df.columns if "safety_stock" in c.lower()), None)
        avg_ss           = pred_df[ss_col].mean() if ss_col else 0
        lt_col           = next((c for c in pred_df.columns if "material_lead_time" in c.lower()), None)
        avg_lt           = pred_df[lt_col].mean() if lt_col else 0
        
        # Calculate new metrics: Inventory Value and Inventory Health Score
        price_col        = next((c for c in pred_df.columns if "moving_price" in c.lower()), None)
        unrest_col       = next((c for c in pred_df.columns if "unrestricted" in c.lower()), None)
        inventory_value  = (pred_df[unrest_col] * pred_df[price_col]).sum() if price_col and unrest_col else 0
        health_score     = (pred_df[status_col] != "Critical").sum() / total_materials * 100 if total_materials and status_col else 100.0

        # Forecast Date label
        date_col         = next((c for c in pred_df.columns if "forecast_date" in c.lower()), None)
        forecast_month   = "—"
        if date_col and len(pred_df) > 0:
            try:
                forecast_month = pd.to_datetime(pred_df[date_col].iloc[0]).strftime("%B %Y")
            except Exception:
                forecast_month = str(pred_df[date_col].iloc[0])

        k1, k2, k3, k4 = st.columns(4)
        with k1: kpi_card("Forecast Month",       forecast_month,               "📅")
        with k2: kpi_card("Total Materials",      fmt_compact(total_materials),  "📦")
        with k3: kpi_card("Est. Purchase Cost",   fmt_currency(total_cost),      "💰")
        with k4: kpi_card("Inventory Asset Value",fmt_currency(inventory_value), "💎")
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        k5, k6, k7, k8 = st.columns(4)
        with k5: kpi_card("Critical Materials",   str(critical_count),           "🚨",
                           "Immediate action needed" if critical_count > 0 else "All systems clear",
                           "#F85149" if critical_count > 0 else "#3FB950")
        with k6: kpi_card("Inventory Health Score",f"{health_score:.1f}%",       "❤️",
                           "Stable buffer levels" if health_score > 90 else "Release procurement buffers",
                           "#3FB950" if health_score > 90 else "#E3B341")
        with k7: kpi_card("Avg Safety Stock",     fmt_compact(avg_ss),           "🛡️")
        with k8: kpi_card("Avg Lead Time",        f"{avg_lt:.1f} Days" if avg_lt else "—", "⏱️")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════════
        # EXECUTIVE SUMMARY & ALERTS GRID
        # ══════════════════════════════════════════════════════════════════════════
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="kpi-card" style="margin-bottom:15px; background: rgba(22, 27, 34, 0.45); border-color: rgba(255,255,255,0.06);">
                <h4 style="margin:0 0 10px 0; color:#58A6FF; font-size:15px;">📊 Monthly Operations Briefing</h4>
                <p style="color:#C9D1D9; font-size:13px; line-height:1.6; margin:0;">
                    During the planning window for <strong>{forecast_month}</strong>, the automated forecasting suite reviewed <strong>{total_materials:,} materials</strong>. 
                    A total purchase allocation of <strong>{fmt_currency(total_cost)}</strong> is recommended across <strong>{materials_order:,} items</strong> ({materials_order/total_materials*100:.1f}% of catalog) to resolve stock deficits.
                    Total active inventory asset valuation is calculated at <strong>{fmt_currency(inventory_value)}</strong>, showing an overall operational safety health score of <strong>{health_score:.1f}%</strong>.
                    Immediate procurement steps are flagged for <strong>{critical_count} materials</strong> to offset stockout threats.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with c_right:
            st.markdown('<div class="section-header">Business Alerts</div>', unsafe_allow_html=True)
            alert_html = ""
            if critical_count > 0:
                alert_html += f"""
                <div class="glowing-critical-card" style="padding:15px; margin-bottom:10px; border-radius:10px; border:1px solid #F85149;">
                    <div style="font-weight:700; color:#FF7B72; font-size:12px; display:flex; align-items:center;">
                        <span class="blink-warning"></span> URGENT STOCKOUT WARNING
                    </div>
                    <div style="color:#C9D1D9; font-size:12px; margin-top:6px;">
                        {critical_count} critical materials have dropped below safety levels. Release purchase approvals.
                    </div>
                </div>
                """
            else:
                alert_html += """
                <div class="kpi-card" style="padding:15px; margin-bottom:10px; border:1px solid rgba(63, 185, 80, 0.3); background:rgba(63, 185, 80, 0.05); border-radius:10px;">
                    <div style="font-weight:700; color:#56D364; font-size:12px;">✓ INVENTORY BALANCED</div>
                    <div style="color:#C9D1D9; font-size:12px; margin-top:6px;">
                        No critical stockouts or supply chain backlogs detected.
                    </div>
                </div>
                """
            
            if total_cost > 500000:
                alert_html += f"""
                <div class="kpi-card" style="padding:15px; border-color:rgba(227, 179, 65, 0.3); background:rgba(227, 179, 65, 0.03); border-radius:10px;">
                    <div style="font-weight:700; color:#F2CC60; font-size:12px;">💰 HIGH PROCUREMENT CAPITAL</div>
                    <div style="color:#C9D1D9; font-size:12px; margin-top:6px;">
                        Allocated capital is high this month ({fmt_currency(total_cost)}). Check top value items for optimization.
                    </div>
                </div>
                """
            st.markdown(alert_html, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # CHARTS ROW 1
    # ══════════════════════════════════════════════════════════════════════════
    if pred_df is not None:
        section_header("Forecast Analysis")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(charts.top_forecast_demand(pred_df, n=10),
                            use_container_width=True)
        with c2:
            st.plotly_chart(charts.top_order_cost(pred_df, n=10),
                            use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # CHARTS ROW 2
    # ══════════════════════════════════════════════════════════════════════════
    if pred_df is not None:
        section_header("Classification & Status")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.plotly_chart(charts.inventory_status_donut(pred_df),
                            use_container_width=True)
        with c2:
            st.plotly_chart(charts.abc_donut(pred_df),
                            use_container_width=True)
        with c3:
            st.plotly_chart(charts.xyz_donut(pred_df),
                            use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # HISTORICAL TREND
    # ══════════════════════════════════════════════════════════════════════════
    if hist_df is not None:
        section_header("Historical Demand Trend")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(charts.demand_trend(hist_df),
                            use_container_width=True)
        with c2:
            if pred_df is not None:
                st.plotly_chart(charts.lead_time_distribution(pred_df),
                                use_container_width=True)
