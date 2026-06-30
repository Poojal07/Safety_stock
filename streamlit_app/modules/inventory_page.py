"""
modules/inventory_page.py
-------------------------
Premium Inventory Planning Dashboard - modeled after SAP Inventory Planning
and Oracle SCM Cloud. Provides overview KPIs, purchase planning matrices,
inventory risk alerts, and cost allocation analytics.
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from modules.utils import (
    inject_global_css, kpi_card, section_header,
    fmt_number, fmt_currency, fmt_compact,
    add_priority_column, PRIORITY_CONFIG, PRIORITY_ORDER
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


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER ENTRY
# ══════════════════════════════════════════════════════════════════════════════

def render_inventory_page() -> None:
    inject_global_css()

    st.markdown("## 📦 Enterprise Inventory Planning Suite")
    st.markdown(
        '<p style="color:#8B949E;margin-top:-8px;font-size:14px;">Establish safety stocks, analyze lead time variances, and determine next cycle\'s optimal purchase requisitions.</p>',
        unsafe_allow_html=True,
    )

    df = _load_prediction()

    if df is None:
        st.markdown("""
        <div style="background:rgba(22, 27, 34, 0.45);border:1px dashed rgba(255,255,255,0.08);border-radius:12px;
                    padding:64px 48px;text-align:center;margin-top:24px;backdrop-filter:blur(10px);">
            <div style="font-size:54px;margin-bottom:16px;">📦</div>
            <div style="font-size:22px;font-weight:800;color:#F0F6FC;margin-bottom:10px;">
                No Inventory Plan Compiled
            </div>
            <div style="font-size:14px;color:#8B949E;max-width:420px;margin:0 auto;line-height:1.5;">
                Please upload the client consumption spreadsheets and run the validation engine to generate inventory plans.
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
    status_col    = "Inventory_Status"
    lt_cat_col    = "lead_time_category"
    xyz_col       = "xyz_class"
    abc_col       = "abc_class"

    # Pre-calculate active metrics
    if "Inventory_Value" not in df.columns:
        df["Inventory_Value"] = df[unrest_col] * df[price_col]

    # ══════════════════════════════════════════════════════════════════════════
    # GLOBAL FILTER BAR
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    section_header("🔍 Portfolio Planning Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_q = st.text_input("Material Search", placeholder="Enter material code...")
    with col2:
        priority_opts = ["All Tiers"] + PRIORITY_ORDER
        priority_sel = st.selectbox("Priority Tier", priority_opts)
    with col3:
        status_opts = ["All Tiers"] + sorted(df[status_col].dropna().unique().tolist()) if status_col in df.columns else ["All Tiers"]
        status_sel = st.selectbox("Inventory Status Class", status_opts)
    with col4:
        lt_opts = ["All Tiers"] + sorted(df[lt_cat_col].dropna().unique().tolist()) if lt_cat_col in df.columns else ["All Tiers"]
        lt_sel = st.selectbox("Lead Time Category", lt_opts)

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        abc_opts = ["All Tiers"] + sorted(df[abc_col].dropna().unique().tolist()) if abc_col in df.columns else ["All Tiers"]
        abc_sel = st.selectbox("ABC Classification", abc_opts)
    with col6:
        xyz_opts = ["All Tiers"] + sorted(df[xyz_col].dropna().unique().tolist()) if xyz_col in df.columns else ["All Tiers"]
        xyz_sel = st.selectbox("XYZ Classification", xyz_opts)
    with col7:
        cost_sel = st.selectbox("Procurement Cost Filter", [
            "All Costs",
            "Invoicing Required (> ₹0)",
            "High Capital Orders (> ₹10,000)",
            "Elite Capital Orders (> ₹1,000,000)"
        ])
    with col8:
        qty_sel = st.selectbox("Order Quantity Filter", [
            "All Quantities",
            "Replenishment Required Only (Qty > 0)",
            "Zero Orders Only (Qty = 0)"
        ])

    # Apply filters dynamically
    filtered = df.copy()
    if search_q:
        filtered = filtered[filtered[material_col].astype(str).str.contains(search_q, case=False)]
    if priority_sel != "All Tiers":
        filtered = filtered[filtered["Business_Priority"] == priority_sel]
    if status_sel != "All Tiers" and status_col in filtered.columns:
        filtered = filtered[filtered[status_col] == status_sel]
    if lt_sel != "All Tiers" and lt_cat_col in filtered.columns:
        filtered = filtered[filtered[lt_cat_col] == lt_sel]
    if abc_sel != "All Tiers" and abc_col in filtered.columns:
        filtered = filtered[filtered[abc_col] == abc_sel]
    if xyz_sel != "All Tiers" and xyz_col in filtered.columns:
        filtered = filtered[filtered[xyz_col] == xyz_sel]
        
    if cost_sel == "Invoicing Required (> ₹0)" and cost_col in filtered.columns:
        filtered = filtered[filtered[cost_col] > 0]
    elif cost_sel == "High Capital Orders (> ₹10,000)" and cost_col in filtered.columns:
        filtered = filtered[filtered[cost_col] > 10000]
    elif cost_sel == "Elite Capital Orders (> ₹1,000,000)" and cost_col in filtered.columns:
        filtered = filtered[filtered[cost_col] > 1000000]
        
    if qty_sel == "Replenishment Required Only (Qty > 0)" and order_qty_col in filtered.columns:
        filtered = filtered[filtered[order_qty_col] > 0]
    elif qty_sel == "Zero Orders Only (Qty = 0)" and order_qty_col in filtered.columns:
        filtered = filtered[filtered[order_qty_col] == 0]

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Inventory Overview",
        "🛒 Purchase Plan",
        "⚠️ Inventory Risk Alerts",
        "📊 Cost & Budget Analysis"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: INVENTORY OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 📊 Portfolio Buffer Health Summary")

        # Stats calculations
        total_materials = len(filtered)
        materials_order = int((filtered[order_qty_col] > 0).sum()) if order_qty_col in filtered.columns else 0
        avg_ss          = filtered[ss_col].mean() if ss_col in filtered.columns else 0
        avg_lt          = filtered[lt_col].mean() if lt_col in filtered.columns else 0
        avg_rop         = filtered[rop_col].mean() if rop_col in filtered.columns else 0
        total_qty       = filtered[order_qty_col].sum() if order_qty_col in filtered.columns else 0
        total_cost      = filtered[cost_col].sum() if cost_col in filtered.columns else 0
        critical_count  = int((filtered[status_col] == "Critical").sum()) if status_col in filtered.columns else 0
        
        health_score    = 100.0
        if total_materials > 0 and status_col in filtered.columns:
            health_score = (filtered[status_col] != "Critical").sum() / total_materials * 100
            
        coverage_series = filtered[unrest_col] / filtered[demand_col].replace(0, 0.001) if unrest_col in filtered.columns and demand_col in filtered.columns else pd.Series()
        avg_coverage    = coverage_series[coverage_series <= 24].mean() if len(coverage_series) > 0 else 0

        # KPI Columns
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: kpi_card("Total Materials",      fmt_compact(total_materials),  "📦")
        with k2: kpi_card("Re-orders Needed",     str(materials_order),         "🛒",
                           f"{materials_order/total_materials*100:.0f}% catalog" if total_materials else "")
        with k3: kpi_card("Avg Safety Buffer",    fmt_compact(avg_ss),          "🛡️")
        with k4: kpi_card("Avg Lead Time",        f"{avg_lt:.1f} Days" if avg_lt else "—", "⏱️")
        with k5: kpi_card("Avg Reorder Pt (ROP)", fmt_compact(avg_rop),         "⚓")

        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

        k6, k7, k8, k9, k10 = st.columns(5)
        with k6: kpi_card("Total Purchase Qty",   fmt_compact(total_qty),       "🚚")
        with k7: kpi_card("Est. Purchase Cost",   fmt_currency(total_cost),     "💰")
        with k8: kpi_card("Inventory Health",     f"{health_score:.1f}%",       "❤️",
                           "No stockouts" if health_score > 90 else "Deficit Alerts",
                           "#3FB950" if health_score > 90 else "#E3B341")
        with k9: kpi_card("Critical Items",       str(critical_count),          "🚨",
                           "Immediate order" if critical_count > 0 else "All stocks clear",
                           "#F85149" if critical_count > 0 else "#3FB950")
        with k10: kpi_card("Avg Stock Coverage",  f"{avg_coverage:.1f} Mon" if avg_coverage else "—", "⏳")

        # Distribution Charts
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(charts.inventory_status_donut(filtered), use_container_width=True)
        with c2:
            st.plotly_chart(charts.safety_stock_distribution(filtered), use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(charts.lead_time_distribution(filtered), use_container_width=True)
        with c4:
            st.plotly_chart(charts.rop_distribution(filtered), use_container_width=True)

        c5, c6 = st.columns(2)
        with c5:
            st.plotly_chart(charts.inventory_gap_distribution(filtered), use_container_width=True)
        with c6:
            st.plotly_chart(charts.purchase_qty_distribution(filtered), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: PURCHASE PLAN
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        section_header("🛒 Next Cycle Purchase Requisitions Table")
        st.markdown(
            '<p style="color:#8B949E;font-size:13px;margin-top:-12px;">Detailed purchase recommendations. Use sort filters to prioritize purchase orders.</p>',
            unsafe_allow_html=True,
        )

        # Sort options
        s1, s2, _ = st.columns([2, 2, 4])
        with s1:
            sort_by = st.selectbox("Sort Table Requisitions", [
                "Suggested Order Cost (High → Low)",
                "Suggested Order Qty (High → Low)",
                "Material Code (Ascending)"
            ])
        with s2:
            display_count = st.selectbox("Items per Page", [50, 100, 200, "All"])

        # Apply Sort
        plan_df = filtered.copy()
        if sort_by == "Suggested Order Cost (High → Low)" and cost_col in plan_df.columns:
            plan_df = plan_df.sort_values(cost_col, ascending=False)
        elif sort_by == "Suggested Order Qty (High → Low)" and order_qty_col in plan_df.columns:
            plan_df = plan_df.sort_values(order_qty_col, ascending=False)
        else:
            plan_df = plan_df.sort_values(material_col)

        # Display Dataframe
        display_map = {
            material_col: "Material ID",
            demand_col: "Forecast Demand",
            unrest_col: "Current Stock",
            ss_col: "Safety Stock",
            "lead_time_demand": "Lead Time Demand",
            rop_col: "Reorder Point",
            gap_col: "Inventory Gap",
            order_qty_col: "Order Quantity",
            cost_col: "Order Cost (₹)",
            lt_col: "Lead Time (Days)",
            status_col: "Inventory Status",
            "Business_Priority": "Priority"
        }

        # Calculate lead time demand dynamically for display if not present
        if "lead_time_demand" not in plan_df.columns:
            plan_df["lead_time_demand"] = (plan_df[rop_col] - plan_df[ss_col]).clip(lower=0)

        cols_to_display = [c for c in display_map if c in plan_df.columns]
        plan_table = plan_df[cols_to_display].rename(columns=display_map)
        
        # Round values
        for col in plan_table.columns:
            if plan_table[col].dtype in ("float64", "float32"):
                plan_table[col] = plan_table[col].round(1)

        # Apply display slice
        if display_count != "All":
            plan_table_view = plan_table.head(int(display_count))
        else:
            plan_table_view = plan_table

        st.dataframe(
            plan_table_view,
            use_container_width=True,
            hide_index=True,
            height=420
        )

        # Download Requisition Sheet
        export_col, _ = st.columns([1.5, 3.5])
        with export_col:
            csv_data = plan_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥  Export Requisition Ledger (CSV)",
                data=csv_data,
                file_name="procurement_purchase_plan.csv",
                mime="text/csv",
                use_container_width=True,
                type="secondary"
            )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: INVENTORY RISK ALERTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        section_header("⚠️ Supply Chain Operational Risk Alerts")
        st.markdown(
            '<p style="color:#8B949E;font-size:13px;margin-top:-12px;">Executive review of critical stock imbalances, lead time alerts, and supplier dependencies.</p>',
            unsafe_allow_html=True,
        )

        r_col1, r_col2 = st.columns(2)
        
        with r_col1:
            # 1. Critical Materials
            crit_df = filtered[filtered[status_col] == "Critical"] if status_col in filtered.columns else pd.DataFrame()
            crit_count = len(crit_df)
            if crit_count > 0:
                crit_list = ", ".join(crit_df[material_col].head(4).astype(str).tolist())
                st.markdown(f"""
                <div class="glowing-critical-card" style="margin-bottom:16px; padding:20px;">
                    <div style="font-weight:800; color:#FF7B72; font-size:14.5px; margin-bottom:6px; display:flex; align-items:center; gap:8px;">
                        🔴 Critical Stock Deficits Detected ({crit_count} Materials)
                    </div>
                    <div style="color:#8B949E; font-size:12.5px; line-height:1.5;">
                        Materials <strong>{crit_list}</strong> have stock balances depleted below safety lines. 
                        <strong>Suggested Action:</strong> Release weekly purchase orders immediately.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="insight-box insight-success" style="margin-bottom:16px;">
                    <div style="font-weight:700; color:#F0F6FC; font-size:13.5px; margin-bottom:4px;">✓ Stockout Risks Neutralized</div>
                    <div style="color:#8B949E; font-size:12px;">All active catalog codes maintain stocks above safety thresholds.</div>
                </div>
                """, unsafe_allow_html=True)

            # 2. Long Lead Time Alerts
            long_lt_df = filtered[filtered[lt_col] >= 60] if lt_col in filtered.columns else pd.DataFrame()
            if len(long_lt_df) > 0:
                lt_list = ", ".join(long_lt_df[material_col].head(4).astype(str).tolist())
                st.markdown(f"""
                <div class="insight-box insight-warning" style="margin-bottom:16px; padding:18px;">
                    <div style="font-weight:700; color:#F0F6FC; font-size:13.5px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                        ⏱️ Extreme Lead Time Risks ({len(long_lt_df)} Materials)
                    </div>
                    <div style="color:#8B949E; font-size:12.5px; line-height:1.4;">
                        Materials <strong>{lt_list}</strong> have lead latency exceeding 60 days. 
                        <strong>Suggested Action:</strong> Review local spot-market buffers and dual-source contracts.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 3. Supplier Attention Needed (A-Class & Z-Class)
            az_df = filtered[(filtered[abc_col] == "A") & (filtered[xyz_col] == "Z")] if abc_col in filtered.columns and xyz_col in filtered.columns else pd.DataFrame()
            if len(az_df) > 0:
                az_list = ", ".join(az_df[material_col].head(4).astype(str).tolist())
                st.markdown(f"""
                <div class="insight-box insight-info" style="border-color:#BC8CFF; margin-bottom:16px; padding:18px;">
                    <div style="font-weight:700; color:#F0F6FC; font-size:13.5px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                        🤝 High Value Erratic Assets (ABC-A / XYZ-Z)
                    </div>
                    <div style="color:#8B949E; font-size:12.5px; line-height:1.4;">
                        Materials <strong>{az_list}</strong> combine highest carrying value with extreme consumption volatility.
                        <strong>Suggested Action:</strong> Shift to Consignment stocking agreements.
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with r_col2:
            # 4. Understock Buffer Risk
            under_df = filtered[filtered[status_col] == "Understock"] if status_col in filtered.columns else pd.DataFrame()
            if len(under_df) > 0:
                under_list = ", ".join(under_df[material_col].head(4).astype(str).tolist())
                st.markdown(f"""
                <div class="insight-box insight-warning" style="border-color:#F2CC60; margin-bottom:16px; padding:18px;">
                    <div style="font-weight:700; color:#F0F6FC; font-size:13.5px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                        ⚠️ Warning: Understock Buffer Breached ({len(under_df)} Materials)
                    </div>
                    <div style="color:#8B949E; font-size:12.5px; line-height:1.4;">
                        Materials <strong>{under_list}</strong> have breached reorder thresholds but aren't critical yet. 
                        <strong>Suggested Action:</strong> Queue monthly replenishment orders now.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 5. Overstocked Capital Holdings
            over_df = filtered[filtered[status_col] == "Overstock"] if status_col in filtered.columns else pd.DataFrame()
            if len(over_df) > 0:
                over_list = ", ".join(over_df[material_col].head(4).astype(str).tolist())
                st.markdown(f"""
                <div class="insight-box insight-success" style="margin-bottom:16px; padding:18px;">
                    <div style="font-weight:700; color:#F0F6FC; font-size:13.5px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                        📦 Cash Carry Locks: Excess Overstock ({len(over_df)} Materials)
                    </div>
                    <div style="color:#8B949E; font-size:12.5px; line-height:1.4;">
                        Materials <strong>{over_list}</strong> represent surplus stock twice their reorder bounds. 
                        <strong>Suggested Action:</strong> Defer purchase orders to optimize working capital.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 6. Safety Stock Calibration Needed
            # Materials with highly variable demand (XYZ Class Z) but standard safety stock
            variable_df = filtered[filtered[xyz_col] == "Z"] if xyz_col in filtered.columns else pd.DataFrame()
            if len(variable_df) > 0:
                var_list = ", ".join(variable_df[material_col].head(4).astype(str).tolist())
                st.markdown(f"""
                <div class="insight-box insight-info" style="margin-bottom:16px; padding:18px;">
                    <div style="font-weight:700; color:#F0F6FC; font-size:13.5px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                        🛡️ Safety Buffer Calibration Needed ({len(variable_df)} Materials)
                    </div>
                    <div style="color:#8B949E; font-size:12.5px; line-height:1.4;">
                        Materials <strong>{var_list}</strong> show erratic consumption patterns. 
                        <strong>Suggested Action:</strong> Increase safety buffer factors to mitigate unexpected demand spikes.
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4: COST & BUDGET ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### 📊 Budget Allocation & Procurement Costs")

        # KPIs
        total_budget  = filtered[cost_col].sum() if cost_col in filtered.columns else 0
        avg_mat_cost  = filtered[cost_col].mean() if cost_col in filtered.columns else 0
        peak_cost     = filtered[cost_col].max() if cost_col in filtered.columns else 0
        min_cost      = filtered[filtered[cost_col] > 0][cost_col].min() if cost_col in filtered.columns else 0
        avg_val       = filtered["Inventory_Value"].mean() if "Inventory_Value" in filtered.columns else 0

        ck1, ck2, ck3, ck4, ck5 = st.columns(5)
        with ck1: kpi_card("Total Order Budget",   fmt_currency(total_budget),  "💰")
        with ck2: kpi_card("Avg Order Cost",       fmt_currency(avg_mat_cost),  "📊")
        with ck3: kpi_card("Peak Material Cost",   fmt_currency(peak_cost),     "⚡")
        with ck4: kpi_card("Min Active Cost",      fmt_currency(min_cost) if pd.notna(min_cost) else "₹0", "🏷️")
        with ck5: kpi_card("Avg Active Assets",    fmt_currency(avg_val),       "🏛️")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        cc1, cc2 = st.columns(2)
        with cc1:
            st.plotly_chart(charts.cost_by_priority(filtered), use_container_width=True)
        with cc2:
            st.plotly_chart(charts.cost_by_status(filtered), use_container_width=True)

        cc3, cc4 = st.columns(2)
        with cc3:
            st.plotly_chart(charts.forecast_vs_cost(filtered), use_container_width=True)
        with cc4:
            st.plotly_chart(charts.purchase_cost_distribution(filtered), use_container_width=True)

        cc5, cc6 = st.columns(2)
        with cc5:
            st.plotly_chart(charts.inventory_value_distribution(filtered), use_container_width=True)
        with cc6:
            st.plotly_chart(charts.moving_price_distribution(filtered), use_container_width=True)
