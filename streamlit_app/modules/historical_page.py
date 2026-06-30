"""
modules/historical_page.py
--------------------------
Premium Historical Analytics Dashboard - designed for inventory managers.
Shows actual demand behavior, material trends, lead times, stock distributions,
and executive portfolio insights.
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from modules.utils import (
    inject_global_css, kpi_card, section_header,
    fmt_number, fmt_currency, fmt_compact,
    add_priority_column, PRIORITY_CONFIG
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
# MAIN RENDER ENTRY
# ══════════════════════════════════════════════════════════════════════════════

def render_historical_page() -> None:
    inject_global_css()

    st.markdown("## 📈 Historical Analytics Console")
    st.markdown(
        '<p style="color:#8B949E;margin-top:-8px;font-size:14px;">Explore historical consumption patterns, unit costs, and inventory asset profiles.</p>',
        unsafe_allow_html=True,
    )

    pred_df = _load_prediction()
    hist_df = _load_historical()

    if pred_df is None or hist_df is None:
        st.markdown("""
        <div style="background:rgba(22, 27, 34, 0.45);border:1px dashed rgba(255,255,255,0.08);border-radius:12px;
                    padding:64px 48px;text-align:center;margin-top:24px;backdrop-filter:blur(10px);">
            <div style="font-size:54px;margin-bottom:16px;">📈</div>
            <div style="font-size:22px;font-weight:800;color:#F0F6FC;margin-bottom:10px;">
                Insufficient Data to Plot History
            </div>
            <div style="font-size:14px;color:#8B949E;max-width:420px;margin:0 auto;line-height:1.5;">
                Please run the ingestion pipeline to compile historical records and planning parameters first.
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
    if "Inventory_Value" not in pred_df.columns:
        pred_df["Inventory_Value"] = pred_df[unrest_col] * pred_df[price_col]

    # Convert historical dates
    hist_df["Date"] = pd.to_datetime(hist_df["Date"])

    # ══════════════════════════════════════════════════════════════════════════
    # GLOBAL FILTER CONTAINER
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    section_header("🔍 Portfolio Dynamic Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_q = st.text_input("Material Search", placeholder="Enter material code...")
    with col2:
        min_date = hist_df["Date"].min()
        max_date = hist_df["Date"].max()
        date_range = st.date_input(
            "Historical Date Range", 
            [min_date, max_date], 
            min_value=min_date, 
            max_value=max_date
        )
    with col3:
        abc_opts = ["All"] + sorted(pred_df[abc_col].dropna().unique().tolist())
        abc_sel = st.selectbox("ABC Category", abc_opts)
    with col4:
        xyz_opts = ["All"] + sorted(pred_df[xyz_col].dropna().unique().tolist())
        xyz_sel = st.selectbox("XYZ Predictability", xyz_opts)

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        lt_opts = ["All"] + sorted(pred_df[lt_cat_col].dropna().unique().tolist())
        lt_sel = st.selectbox("Lead Time Category Filter", lt_opts)
    with col6:
        min_dem = float(pred_df[demand_col].min()) if demand_col in pred_df.columns else 0.0
        max_dem = float(pred_df[demand_col].max()) if demand_col in pred_df.columns else 10000.0
        demand_range = st.slider("Demand Volatility Range", min_dem, max_dem, (min_dem, max_dem))
    with col7:
        min_val = float(pred_df["Inventory_Value"].min())
        max_val = float(pred_df["Inventory_Value"].max())
        val_range = st.slider("Asset Valuation (₹)", min_val, max_val, (min_val, max_val))
    with col8:
        min_pr = float(pred_df[price_col].min())
        max_pr = float(pred_df[price_col].max())
        price_range = st.slider("Unit Moving Price (₹)", min_pr, max_pr, (min_pr, max_pr))

    # Apply filters dynamically
    filtered_pred = pred_df.copy()
    if search_q:
        filtered_pred = filtered_pred[filtered_pred[material_col].astype(str).str.contains(search_q, case=False)]
    if abc_sel != "All":
        filtered_pred = filtered_pred[filtered_pred[abc_col] == abc_sel]
    if xyz_sel != "All":
        filtered_pred = filtered_pred[filtered_pred[xyz_col] == xyz_sel]
    if lt_sel != "All":
        filtered_pred = filtered_pred[filtered_pred[lt_cat_col] == lt_sel]
    
    filtered_pred = filtered_pred[
        (filtered_pred[demand_col] >= demand_range[0]) & 
        (filtered_pred[demand_col] <= demand_range[1])
    ]
    filtered_pred = filtered_pred[
        (filtered_pred["Inventory_Value"] >= val_range[0]) & 
        (filtered_pred["Inventory_Value"] <= val_range[1])
    ]
    filtered_pred = filtered_pred[
        (filtered_pred[price_col] >= price_range[0]) & 
        (filtered_pred[price_col] <= price_range[1])
    ]

    # Dynamically align historical records
    filtered_hist = hist_df[hist_df["material_id"].isin(filtered_pred[material_col])].copy()
    
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        filtered_hist = filtered_hist[(filtered_hist["Date"] >= start_date) & (filtered_hist["Date"] <= end_date)]

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Demand Analytics",
        "📊 Inventory Analytics",
        "📦 Material Insights",
        "💡 Business Summary"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: DEMAND ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 📊 Demands & Consumption Overview")
        
        # Calculate demand KPIs
        total_records = len(filtered_hist)
        unique_mat    = filtered_hist["material_id"].nunique()
        
        # Monthly totals
        monthly_sums = filtered_hist.groupby(filtered_hist["Date"].dt.to_period("M"))["Demand"].sum()
        avg_monthly  = monthly_sums.mean() if len(monthly_sums) > 0 else 0
        peak_monthly = monthly_sums.max() if len(monthly_sums) > 0 else 0
        low_monthly  = monthly_sums.min() if len(monthly_sums) > 0 else 0
        
        # Variability
        volatility = (monthly_sums.std() / avg_monthly * 100) if len(monthly_sums) > 0 and avg_monthly > 0 else 0
        avg_lead_t = filtered_pred[lt_col].mean() if len(filtered_pred) > 0 else 0
        timespan   = f"{len(monthly_sums)} Months" if len(monthly_sums) > 0 else "—"

        k1, k2, k3, k4 = st.columns(4)
        with k1: kpi_card("Total Historical Records", fmt_compact(total_records), "📋")
        with k2: kpi_card("Active Catalog Items",   fmt_compact(unique_mat),    "📦")
        with k3: kpi_card("Avg Monthly Demand",    fmt_compact(avg_monthly),   "📈")
        with k4: kpi_card("Highest Month Volume",   fmt_compact(peak_monthly),  "⚡")

        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

        k5, k6, k7, k8 = st.columns(4)
        with k5: kpi_card("Lowest Month Volume",    fmt_compact(low_monthly),   "📉")
        with k6: kpi_card("Demand Volatility (CV)",  f"{volatility:.1f}%",       "📊",
                           "Highly Erratic" if volatility > 50 else "Stable Behavior",
                           "#FF7B72" if volatility > 50 else "#3FB950")
        with k7: kpi_card("Avg Lead Time",          f"{avg_lead_t:.1f} Days",   "⏱️")
        with k8: kpi_card("Historical Horizon",     timespan,                   "📅")

        # Demand Charts Grid
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(charts.demand_trend(filtered_hist), use_container_width=True)
        with c2:
            st.plotly_chart(charts.yearly_demand_trend(filtered_hist), use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(charts.rolling_average_trend(filtered_hist), use_container_width=True)
        with c4:
            st.plotly_chart(charts.demand_seasonality(filtered_hist), use_container_width=True)

        c5, c6 = st.columns(2)
        with c5:
            # Heatmap
            st.plotly_chart(charts.consumption_heatmap(filtered_hist), use_container_width=True)
        with c6:
            # Top 20 historical consumption materials
            top_mat = filtered_hist.groupby("material_id")["Demand"].sum().reset_index().nlargest(20, "Demand")
            top_mat["material_id"] = top_mat["material_id"].astype(str)
            top_mat = top_mat.sort_values("Demand", ascending=False)
            height = max(600, len(top_mat) * 35)
            fig_top = px.bar(
                top_mat, x="Demand", y="material_id",
                orientation="h", color_discrete_sequence=["#58A6FF"],
                labels={"Demand": "Total Ingested Demand", "material_id": "Material ID"},
                height=height,
            )
            fig_top.update_traces(
                texttemplate="%{x:,.0f}",
                textposition="outside",
                hovertemplate="<b>Material ID:</b> %{y}<br><b>Total Historical Demand:</b> %{x:,.0f} Units<extra></extra>"
            )
            fig_top.update_layout(
                yaxis=dict(type="category", autorange="reversed"),
                bargap=0.25
            )
            st.plotly_chart(charts._apply_theme(fig_top, "Top 20 Materials by Historical Volume"), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: INVENTORY ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🛡️ Active Asset Valuation & Coverage")

        # Asset KPIs
        avg_value = filtered_pred["Inventory_Value"].mean() if len(filtered_pred) > 0 else 0
        avg_price = filtered_pred[price_col].mean() if len(filtered_pred) > 0 else 0
        avg_stock = filtered_pred[unrest_col].mean() if len(filtered_pred) > 0 else 0
        
        health = 100.0
        if len(filtered_pred) > 0 and status_col in filtered_pred.columns:
            health = (filtered_pred[status_col] != "Critical").sum() / len(filtered_pred) * 100

        ik1, ik2, ik3, ik4 = st.columns(4)
        with ik1: kpi_card("Avg Inventory Value",   fmt_currency(avg_value),  "💰")
        with ik2: kpi_card("Avg Moving Price",      fmt_currency(avg_price),  "🏷️")
        with ik3: kpi_card("Avg Stock Balance",     fmt_compact(avg_stock),   "📦")
        with ik4: kpi_card("Portfolio Health Score", f"{health:.1f}%",        "❤️",
                           "All stocks clear" if health > 90 else "Action Required",
                           "#3FB950" if health > 90 else "#E3B341")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        ic1, ic2 = st.columns(2)
        with ic1:
            st.plotly_chart(charts.abc_xyz_matrix(filtered_pred), use_container_width=True)
        with ic2:
            st.plotly_chart(charts.inventory_value_distribution(filtered_pred), use_container_width=True)

        ic3, ic4 = st.columns(2)
        with ic3:
            st.plotly_chart(charts.stock_distribution(filtered_pred), use_container_width=True)
        with ic4:
            st.plotly_chart(charts.material_coverage_distribution(filtered_pred), use_container_width=True)

        ic5, ic6 = st.columns(2)
        with ic5:
            st.plotly_chart(charts.moving_price_distribution(filtered_pred), use_container_width=True)
        with ic6:
            st.plotly_chart(charts.lead_time_distribution(filtered_pred), use_container_width=True)

        ic7, ic8 = st.columns(2)
        with ic7:
            st.plotly_chart(charts.purchase_cost_distribution(filtered_pred), use_container_width=True)
        with ic8:
            # Side-by-side ABC and XYZ donuts
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.plotly_chart(charts.abc_donut(filtered_pred), use_container_width=True)
            with d_col2:
                st.plotly_chart(charts.xyz_donut(filtered_pred), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: MATERIAL INSIGHTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 🔎 Specific Material Inquest")
        
        select_material = st.selectbox(
            "Choose Material ID to Audit",
            options=sorted(filtered_pred[material_col].dropna().unique().tolist())
        )

        if select_material:
            mat_row = filtered_pred[filtered_pred[material_col] == select_material].iloc[0]
            priority = mat_row.get("Business_Priority", "Routine Stock")
            cfg = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG["Routine Stock"])

            # Extract metrics
            mat_forecast = mat_row.get(demand_col, 0)
            mat_ss       = mat_row.get(ss_col, 0)
            mat_rop      = mat_row.get(rop_col, 0)
            mat_price    = mat_row.get(price_col, 0)
            mat_stock    = mat_row.get(unrest_col, 0)
            mat_gap      = mat_row.get(gap_col, 0)
            mat_val      = mat_row.get("Inventory_Value", 0)
            mat_qty      = mat_row.get(order_qty_col, 0)
            mat_cost     = mat_row.get(cost_col, 0)
            mat_lt       = mat_row.get(lt_col, 0)
            mat_abc      = mat_row.get(abc_col, "—")
            mat_xyz      = mat_row.get(xyz_col, "—")
            mat_status   = mat_row.get(status_col, "—")

            d1, d2 = st.columns([1.5, 2.5])
            with d1:
                # Material Card details
                st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid {cfg['color']}; padding:24px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h3 style="margin:0; font-size:18px;">Audit ID #{select_material}</h3>
                        <span class="badge {cfg['badge']}">{priority.upper()}</span>
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:12px; line-height:1.5;">
                        <div>
                            <span style="color:#8B949E; font-weight:600;">Moving Price:</span><br>
                            <span style="color:#F0F6FC; font-weight:700;">{fmt_currency(mat_price)}</span>
                        </div>
                        <div>
                            <span style="color:#8B949E; font-weight:600;">Stock Value:</span><br>
                            <span style="color:#F0F6FC; font-weight:700;">{fmt_currency(mat_val)}</span>
                        </div>
                        <div>
                            <span style="color:#8B949E; font-weight:600;">ABC / XYZ Class:</span><br>
                            <span style="color:#F0F6FC; font-weight:700;">{mat_abc} / {mat_xyz}</span>
                        </div>
                        <div>
                            <span style="color:#8B949E; font-weight:600;">Lead Time:</span><br>
                            <span style="color:#F0F6FC; font-weight:700;">{mat_lt:.0f} Days</span>
                        </div>
                    </div>
                    <hr style="border-color:rgba(255,255,255,0.05); margin:16px 0;">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; font-size:11.5px; line-height:1.5;">
                        <div>
                            <span style="color:#8B949E;">Current Stock:</span> <strong>{fmt_number(mat_stock)}</strong>
                        </div>
                        <div>
                            <span style="color:#8B949E;">Forecast Demand:</span> <strong>{fmt_number(mat_forecast)}</strong>
                        </div>
                        <div>
                            <span style="color:#8B949E;">Safety Stock:</span> <strong>{fmt_number(mat_ss)}</strong>
                        </div>
                        <div>
                            <span style="color:#8B949E;">Reorder Point:</span> <strong>{fmt_number(mat_rop)}</strong>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with d2:
                # Historical mini chart
                mat_hist = filtered_hist[filtered_hist["material_id"] == select_material].sort_values("Date")
                if len(mat_hist) > 0:
                    fig_mini = go.Figure()
                    fig_mini.add_trace(go.Scatter(
                        x=mat_hist["Date"], y=mat_hist["Demand"],
                        mode="lines+markers",
                        line=dict(color="#1F6FEB", width=2),
                        marker=dict(size=4),
                        name="Demand Pattern"
                    ))
                    fig_mini.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#C9D1D9", family="Inter, sans-serif", size=10),
                        margin=dict(l=10, r=10, t=30, b=10),
                        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                        height=250,
                        title=dict(text=f"Historical Demand Trend - Material #{select_material}", font=dict(size=11, color="#F0F6FC"))
                    )
                    st.plotly_chart(fig_mini, use_container_width=True)
                else:
                    st.info("No historical demand records match the current date filters.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4: BUSINESS SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### 💡 Strategic Inventory Summary")
        
        # ── 1. Highest Demand Materials ───────────────────────────────────────
        high_vol = filtered_hist.groupby("material_id")["Demand"].sum().reset_index().nlargest(3, "Demand")
        if len(high_vol) > 0:
            vol_list = ", ".join(high_vol["material_id"].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-info">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">📈 High Volume Fast-Movers</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Materials <strong>{vol_list}</strong> represent your largest historical consumption volumes. 
                    Monitor logistics pipelines for these items closely to prevent disruption.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 2. Slow-Moving Stock Risk (Overstock) ──────────────────────────────
        # Items with zero demand in date range but positive stock balance
        zero_demand_mats = set(filtered_pred[material_col]) - set(filtered_hist[filtered_hist["Demand"] > 0]["material_id"])
        slow_mats = filtered_pred[(filtered_pred[material_col].isin(zero_demand_mats)) & (filtered_pred[unrest_col] > 0)].head(3)
        if len(slow_mats) > 0:
            slow_list = ", ".join(slow_mats[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-warning">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">📦 Inactive Capital — Slow-Moving Materials</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Materials <strong>{slow_list}</strong> have positive warehouse balances but registered <strong>zero</strong> consumption demand. 
                    Recommend reviewing shelf lives and evaluating write-down potentials.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 3. High Value Assets ──────────────────────────────────────────────
        high_val_mats = filtered_pred.nlargest(3, "Inventory_Value")
        if len(high_val_mats) > 0:
            val_list = ", ".join(high_val_mats[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-info" style="border-color:#58A6FF;">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">💎 High Asset Capital Value Concentration</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Materials <strong>{val_list}</strong> represent the highest capital value in your active inventory. 
                    Ensure safety stocks are optimized to prevent cash-flow locking.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 4. Long Lead Time Risks ───────────────────────────────────────────
        long_lt = filtered_pred[filtered_pred[lt_col] >= 60].head(3)
        if len(long_lt) > 0:
            lt_list = ", ".join(long_lt[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-urgent" style="border-color:#E3B341;">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">⏱️ Supply Chain Latency Risks</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Materials <strong>{lt_list}</strong> have lead times exceeding 60 days. 
                    Delays in procurement could cause critical operations stoppages. Suggest maintaining dual-sourcing contracts.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 5. Stable Predictable Demand (Kanban Candidates) ─────────────────
        stable_mats = filtered_pred[(filtered_pred[abc_col] == "A") & (filtered_pred[xyz_col] == "X")].head(3)
        if len(stable_mats) > 0:
            st_list = ", ".join(stable_mats[material_col].astype(str).tolist())
            st.markdown(f"""
            <div class="insight-box insight-success">
                <div style="font-weight:700;color:#F0F6FC;font-size:14px;margin-bottom:4px;">⚙️ Kanban Replenishment Opportunities</div>
                <div style="color:#8B949E;font-size:12.5px;">
                    Materials <strong>{st_list}</strong> show high values (Class A) combined with predictable stable demand (Class X). 
                    Recommend shifting to automated blanket Kanban call-offs to minimize administrative work.
                </div>
            </div>
            """, unsafe_allow_html=True)
