"""
modules/forecast_page.py
------------------------
Next Month Forecast — the primary page of the application.
Shows KPIs, charts, priority recommendations, smart insights,
and a searchable/filterable forecast table.
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from modules.utils import (
    inject_global_css, kpi_card, section_header,
    fmt_number, fmt_currency, fmt_compact,
    add_priority_column, PRIORITY_CONFIG, PRIORITY_ORDER,
)
from modules import charts
from modules.pipeline import get_prediction_path, DEPLOYMENT_ROOT


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADERS
# ══════════════════════════════════════════════════════════════════════════════

def _load_prediction() -> pd.DataFrame | None:
    if st.session_state.get("prediction_df") is not None:
        df = st.session_state["prediction_df"]
        if "Business_Priority" not in df.columns:
            df = add_priority_column(df)
            st.session_state["prediction_df"] = df
        return df

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


def _load_historical() -> pd.DataFrame | None:
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


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: SINGLE MATERIAL MIN-TREND CHART
# ═══════════════════════════════════════════════════════════════════════════

def _single_material_trend(hist_df: pd.DataFrame, material_id: int, forecast_val: float, forecast_date: str) -> go.Figure:
    """Create a detailed mini-trend chart for a specific material showing history and forecast."""
    mat_hist = hist_df[hist_df["material_id"] == material_id].copy()
    if len(mat_hist) == 0:
        return go.Figure()

    # Determine date columns
    date_col = next((c for c in mat_hist.columns if c.lower() in ("date", "Date")), None)
    demand_col = next((c for c in mat_hist.columns if c.lower() == "demand"), None)
    if not date_col or not demand_col:
        return go.Figure()

    # Sort values chronologically
    mat_hist = mat_hist.sort_values(date_col)

    fig = go.Figure()
    
    # Plot historical actuals
    fig.add_trace(go.Scatter(
        x=mat_hist[date_col], y=mat_hist[demand_col],
        mode="lines+markers",
        line=dict(color="#1F6FEB", width=2.5),
        marker=dict(size=5, color="#58A6FF"),
        name="Actual Demand",
    ))
    
    # Connect last actual to forecast point
    last_actual = mat_hist.iloc[-1]
    fig.add_trace(go.Scatter(
        x=[last_actual[date_col], forecast_date],
        y=[last_actual[demand_col], forecast_val],
        mode="lines",
        line=dict(color="#BC8CFF", width=2.5, dash="dash"),
        name="Forecast Transition",
        showlegend=False
    ))
    
    # Plot forecast star
    fig.add_trace(go.Scatter(
        x=[forecast_date], y=[forecast_val],
        mode="markers",
        marker=dict(size=10, color="#BC8CFF", symbol="star"),
        name="Forecast Month",
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#C9D1D9", family="Inter, sans-serif", size=10),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)"),
        height=250,
        showlegend=True,
        title=dict(text=f"Demand History & Projection for Material {material_id}", font=dict(size=11, color="#F0F6FC"))
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER ENTRY
# ══════════════════════════════════════════════════════════════════════════════

def render_forecast_page() -> None:
    inject_global_css()

    st.markdown("## 🔮 Next Month Forecast Engine")
    st.markdown(
        '<p style="color:#8B949E;margin-top:-8px;font-size:14px;">Review next cycle\'s demand forecasting, safety buffers, and capital requirements.</p>',
        unsafe_allow_html=True,
    )

    df = _load_prediction()
    hist_df = _load_historical()

    if df is None:
        st.markdown("""
        <div style="background:rgba(22, 27, 34, 0.45);border:1px dashed rgba(255,255,255,0.08);border-radius:12px;
                    padding:64px 48px;text-align:center;margin-top:24px;backdrop-filter:blur(10px);">
            <div style="font-size:54px;margin-bottom:16px;">🔮</div>
            <div style="font-size:22px;font-weight:800;color:#F0F6FC;margin-bottom:10px;">
                No Forecast Metrics Compiled
            </div>
            <div style="font-size:14px;color:#8B949E;max-width:420px;margin:0 auto;line-height:1.5;">
                Please upload the consumption and lead time Excel files and execute the processing engine to generate predictions.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Resolve Column Headers exactly
    material_col  = "material_id"
    date_col      = "forecast_date"
    demand_col    = "forecast_demand"
    lt_col        = "material_lead_time"
    price_col     = "moving_price"
    unrest_col    = "unrestricted"
    ss_col        = "Safety_Stock"
    rop_col       = "Reorder_Point"
    gap_col       = "Inventory_Gap"
    order_qty_col = "Order_Quantity"
    cost_col      = "Order_Cost"
    action_col    = "Suggested_Action"
    status_col    = "Inventory_Status"
    lt_cat_col    = "lead_time_category"
    xyz_col       = "xyz_class"
    abc_col       = "abc_class"

    # Determine forecast month label
    forecast_month = "—"
    if date_col in df.columns and len(df) > 0:
        try:
            forecast_month = pd.to_datetime(df[date_col].iloc[0]).strftime("%B %Y")
        except Exception:
            forecast_month = str(df[date_col].iloc[0])

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Forecast Overview",
        "🎯 Priority Recommendation",
        "📦 Material Details",
        "💡 Business Insights"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: FORECAST OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        # ── KPI Cards ─────────────────────────────────────────────────────────
        total_materials = len(df)
        total_forecast  = df[demand_col].sum() if demand_col in df.columns else 0
        materials_order = int((df[order_qty_col] > 0).sum()) if order_qty_col in df.columns else 0
        total_cost      = df[cost_col].sum() if cost_col in df.columns else 0
        avg_demand      = df[demand_col].mean() if demand_col in df.columns else 0
        avg_ss          = df[ss_col].mean() if ss_col in df.columns else 0
        avg_lt          = df[lt_col].mean() if lt_col in df.columns else 0
        critical_count  = int((df[status_col] == "Critical").sum()) if status_col in df.columns else 0
        
        health_score    = 100.0
        if total_materials > 0 and status_col in df.columns:
            health_score = (df[status_col] != "Critical").sum() / total_materials * 100

        k1, k2, k3 = st.columns(3)
        with k1: kpi_card("Forecast Month",       forecast_month,               "📅")
        with k2: kpi_card("Total Materials",      fmt_compact(total_materials),  "📦")
        with k3: kpi_card("Materials to Purchase",str(materials_order),         "🛒",
                           f"{materials_order/total_materials*100:.0f}% of catalog" if total_materials else "")
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        k4, k5, k6 = st.columns(3)
        with k4: kpi_card("Est. Purchase Cost",   fmt_currency(total_cost),     "💰")
        with k5: kpi_card("Avg Forecast Demand",  fmt_compact(avg_demand),      "📈")
        with k6: kpi_card("Avg Safety Stock",     fmt_compact(avg_ss),          "🛡️")
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        k7, k8, k9 = st.columns(3)
        with k7: kpi_card("Avg Lead Time",        f"{avg_lt:.1f} Days" if avg_lt else "—", "⏱️")
        with k8: kpi_card("Inventory Health Score",f"{health_score:.1f}%",       "❤️",
                           "Sufficient buffers" if health_score > 90 else "Action Required",
                           "#3FB950" if health_score > 90 else "#E3B341")
        with k9: kpi_card("Critical Materials",   str(critical_count),          "🚨",
                           "Procure immediately" if critical_count > 0 else "All stocks safe",
                           "#F85149" if critical_count > 0 else "#3FB950")

        # ── Filters & Search Section ──────────────────────────────────────────
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        section_header("🔍 Search & Filter Catalog")
        
        f1, f2, f3 = st.columns([2, 1.5, 1.5])
        with f1:
            search_query = st.text_input("Search by Material ID", placeholder="Enter material code...")
        with f2:
            abc_opts = ["All"] + sorted(df[abc_col].dropna().unique().tolist()) if abc_col in df.columns else ["All"]
            abc_filter = st.selectbox("ABC Class Filter", abc_opts)
        with f3:
            xyz_opts = ["All"] + sorted(df[xyz_col].dropna().unique().tolist()) if xyz_col in df.columns else ["All"]
            xyz_filter = st.selectbox("XYZ Class Filter", xyz_opts)

        f4, f5, f6 = st.columns([1.6, 1.6, 1.8])
        with f4:
            priority_opts = ["All"] + PRIORITY_ORDER
            priority_filter = st.selectbox("Priority Tier Filter", priority_opts)
        with f5:
            lt_cat_opts = ["All"] + sorted(df[lt_cat_col].dropna().unique().tolist()) if lt_cat_col in df.columns else ["All"]
            lt_cat_filter = st.selectbox("Lead Time Bracket Filter", lt_cat_opts)
        with f6:
            cost_filter = st.selectbox("Purchase Cost Bracket", [
                "All Materials",
                "Purchase Required Only (Order Qty > 0)",
                "High Value Orders (> ₹10,000)",
                "Elite Value Orders (> ₹1,000,000)"
            ])

        # Apply Filters
        filtered = df.copy()
        if search_query:
            filtered = filtered[filtered[material_col].astype(str).str.contains(search_query, case=False)]
        if abc_filter != "All" and abc_col in df.columns:
            filtered = filtered[filtered[abc_col] == abc_filter]
        if xyz_filter != "All" and xyz_col in df.columns:
            filtered = filtered[filtered[xyz_col] == xyz_filter]
        if priority_filter != "All" and "Business_Priority" in df.columns:
            filtered = filtered[filtered["Business_Priority"] == priority_filter]
        if lt_cat_filter != "All" and lt_cat_col in df.columns:
            filtered = filtered[filtered[lt_cat_col] == lt_cat_filter]
            
        if cost_filter == "Purchase Required Only (Order Qty > 0)" and order_qty_col in df.columns:
            filtered = filtered[filtered[order_qty_col] > 0]
        elif cost_filter == "High Value Orders (> ₹10,000)" and cost_col in df.columns:
            filtered = filtered[filtered[cost_col] > 10000]
        elif cost_filter == "Elite Value Orders (> ₹1,000,000)" and cost_col in df.columns:
            filtered = filtered[filtered[cost_col] > 1000000]

        # Display Dataframe
        st.caption(f"Showing {len(filtered):,} of {len(df):,} matching planning records")
        
        display_map = {
            material_col: "Material ID",
            "Business_Priority": "Priority",
            demand_col: "Forecast Demand",
            unrest_col: "Current Stock",
            ss_col: "Safety Stock",
            rop_col: "Reorder Point",
            order_qty_col: "Order Qty",
            cost_col: "Order Cost (₹)",
            status_col: "Status"
        }
        cols_to_show = [c for c in display_map if c in filtered.columns]
        table_df = filtered[cols_to_show].rename(columns=display_map)
        for col in table_df.columns:
            if table_df[col].dtype in ("float64", "float32"):
                table_df[col] = table_df[col].round(2)
                
        st.dataframe(table_df, use_container_width=True, hide_index=True, height=350)

        # Export CSV Button
        export_col, _ = st.columns([1, 3])
        with export_col:
            csv_data = filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥  Export Filtered Catalog (CSV)",
                data=csv_data,
                file_name="forecast_planning_filtered.csv",
                mime="text/csv",
                use_container_width=True,
                type="secondary"
            )

        # ── Charts Grid ───────────────────────────────────────────────────────
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        section_header("📈 Forecast Operations Insights")
        
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(charts.top_forecast_demand(filtered, n=20), use_container_width=True)
        with c2:
            st.plotly_chart(charts.top_order_cost(filtered, n=20), use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            if hist_df is not None:
                st.plotly_chart(charts.forecast_trend(hist_df, filtered), use_container_width=True)
            else:
                st.info("Historical demand trend requires raw dataset upload.")
        with c4:
            st.plotly_chart(charts.purchase_cost_distribution(filtered), use_container_width=True)

        c5, c6, c7 = st.columns(3)
        with c5:
            st.plotly_chart(charts.inventory_status_donut(filtered), use_container_width=True)
        with c6:
            st.plotly_chart(charts.forecast_distribution(filtered), use_container_width=True)
        with c7:
            st.plotly_chart(charts.lead_time_distribution(filtered), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: PRIORITY RECOMMENDATION
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        section_header("📋 Procurement Priority Group Recommendations")
        st.markdown(
            '<p style="color:#8B949E;font-size:13px;margin-top:-12px;">Review structured recommendations grouped by SCM importance. High risk items are highlighted with glowing borders.</p>',
            unsafe_allow_html=True,
        )

        # Limit cards display count to keep interface fast
        urgent_df = filtered[filtered[order_qty_col] > 0] if order_qty_col in filtered.columns else filtered
        priority_group = st.selectbox("Select Priority Group to Display", ["All Tiers"] + PRIORITY_ORDER)
        
        display_cards = urgent_df.copy()
        if priority_group != "All Tiers":
            display_cards = display_cards[display_cards["Business_Priority"] == priority_group]

        # Sorting: cost descending
        if cost_col in display_cards.columns:
            display_cards = display_cards.sort_values(cost_col, ascending=False)
            
        limit = 20
        sliced_cards = display_cards.head(limit)
        
        if len(sliced_cards) == 0:
            st.success("🎉 No materials require purchasing in this category!")
        else:
            if len(display_cards) > limit:
                st.caption(f"Displaying top {limit} of {len(display_cards):,} materials. Use filters on Tab 1 to narrow down details.")
                
            for _, row in sliced_cards.iterrows():
                priority = row.get("Business_Priority", "Routine Stock")
                cfg = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG["Routine Stock"])
                
                # Determine risk and impact dynamically
                gap_val = row.get(gap_col, 0) if gap_col in row else 0
                lead_time_val = row.get(lt_col, 0) if lt_col in row else 0
                cost_val = row.get(cost_col, 0) if cost_col in row else 0
                qty_val = row.get(order_qty_col, 0) if order_qty_col in row else 0
                demand_val = row.get(demand_col, 0) if demand_col in row else 0
                unrest_val = row.get(unrest_col, 0) if unrest_col in row else 0
                
                # Check status
                status_val = row.get(status_col, "Sufficient")
                
                # Build custom HTML Card based on criticality
                if priority == "Critical Priority":
                    st.markdown(f"""
                    <div class="glowing-critical-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="font-size:16px; font-weight:800; color:#FF7B72; display:flex; align-items:center; gap:8px;">
                                🚨 Material ID: {row[material_col]}
                            </div>
                            <span class="badge {cfg['badge']}">{priority.upper()}</span>
                        </div>
                        <div style="margin-top:14px; display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:14px;">
                            <div>
                                <span style="color:#8B949E; font-size:11px; text-transform:uppercase;">Forecast Demand</span><br>
                                <strong style="color:#F0F6FC; font-size:14px;">{fmt_number(demand_val)}</strong>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-size:11px; text-transform:uppercase;">Current Stock</span><br>
                                <strong style="color:#F0F6FC; font-size:14px;">{fmt_number(unrest_val)}</strong>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-size:11px; text-transform:uppercase;">Purchase Qty</span><br>
                                <strong style="color:#FF7B72; font-size:14px; font-weight:800;">{fmt_number(qty_val)}</strong>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-size:11px; text-transform:uppercase;">Purchase Cost</span><br>
                                <strong style="color:#FF7B72; font-size:14px; font-weight:800;">{fmt_currency(cost_val)}</strong>
                            </div>
                        </div>
                        <div style="margin-top:12px; display:grid; grid-template-columns: 1fr; gap:8px; font-size:12px; line-height:1.5;">
                            <div>
                                <span style="color:#8B949E; font-weight:700;">Suggested Action:</span> <span style="color:#F0F6FC;">{cfg['action']}</span>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-weight:700;">Reason:</span> <span style="color:#C9D1D9;">{cfg['reason']}</span>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-weight:700;">Business Impact:</span> <span style="color:#FF7B72;">{cfg['impact']}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; color:#8B949E; font-size:11px; margin-top:4px;">
                                <span>Lead Time: <strong>{lead_time_val:.0f} Days</strong></span>
                                <span>Inventory Risk: <strong style="color:#FF7B72;">Stockout Threat (Deficit: {fmt_number(gap_val)})</strong></span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="rec-card {cfg['card']}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="font-size:15px; font-weight:700; color:#F0F6FC; display:flex; align-items:center; gap:8px;">
                                Material ID: {row[material_col]}
                            </div>
                            <span class="badge {cfg['badge']}">{priority.upper()}</span>
                        </div>
                        <div style="margin-top:12px; display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:12px;">
                            <div>
                                <span style="color:#8B949E; font-size:11px; text-transform:uppercase;">Forecast Demand</span><br>
                                <strong style="color:#F0F6FC; font-size:13px;">{fmt_number(demand_val)}</strong>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-size:11px; text-transform:uppercase;">Current Stock</span><br>
                                <strong style="color:#F0F6FC; font-size:13px;">{fmt_number(unrest_val)}</strong>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-size:11px; text-transform:uppercase;">Purchase Qty</span><br>
                                <strong style="color:#C9D1D9; font-size:13px;">{fmt_number(qty_val)}</strong>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-size:11px; text-transform:uppercase;">Purchase Cost</span><br>
                                <strong style="color:#F0F6FC; font-size:13px;">{fmt_currency(cost_val)}</strong>
                            </div>
                        </div>
                        <div style="margin-top:10px; display:grid; grid-template-columns: 1fr; gap:6px; font-size:12px; line-height:1.4;">
                            <div>
                                <span style="color:#8B949E; font-weight:600;">Suggested Action:</span> <span style="color:#C9D1D9;">{cfg['action']}</span>
                            </div>
                            <div>
                                <span style="color:#8B949E; font-weight:600;">Reason:</span> <span style="color:#8B949E;">{cfg['reason']}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; color:#8B949E; font-size:11px; margin-top:2px;">
                                <span>Lead Time: <strong>{lead_time_val:.0f} Days</strong></span>
                                <span>Inventory Risk: <strong style="color:{cfg['color']};">{status_val} Stock Levels</strong></span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: MATERIAL DETAILS
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        section_header("📦 Individual Material Analysis")
        st.markdown(
            '<p style="color:#8B949E;font-size:13px;margin-top:-12px;">Query historical actuals, forecast metrics, safety stock calculations, and reorder patterns for any catalog item.</p>',
            unsafe_allow_html=True,
        )

        select_material = st.selectbox(
            "Select Material ID to Inspect",
            options=sorted(df[material_col].dropna().unique().tolist())
        )

        if select_material:
            mat_row = df[df[material_col] == select_material].iloc[0]
            priority = mat_row.get("Business_Priority", "Routine Stock")
            cfg = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG["Routine Stock"])

            # Extract metrics
            mat_forecast = mat_row.get(demand_col, 0)
            mat_ss       = mat_row.get(ss_col, 0)
            mat_rop      = mat_row.get(rop_col, 0)
            mat_price    = mat_row.get(price_col, 0)
            mat_stock    = mat_row.get(unrest_col, 0)
            mat_gap      = mat_row.get(gap_col, 0)
            mat_qty      = mat_row.get(order_qty_col, 0)
            mat_cost     = mat_row.get(cost_col, 0)
            mat_lt       = mat_row.get(lt_col, 0)
            mat_abc      = mat_row.get(abc_col, "—")
            mat_xyz      = mat_row.get(xyz_col, "—")
            mat_status   = mat_row.get(status_col, "—")
            
            # Lead Time demand is ROP minus Safety Stock
            mat_ltd      = max(0, mat_rop - mat_ss)

            d1, d2 = st.columns([1.5, 2.5])
            with d1:
                # Material Card details
                st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid {cfg['color']}; padding:24px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h3 style="margin:0; font-size:18px;">Material #{select_material}</h3>
                        <span class="badge {cfg['badge']}">{priority.upper()}</span>
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:12px; line-height:1.5;">
                        <div>
                            <span style="color:#8B949E; font-weight:600;">Unit Price:</span><br>
                            <span style="color:#F0F6FC; font-weight:700;">{fmt_currency(mat_price)}</span>
                        </div>
                        <div>
                            <span style="color:#8B949E; font-weight:600;">Lead Time:</span><br>
                            <span style="color:#F0F6FC; font-weight:700;">{mat_lt:.0f} Days</span>
                        </div>
                        <div>
                            <span style="color:#8B949E; font-weight:600;">ABC / XYZ Class:</span><br>
                            <span style="color:#F0F6FC; font-weight:700;">{mat_abc} / {mat_xyz}</span>
                        </div>
                        <div>
                            <span style="color:#8B949E; font-weight:600;">Stock Status:</span><br>
                            <span style="color:{cfg['color']}; font-weight:700;">{mat_status}</span>
                        </div>
                    </div>
                    <hr style="border-color:rgba(255,255,255,0.05); margin:16px 0;">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:11.5px; line-height:1.5;">
                        <div>
                            <span style="color:#8B949E;">Forecast Demand:</span> <strong>{fmt_number(mat_forecast)}</strong>
                        </div>
                        <div>
                            <span style="color:#8B949E;">Current Stock:</span> <strong>{fmt_number(mat_stock)}</strong>
                        </div>
                        <div>
                            <span style="color:#8B949E;">Safety Stock Buffer:</span> <strong>{fmt_number(mat_ss)}</strong>
                        </div>
                        <div>
                            <span style="color:#8B949E;">Reorder Point (ROP):</span> <strong>{fmt_number(mat_rop)}</strong>
                        </div>
                        <div>
                            <span style="color:#8B949E;">Lead Time Demand:</span> <strong>{fmt_number(mat_ltd)}</strong>
                        </div>
                        <div>
                            <span style="color:#8B949E;">Inventory Gap:</span> <strong style="color:{cfg['color']};">{fmt_number(mat_gap)}</strong>
                        </div>
                    </div>
                    <hr style="border-color:rgba(255,255,255,0.05); margin:16px 0;">
                    <div style="font-size:12px;">
                        <span style="color:#8B949E; font-weight:600;">Recommendation:</span><br>
                        <span style="color:#F0F6FC;">Order <strong>{fmt_number(mat_qty)}</strong> units this month, estimated cost <strong>{fmt_currency(mat_cost)}</strong>.</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with d2:
                # Mini trend chart
                if hist_df is not None:
                    pred_date_val = str(mat_row[date_col]) if date_col in mat_row else forecast_month
                    st.plotly_chart(_single_material_trend(hist_df, select_material, mat_forecast, pred_date_val), use_container_width=True)
                else:
                    st.info("Please run the validation pipeline first to enable trend visualizations.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4: BUSINESS INSIGHTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        section_header("💡 Executive Smart Decisions & Insights")
        st.markdown(
            '<p style="color:#8B949E;font-size:13px;margin-top:-12px;">Auto-generated operational insights highlighting critical procurement actions and buffer warnings.</p>',
            unsafe_allow_html=True,
        )

        # ── 1. Immediate Purchase Required ────────────────────────────────────
        critical_items = df[df[status_col] == "Critical"].head(3) if status_col in df.columns else pd.DataFrame()
        if len(critical_items) > 0:
            mat_list = ", ".join(critical_items[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-urgent">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">🚨 Immediate Purchase Required</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Critical stock deficiencies detected on materials: <strong>{mat_list}</strong>. 
                    These items are below safety thresholds and require immediate purchase requisition to prevent production stops.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 2. Risk of Stockout ───────────────────────────────────────────────
        stockout_items = df[df[unrest_col] < df[ss_col]].head(3) if unrest_col in df.columns and ss_col in df.columns else pd.DataFrame()
        if len(stockout_items) > 0:
            mat_list = ", ".join(stockout_items[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-urgent" style="border-color:#F2CC60;">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">⚠️ Buffer Alert — Stockout Risk</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Current unrestricted stock for materials <strong>{mat_list}</strong> has breached safety stock buffers. 
                    Standard operations are exposed to delivery lags. Place orders immediately.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 3. High Lead Time Alert ───────────────────────────────────────────
        long_lt_items = df[df[lt_col] >= 60].head(3) if lt_col in df.columns else pd.DataFrame()
        if len(long_lt_items) > 0:
            mat_list = ", ".join(long_lt_items[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-warning">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">⏱️ Long Lead Time Warnings</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Materials <strong>{mat_list}</strong> have lead times exceeding 60 days. 
                    Ensure order pipelines account for this latency. Review supplier logistics contracts.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 4. High Purchase Cost Concentration ───────────────────────────────
        if cost_col in df.columns:
            top_cost = df.nlargest(5, cost_col)
            combined_cost = top_cost[cost_col].sum()
            cost_pct = (combined_cost / total_cost * 100) if total_cost > 0 else 0
            if combined_cost > 0:
                st.markdown(f"""
                <div class="insight-box insight-info">
                    <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">💰 Capital Allocation Concentration</div>
                    <div style="color:#8B949E;font-size:12.5px;">
                        The top 5 materials by order cost account for <strong>{cost_pct:.0f}%</strong> of total recommended spend ({fmt_currency(combined_cost)}). 
                        Focus price negotiations and volume contracts on these items.
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── 5. Supplier Review Recommended (A-Class & Z-Class) ────────────────
        az_items = df[(df[abc_col] == "A") & (df[xyz_col] == "Z")].head(3) if abc_col in df.columns and xyz_col in df.columns else pd.DataFrame()
        if len(az_items) > 0:
            mat_list = ", ".join(az_items[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-info" style="border-color:#BC8CFF;">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">🤝 Supplier Re-negotiation Advisory</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Materials <strong>{mat_list}</strong> combine high expenditure values (Class A) with erratic demand schedules (Class Z). 
                    Recommend shifting to Consignment stock or Vendor-Managed Inventory (VMI) to transfer stockout risks.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 6. Excess Inventory Alert ─────────────────────────────────────────
        excess_items = df[df[unrest_col] > df[rop_col] * 2].head(3) if unrest_col in df.columns and rop_col in df.columns else pd.DataFrame()
        if len(excess_items) > 0:
            mat_list = ", ".join(excess_items[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-success">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">📦 Overstocked Assets Warning</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Current unrestricted stock for materials <strong>{mat_list}</strong> exceeds twice their reorder points. 
                    Recommend deferring purchase requisitions to reduce inventory carrying fees and locked capital.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 7. Forecast Stable (JIT Candidates) ──────────────────────────────
        jit_items = df[(df[abc_col] == "A") & (df[xyz_col] == "X")].head(3) if abc_col in df.columns and xyz_col in df.columns else pd.DataFrame()
        if len(jit_items) > 0:
            mat_list = ", ".join(jit_items[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-success" style="border-color:#58A6FF;">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">🚀 Just-In-Time (JIT) Opportunities</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Materials <strong>{mat_list}</strong> represent high value (Class A) and extremely stable demand (Class X). 
                    Perfect candidates for JIT replenishment or Kanban releases to reduce warehouse holding costs.
                </div>
            </div>
            """, unsafe_allow_html=True)
