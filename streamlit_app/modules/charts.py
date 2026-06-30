"""
modules/charts.py
-----------------
All Plotly chart functions used across the application.
Every function returns a plotly Figure with consistent dark styling.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# ── Shared dark theme layout ──────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(color="#C9D1D9", family="Inter, Segoe UI, sans-serif", size=11),
    margin        = dict(l=20, r=20, t=40, b=20),
    legend        = dict(bgcolor="rgba(22, 27, 34, 0.6)", bordercolor="rgba(255,255,255,0.08)"),
    xaxis         = dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.05)"),
    yaxis         = dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.05)"),
)

BLUE_PALETTE  = ["#1F6FEB", "#388BFD", "#58A6FF", "#79C0FF", "#A5D6FF"]
STATUS_COLORS = {"Sufficient": "#3FB950", "Low": "#E3B341", "Critical": "#F85149"}
PRIORITY_COLORS = {
    "Critical Priority" : "#F85149",
    "High Priority"     : "#E3B341",
    "Medium Priority"   : "#3FB950",
    "Low Priority"      : "#58A6FF",
    "Routine Purchase"  : "#BC8CFF",
    "Order On Demand"   : "#56D364",
}

def _apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(**_LAYOUT, title=dict(text=title, font=dict(size=13, color="#F0F6FC", weight="bold")))
    return fig

# ── Bar: Top N Forecast Demand ────────────────────────────────────────────────

def top_forecast_demand(df: pd.DataFrame, n: int = 15) -> go.Figure:
    top = df.nlargest(n, "forecast_demand")[["material_id", "forecast_demand"]].copy()
    top["material_id"] = top["material_id"].astype(str)
    top = top.sort_values("forecast_demand", ascending=False)
    height = max(600, len(top) * 35)
    fig = px.bar(
        top, x="forecast_demand", y="material_id",
        orientation="h",
        color="forecast_demand",
        color_continuous_scale=["#1F3A6E", "#1F6FEB", "#79C0FF"],
        labels={"forecast_demand": "Forecast Demand", "material_id": "Material ID"},
        height=height,
    )
    fig.update_traces(
        marker_line_width=0,
        texttemplate="%{x:,.0f}",
        textposition="outside",
        hovertemplate="<b>Material ID:</b> %{y}<br><b>Forecast Demand:</b> %{x:,.0f} Units<extra></extra>"
    )
    fig.update_layout(
        coloraxis_showscale=False, 
        yaxis=dict(type="category", autorange="reversed"),
        bargap=0.25
    )
    return _apply_theme(fig, f"Top {n} Materials by Forecast Demand")


# ── Bar: Top N Order Cost ─────────────────────────────────────────────────────

def top_order_cost(df: pd.DataFrame, n: int = 15) -> go.Figure:
    col = next((c for c in df.columns if "order_cost" in c.lower()), None)
    if col is None:
        return go.Figure()
    top = df.nlargest(n, col)[["material_id", col]].copy()
    top["material_id"] = top["material_id"].astype(str)
    top = top.sort_values(col, ascending=False)
    height = max(600, len(top) * 35)
    fig = px.bar(
        top, x=col, y="material_id",
        orientation="h",
        color=col,
        color_continuous_scale=["#3D1A1A", "#F85149", "#FFB3AE"],
        labels={col: "Order Cost (₹)", "material_id": "Material ID"},
        height=height,
    )
    fig.update_traces(
        marker_line_width=0,
        texttemplate="₹%{x:,.0f}",
        textposition="outside",
        hovertemplate="<b>Material ID:</b> %{y}<br><b>Estimated Order Cost:</b> ₹%{x:,.2f}<extra></extra>"
    )
    fig.update_layout(
        coloraxis_showscale=False, 
        yaxis=dict(type="category", autorange="reversed"),
        bargap=0.25
    )
    return _apply_theme(fig, f"Top {n} Materials by Estimated Order Cost")


# ── Donut: Inventory Status ───────────────────────────────────────────────────

def inventory_status_donut(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if "inventory_status" in c.lower()), None)
    if col is None:
        return go.Figure()
    counts = df[col].value_counts().reset_index()
    counts.columns = ["Status", "Count"]
    colors = [STATUS_COLORS.get(s, "#8B949E") for s in counts["Status"]]
    fig = go.Figure(go.Pie(
        labels=counts["Status"], values=counts["Count"],
        hole=0.6,
        marker=dict(colors=colors, line=dict(color="#161B22", width=2)),
        textinfo="label+percent",
        textfont=dict(size=12, color="#E6EDF3"),
    ))
    fig.update_layout(showlegend=False)
    return _apply_theme(fig, "Inventory Status Distribution")


# ── Donut: ABC Distribution ───────────────────────────────────────────────────

def abc_donut(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if c.lower() in ("abc_class", "abc")), None)
    if col is None:
        return go.Figure()
    counts = df[col].value_counts().reset_index()
    counts.columns = ["Class", "Count"]
    colors = {"A": "#F85149", "B": "#E3B341", "C": "#3FB950"}
    fig = go.Figure(go.Pie(
        labels=counts["Class"], values=counts["Count"],
        hole=0.6,
        marker=dict(
            colors=[colors.get(c, "#8B949E") for c in counts["Class"]],
            line=dict(color="#161B22", width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=13, color="#E6EDF3"),
    ))
    fig.update_layout(showlegend=False)
    return _apply_theme(fig, "ABC Classification")


# ── Donut: XYZ Distribution ───────────────────────────────────────────────────

def xyz_donut(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if c.lower() in ("xyz_class", "xyz")), None)
    if col is None:
        return go.Figure()
    counts = df[col].value_counts().reset_index()
    counts.columns = ["Class", "Count"]
    colors = {"X": "#58A6FF", "Y": "#BC8CFF", "Z": "#56D364"}
    fig = go.Figure(go.Pie(
        labels=counts["Class"], values=counts["Count"],
        hole=0.6,
        marker=dict(
            colors=[colors.get(c, "#8B949E") for c in counts["Class"]],
            line=dict(color="#161B22", width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=13, color="#E6EDF3"),
    ))
    fig.update_layout(showlegend=False)
    return _apply_theme(fig, "XYZ Demand Variability")


# ── Bar: Priority Distribution ────────────────────────────────────────────────

def priority_bar(df: pd.DataFrame) -> go.Figure:
    if "Business_Priority" not in df.columns:
        return go.Figure()
    from modules.utils import PRIORITY_ORDER
    counts = df["Business_Priority"].value_counts().reindex(PRIORITY_ORDER).dropna().reset_index()
    counts.columns = ["Priority", "Count"]
    colors = [PRIORITY_COLORS.get(p, "#8B949E") for p in counts["Priority"]]
    fig = go.Figure(go.Bar(
        x=counts["Priority"], y=counts["Count"],
        marker_color=colors,
        marker_line_width=0,
        text=counts["Count"],
        textposition="outside",
        textfont=dict(color="#E6EDF3"),
    ))
    fig.update_traces(
        texttemplate="%{y:,.0f}",
        hovertemplate="<b>Priority:</b> %{x}<br><b>Materials Count:</b> %{y:,.0f}<extra></extra>"
    )
    fig.update_layout(
        xaxis=dict(type="category", tickangle=-20),
        bargap=0.3
    )
    return _apply_theme(fig, "Materials by Business Priority")


# ── Histogram: Forecast Demand Distribution ───────────────────────────────────

def forecast_distribution(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df, x="forecast_demand", nbins=40,
        color_discrete_sequence=["#1F6FEB"],
        labels={"forecast_demand": "Forecast Demand", "count": "Number of Materials"},
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Forecast Demand Distribution")


# ── Histogram: Safety Stock Distribution ─────────────────────────────────────

def safety_stock_distribution(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if "safety_stock" in c.lower()), None)
    if col is None:
        return go.Figure()
    fig = px.histogram(
        df, x=col, nbins=40,
        color_discrete_sequence=["#E3B341"],
        labels={col: "Safety Stock", "count": "Number of Materials"},
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Safety Stock Distribution")


# ── Scatter: Reorder Point vs Unrestricted Stock ──────────────────────────────

def rop_vs_stock_scatter(df: pd.DataFrame) -> go.Figure:
    rop_col   = next((c for c in df.columns if "reorder_point" in c.lower()), None)
    stock_col = next((c for c in df.columns if c.lower() == "unrestricted"), None)
    status_col = next((c for c in df.columns if "inventory_status" in c.lower()), None)

    if not rop_col or not stock_col:
        return go.Figure()

    plot_df = df[[rop_col, stock_col]].copy()
    if status_col:
        plot_df["Status"] = df[status_col]
        color_map = STATUS_COLORS
        fig = px.scatter(
            plot_df, x=stock_col, y=rop_col,
            color="Status", color_discrete_map=color_map,
            labels={rop_col: "Reorder Point", stock_col: "Unrestricted Stock"},
            opacity=0.7,
        )
    else:
        fig = px.scatter(
            plot_df, x=stock_col, y=rop_col,
            color_discrete_sequence=["#1F6FEB"], opacity=0.7,
        )

    # Diagonal reference line (perfect balance)
    max_val = max(plot_df[rop_col].max(), plot_df[stock_col].max())
    fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                  line=dict(color="#8B949E", width=1, dash="dot"))
    return _apply_theme(fig, "Reorder Point vs Current Stock")


# ── Line: Demand Trend (historical) ──────────────────────────────────────────

def demand_trend(df: pd.DataFrame) -> go.Figure:
    date_col   = next((c for c in df.columns if c.lower() in ("date", "Date")), None)
    demand_col = next((c for c in df.columns if c.lower() == "demand"), None)
    if not date_col or not demand_col:
        return go.Figure()

    monthly = (
        df.groupby(date_col)[demand_col]
          .sum()
          .reset_index()
          .sort_values(date_col)
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly[date_col], y=monthly[demand_col],
        mode="lines+markers",
        line=dict(color="#1F6FEB", width=2),
        marker=dict(size=5, color="#58A6FF"),
        fill="tozeroy",
        fillcolor="rgba(31,111,235,0.08)",
        name="Total Demand",
    ))
    return _apply_theme(fig, "Historical Demand Trend")


# ── Bar: Lead Time Distribution ───────────────────────────────────────────────

def lead_time_distribution(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if "lead_time_category" in c.lower()), None)
    if col is None:
        return go.Figure()
    counts = df[col].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    cat_colors = {
        "Short": "#3FB950", "Medium": "#E3B341",
        "Long": "#F85149",  "Very Long": "#BC8CFF",
    }
    colors = [cat_colors.get(c, "#8B949E") for c in counts["Category"]]
    fig = go.Figure(go.Bar(
        x=counts["Category"], y=counts["Count"],
        marker_color=colors, marker_line_width=0,
        text=counts["Count"], textposition="outside",
        textfont=dict(color="#E6EDF3"),
    ))
    fig.update_traces(
        texttemplate="%{y:,.0f}",
        hovertemplate="<b>Category:</b> %{x}<br><b>Count:</b> %{y:,.0f}<extra></extra>"
    )
    fig.update_layout(
        xaxis=dict(type="category"),
        bargap=0.3
    )
    return _apply_theme(fig, "Lead Time Category Distribution")


# ── Histogram: Purchase Cost Distribution ─────────────────────────────────────

def purchase_cost_distribution(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if "order_cost" in c.lower()), None)
    if col is None:
        return go.Figure()
    # Filter out items with 0 purchase cost to make the distribution meaningful
    filtered = df[df[col] > 0]
    if len(filtered) == 0:
        return go.Figure()
    fig = px.histogram(
        filtered, x=col, nbins=30,
        color_discrete_sequence=["#FF7B72"],
        labels={col: "Estimated Order Cost (₹)", "count": "Number of Materials"},
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Estimated Purchase Cost Distribution (Orders > ₹0)")


# ── Line: Demand Forecast Projection Trend ────────────────────────────────────

def forecast_trend(hist_df: pd.DataFrame, pred_df: pd.DataFrame) -> go.Figure:
    hist_date_col = next((c for c in hist_df.columns if c.lower() in ("date", "Date")), None)
    hist_demand_col = next((c for c in hist_df.columns if c.lower() == "demand"), None)
    pred_date_col = next((c for c in pred_df.columns if "forecast_date" in c.lower()), None)
    pred_demand_col = next((c for c in pred_df.columns if "forecast_demand" in c.lower()), None)
    
    if not hist_date_col or not hist_demand_col or not pred_date_col or not pred_demand_col:
        return go.Figure()
        
    # Group historical by Date
    hist_monthly = (
        hist_df.groupby(hist_date_col)[hist_demand_col]
        .sum()
        .reset_index()
        .sort_values(hist_date_col)
    )
    hist_monthly.columns = ["Date", "Demand"]
    hist_monthly["Type"] = "Actual Demand"
    
    # Next month forecast demand
    pred_total = pred_df[pred_demand_col].sum()
    pred_date = str(pred_df[pred_date_col].iloc[0])
    pred_row = pd.DataFrame([{"Date": pred_date, "Demand": pred_total, "Type": "Forecast"}])
    
    # Combine them
    combined = pd.concat([hist_monthly, pred_row], ignore_index=True)
    combined["Date"] = pd.to_datetime(combined["Date"])
    combined = combined.sort_values("Date")
    
    fig = go.Figure()
    
    # Plot actual demand line
    actual_df = combined[combined["Type"] == "Actual Demand"]
    fig.add_trace(go.Scatter(
        x=actual_df["Date"], y=actual_df["Demand"],
        mode="lines+markers",
        line=dict(color="#1F6FEB", width=3),
        marker=dict(size=6, color="#58A6FF"),
        name="Actual Demand",
    ))
    
    # Connect the last actual demand point to the forecast demand point with a dotted line
    last_actual = actual_df.iloc[-1] if len(actual_df) > 0 else None
    forecast_item = combined[combined["Type"] == "Forecast"]
    if last_actual is not None and len(forecast_item) > 0:
        forecast_pt = forecast_item.iloc[0]
        fig.add_trace(go.Scatter(
            x=[last_actual["Date"], forecast_pt["Date"]],
            y=[last_actual["Demand"], forecast_pt["Demand"]],
            mode="lines",
            line=dict(color="#BC8CFF", width=3, dash="dash"),
            name="Forecast Transition",
            showlegend=False
          ))
          
    # Plot forecast point
    if len(forecast_item) > 0:
        fig.add_trace(go.Scatter(
            x=forecast_item["Date"], y=forecast_item["Demand"],
            mode="markers",
            marker=dict(size=10, color="#BC8CFF", symbol="star"),
            name="Forecast Month",
        ))
        
    fig.update_layout(xaxis=dict(type="date"))
    return _apply_theme(fig, "Demand Forecast Projection Trend")


# ── Bar: Yearly Demand Trend ──────────────────────────────────────────────────

def yearly_demand_trend(df: pd.DataFrame) -> go.Figure:
    date_col = next((c for c in df.columns if c.lower() in ("date", "Date")), None)
    demand_col = next((c for c in df.columns if c.lower() == "demand"), None)
    if not date_col or not demand_col or len(df) == 0:
        return go.Figure()
        
    df_copy = df.copy()
    df_copy["Date"] = pd.to_datetime(df_copy[date_col])
    df_copy["Year"] = df_copy["Date"].dt.year
    yearly = df_copy.groupby("Year")[demand_col].sum().reset_index()
    fig = px.bar(
        yearly, x="Year", y=demand_col,
        color_discrete_sequence=["#58A6FF"],
    )
    fig.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="outside",
        hovertemplate="<b>Year:</b> %{x}<br><b>Total Demand:</b> %{y:,.0f} Units<extra></extra>"
    )
    fig.update_layout(
        xaxis=dict(type="category"),
        bargap=0.3
    )
    return _apply_theme(fig, "Yearly Demand Trend")


# ── Line: Demand Seasonality ──────────────────────────────────────────────────

def demand_seasonality(df: pd.DataFrame) -> go.Figure:
    date_col = next((c for c in df.columns if c.lower() in ("date", "Date")), None)
    demand_col = next((c for c in df.columns if c.lower() == "demand"), None)
    if not date_col or not demand_col or len(df) == 0:
        return go.Figure()
        
    df_copy = df.copy()
    df_copy["Date"] = pd.to_datetime(df_copy[date_col])
    df_copy["Year"] = df_copy["Date"].dt.year
    df_copy["Month"] = df_copy["Date"].dt.month
    df_copy["Month_Name"] = df_copy["Date"].dt.strftime("%b")
    
    monthly_season = df_copy.groupby(["Year", "Month", "Month_Name"])[demand_col].sum().reset_index()
    monthly_season = monthly_season.sort_values(["Year", "Month"])
    
    fig = go.Figure()
    years = sorted(monthly_season["Year"].unique())
    colors = ["#1F6FEB", "#BC8CFF", "#FF7B72", "#3FB950", "#58A6FF", "#E3B341"]
    
    for i, year in enumerate(years):
        year_df = monthly_season[monthly_season["Year"] == year]
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=year_df["Month_Name"], y=year_df[demand_col],
            mode="lines+markers",
            name=str(year),
            line=dict(width=2, color=color),
            marker=dict(size=4)
        ))
        
    return _apply_theme(fig, "Demand Seasonality Overlay (Year-over-Year)")


# ── Line: Rolling Average Trend ───────────────────────────────────────────────

def rolling_average_trend(df: pd.DataFrame) -> go.Figure:
    date_col = next((c for c in df.columns if c.lower() in ("date", "Date")), None)
    demand_col = next((c for c in df.columns if c.lower() == "demand"), None)
    if not date_col or not demand_col or len(df) == 0:
        return go.Figure()
        
    df_copy = df.copy()
    df_copy["Date"] = pd.to_datetime(df_copy[date_col])
    monthly = df_copy.groupby("Date")[demand_col].sum().reset_index().sort_values("Date")
    
    # Calculate rolling averages
    monthly["3-Month Rolling"] = monthly[demand_col].rolling(window=3, min_periods=1).mean()
    monthly["6-Month Rolling"] = monthly[demand_col].rolling(window=6, min_periods=1).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["Date"], y=monthly[demand_col],
        mode="lines", name="Actual Demand",
        line=dict(color="#1F6FEB", width=1.5, dash="solid")
    ))
    fig.add_trace(go.Scatter(
        x=monthly["Date"], y=monthly["3-Month Rolling"],
        mode="lines", name="3-Month SMA",
        line=dict(color="#BC8CFF", width=2, dash="dash")
    ))
    fig.add_trace(go.Scatter(
        x=monthly["Date"], y=monthly["6-Month Rolling"],
        mode="lines", name="6-Month SMA",
        line=dict(color="#3FB950", width=2.5, dash="dot")
    ))
    return _apply_theme(fig, "Monthly Demand with Simple Moving Average (SMA)")


# ── Matrix: Consumption Heatmap ───────────────────────────────────────────────

def consumption_heatmap(df: pd.DataFrame) -> go.Figure:
    date_col = next((c for c in df.columns if c.lower() in ("date", "Date")), None)
    demand_col = next((c for c in df.columns if c.lower() == "demand"), None)
    if not date_col or not demand_col or len(df) == 0:
        return go.Figure()
        
    df_copy = df.copy()
    df_copy["Date"] = pd.to_datetime(df_copy[date_col])
    df_copy["Year"] = df_copy["Date"].dt.year
    df_copy["Month"] = df_copy["Date"].dt.month
    df_copy["Month_Name"] = df_copy["Date"].dt.strftime("%b")
    
    heatmap_data = df_copy.groupby(["Year", "Month", "Month_Name"])[demand_col].sum().reset_index()
    heatmap_data = heatmap_data.sort_values(["Year", "Month"])
    
    # Pivot
    heatmap_pivot = heatmap_data.pivot(index="Year", columns="Month_Name", values=demand_col)
    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    heatmap_pivot = heatmap_pivot.reindex(columns=[m for m in months_order if m in heatmap_pivot.columns])
    
    fig = px.imshow(
        heatmap_pivot,
        color_continuous_scale="Blues",
        text_auto=True,
        labels=dict(x="Month", y="Year", color="Total Demand")
    )
    return _apply_theme(fig, "Monthly Consumption Heatmap Matrix")


# ── Matrix: ABC-XYZ crosstab ──────────────────────────────────────────────────

def abc_xyz_matrix(df: pd.DataFrame) -> go.Figure:
    abc_col = next((c for c in df.columns if "abc_class" in c.lower()), None)
    xyz_col = next((c for c in df.columns if "xyz_class" in c.lower()), None)
    if not abc_col or not xyz_col or len(df) == 0:
        return go.Figure()
        
    matrix = pd.crosstab(df[abc_col], df[xyz_col])
    matrix = matrix.reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"], fill_value=0)
    
    fig = px.imshow(
        matrix,
        color_continuous_scale="Blues",
        text_auto=True,
        labels=dict(x="XYZ Predictability Class", y="ABC Capital Value Class", color="Materials Count")
    )
    return _apply_theme(fig, "ABC-XYZ Classification Matrix")


# ── Histogram: Inventory Value Distribution ───────────────────────────────────

def inventory_value_distribution(df: pd.DataFrame) -> go.Figure:
    val_col = next((c for c in df.columns if "inventory_value" in c.lower()), None)
    if val_col is None:
        unrest = next((c for c in df.columns if "unrestricted" in c.lower()), None)
        price = next((c for c in df.columns if "moving_price" in c.lower()), None)
        if unrest and price:
            df_val = df[unrest] * df[price]
            # Assign value inside local scope to avoid pandas copy warnings
            filtered = df[df_val > 0].copy()
            filtered["Inventory_Value"] = filtered[unrest] * filtered[price]
            val_col = "Inventory_Value"
        else:
            return go.Figure()
    else:
        filtered = df[df[val_col] > 0]
        
    if len(filtered) == 0:
        return go.Figure()
        
    fig = px.histogram(
        filtered, x=val_col, nbins=30,
        color_discrete_sequence=["#3FB950"],
        labels={val_col: "Inventory Asset Value (₹)", "count": "Count"}
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Inventory Value Spread (Active Assets)")


# ── Histogram: Stock Volume Distribution ──────────────────────────────────────

def stock_distribution(df: pd.DataFrame) -> go.Figure:
    unrest = next((c for c in df.columns if "unrestricted" in c.lower()), None)
    if unrest is None or len(df) == 0:
        return go.Figure()
        
    filtered = df[df[unrest] > 0]
    if len(filtered) == 0:
        return go.Figure()
        
    fig = px.histogram(
        filtered, x=unrest, nbins=30,
        color_discrete_sequence=["#58A6FF"],
        labels={unrest: "Unrestricted Stock Balance (Units)", "count": "Count"}
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Current Stock Volume Distribution")


# ── Histogram: Material Coverage Distribution ─────────────────────────────────

def material_coverage_distribution(df: pd.DataFrame) -> go.Figure:
    unrest = next((c for c in df.columns if "unrestricted" in c.lower()), None)
    demand = next((c for c in df.columns if "forecast_demand" in c.lower()), None)
    if not unrest or not demand or len(df) == 0:
        return go.Figure()
        
    df_copy = df.copy()
    # Calculate coverage in months (stock / monthly demand)
    df_copy["Coverage_Months"] = df_copy[unrest] / df_copy[demand].replace(0, 0.001)
    
    # Filter out extreme outliers for nice charting
    filtered = df_copy[(df_copy["Coverage_Months"] > 0) & (df_copy["Coverage_Months"] <= 24)]
    if len(filtered) == 0:
        return go.Figure()
        
    fig = px.histogram(
        filtered, x="Coverage_Months", nbins=24,
        color_discrete_sequence=["#E3B341"],
        labels={"Coverage_Months": "Inventory Coverage (Months)", "count": "Count"}
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Material Inventory Coverage Spread")


# ── Histogram: Price Distribution ─────────────────────────────────────────────

def moving_price_distribution(df: pd.DataFrame) -> go.Figure:
    price = next((c for c in df.columns if "moving_price" in c.lower()), None)
    if price is None or len(df) == 0:
        return go.Figure()
        
    filtered = df[df[price] > 0]
    if len(filtered) == 0:
        return go.Figure()
        
    fig = px.histogram(
        filtered, x=price, nbins=30,
        color_discrete_sequence=["#BC8CFF"],
        labels={price: "Moving Average Price (₹)", "count": "Count"}
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Material Moving Unit Price Distribution")


# ── Histogram: ROP Distribution ───────────────────────────────────────────────

def rop_distribution(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if "reorder_point" in c.lower()), None)
    if col is None or len(df) == 0:
        return go.Figure()
    filtered = df[df[col] > 0]
    if len(filtered) == 0:
        return go.Figure()
    fig = px.histogram(
        filtered, x=col, nbins=30,
        color_discrete_sequence=["#FF7B72"],
        labels={col: "Reorder Point (ROP)", "count": "Count"}
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Reorder Point (ROP) Distribution")


# ── Histogram: Inventory Gap Distribution ─────────────────────────────────────

def inventory_gap_distribution(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if "inventory_gap" in c.lower()), None)
    if col is None or len(df) == 0:
        return go.Figure()
    filtered = df[df[col] > 0]
    if len(filtered) == 0:
        return go.Figure()
    fig = px.histogram(
        filtered, x=col, nbins=30,
        color_discrete_sequence=["#FF7B72"],
        labels={col: "Inventory Deficit Gap (Units)", "count": "Count"}
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Inventory Gap (Deficit) Distribution")


# ── Histogram: Purchase Quantity Distribution ─────────────────────────────────

def purchase_qty_distribution(df: pd.DataFrame) -> go.Figure:
    col = next((c for c in df.columns if "order_quantity" in c.lower()), None)
    if col is None or len(df) == 0:
        return go.Figure()
    filtered = df[df[col] > 0]
    if len(filtered) == 0:
        return go.Figure()
    fig = px.histogram(
        filtered, x=col, nbins=30,
        color_discrete_sequence=["#58A6FF"],
        labels={col: "Recommended Order Quantity (Units)", "count": "Count"}
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return _apply_theme(fig, "Purchase Quantity Distribution (Orders > 0)")


# ── Bar: Recommended Cost by Priority Tier ────────────────────────────────────

def cost_by_priority(df: pd.DataFrame) -> go.Figure:
    cost_col = next((c for c in df.columns if "order_cost" in c.lower()), None)
    priority_col = "Business_Priority"
    if cost_col is None or priority_col not in df.columns or len(df) == 0:
        return go.Figure()
        
    grouped = df.groupby(priority_col)[cost_col].sum().reset_index()
    priority_order = ["Critical Priority", "High Priority", "Planned Purchase", "Routine Stock", "Order On Demand"]
    grouped[priority_col] = pd.Categorical(grouped[priority_col], categories=priority_order, ordered=True)
    grouped = grouped.sort_values(priority_col)
    
    fig = px.bar(
        grouped, x=priority_col, y=cost_col,
        color=priority_col,
        color_discrete_map={
            "Critical Priority": "#F85149",
            "High Priority": "#E3B341",
            "Planned Purchase": "#58A6FF",
            "Routine Stock": "#3FB950",
            "Order On Demand": "#8B949E"
        },
        labels={cost_col: "Total Cost (₹)", priority_col: "Priority Tier"}
    )
    fig.update_traces(
        texttemplate="₹%{y:,.0f}",
        textposition="outside",
        hovertemplate="<b>Priority Tier:</b> %{x}<br><b>Total Cost:</b> ₹%{y:,.2f}<extra></extra>"
    )
    fig.update_layout(
        xaxis=dict(type="category"),
        bargap=0.3
    )
    return _apply_theme(fig, "Recommended Purchase Capital by Priority Tier")


# ── Pie: Recommended Cost by Inventory Status ─────────────────────────────────

def cost_by_status(df: pd.DataFrame) -> go.Figure:
    cost_col = next((c for c in df.columns if "order_cost" in c.lower()), None)
    status_col = next((c for c in df.columns if "inventory_status" in c.lower()), None)
    if cost_col is None or status_col is None or len(df) == 0:
        return go.Figure()
        
    grouped = df.groupby(status_col)[cost_col].sum().reset_index()
    fig = px.pie(
        grouped, values=cost_col, names=status_col,
        color=status_col,
        color_discrete_map={
            "Critical": "#F85149",
            "Understock": "#E3B341",
            "Sufficient": "#3FB950",
            "Overstock": "#BC8CFF"
        },
        hole=0.4
    )
    return _apply_theme(fig, "Capital Allocation by Stock Health Status")


# ── Scatter: Demand vs Recommended Cost ───────────────────────────────────────

def forecast_vs_cost(df: pd.DataFrame) -> go.Figure:
    demand_col = next((c for c in df.columns if "forecast_demand" in c.lower()), None)
    cost_col = next((c for c in df.columns if "order_cost" in c.lower()), None)
    priority_col = "Business_Priority"
    if not demand_col or not cost_col or len(df) == 0:
        return go.Figure()
        
    fig = px.scatter(
        df, x=demand_col, y=cost_col,
        color=priority_col if priority_col in df.columns else None,
        color_discrete_map={
            "Critical Priority": "#F85149",
            "High Priority": "#E3B341",
            "Planned Purchase": "#58A6FF",
            "Routine Stock": "#3FB950",
            "Order On Demand": "#8B949E"
        },
        opacity=0.7,
        labels={demand_col: "Forecast Monthly Demand (Units)", cost_col: "Estimated Order Cost (₹)"}
    )
    return _apply_theme(fig, "Forecast Demand vs Recommended Order Cost Correlation")
