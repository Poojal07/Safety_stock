"""
modules/utils.py
----------------
Shared utilities: CSS injection, KPI cards, business priority mapping,
colour palettes, and common data helpers.
"""

import streamlit as st
import pandas as pd
import numpy as np


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════

def inject_global_css() -> None:
    """Inject global CSS styles into the Streamlit app."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* ── Base ── */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 10% 20%, rgba(13, 20, 35, 1) 0%, rgba(9, 13, 22, 1) 90.1%);
    }
    
    [data-testid="stSidebar"] {
        background: rgba(13, 17, 23, 0.85) !important;
        backdrop-filter: blur(20px) saturate(180%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .main .block-container {
        padding: 2rem 2.5rem 3rem 2.5rem;
        max-width: 1440px;
    }
    
    /* ── Animations ── */
    @keyframes slideUp {
        from { transform: translateY(24px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulseRed {
        0%, 100% { box-shadow: 0 0 15px rgba(248, 81, 73, 0.2); border-color: rgba(248, 81, 73, 0.4); }
        50% { box-shadow: 0 0 30px rgba(248, 81, 73, 0.6); border-color: rgba(248, 81, 73, 0.9); }
    }
    
    @keyframes pulseBlue {
        0%, 100% { border-color: rgba(31, 111, 235, 0.3); }
        50% { border-color: rgba(31, 111, 235, 0.8); }
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.25; }
    }
    
    /* ── Animation Classes ── */
    .animate-slideup {
        animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    .animate-fadein {
        animation: fadeIn 0.8s ease-out both;
    }
    .blink-warning {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #F85149;
        border-radius: 50%;
        animation: blink 1.2s infinite ease-in-out;
        margin-right: 6px;
    }
    
    /* ── KPI Cards (Glassmorphism) ── */
    .kpi-card {
        background: rgba(22, 27, 34, 0.45);
        backdrop-filter: blur(12px) saturate(180%);
        -webkit-backdrop-filter: blur(12px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 0px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: rgba(31, 111, 235, 0.4);
        background: rgba(22, 27, 34, 0.6);
        box-shadow: 0 12px 30px rgba(31, 111, 235, 0.12), 0 0 15px rgba(31, 111, 235, 0.08);
    }
    .kpi-label {
        font-size: 11px;
        color: #8B949E;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 800;
        color: #F0F6FC;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    .kpi-delta {
        font-size: 12px;
        margin-top: 8px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .kpi-icon {
        font-size: 20px;
        opacity: 0.8;
    }
    
    /* ── Section headers ── */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #F0F6FC;
        border-left: 4px solid #1F6FEB;
        padding-left: 14px;
        margin: 32px 0 18px 0;
        letter-spacing: -0.3px;
    }
    
    /* ── Priority badges ── */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-critical { background: rgba(248, 81, 73, 0.15); color: #FF7B72; border: 1px solid rgba(248, 81, 73, 0.4); }
    .badge-high     { background: rgba(227, 179, 65, 0.15); color: #F2CC60; border: 1px solid rgba(227, 179, 65, 0.4); }
    .badge-medium   { background: rgba(56, 139, 253, 0.15); color: #58A6FF; border: 1px solid rgba(56, 139, 253, 0.4); }
    .badge-low      { background: rgba(63, 185, 80, 0.15); color: #56D364; border: 1px solid rgba(63, 185, 80, 0.4); }
    .badge-routine  { background: rgba(188, 140, 255, 0.15); color: #D2A8FF; border: 1px solid rgba(188, 140, 255, 0.4); }
    .badge-demand   { background: rgba(139, 148, 158, 0.15); color: #C9D1D9; border: 1px solid rgba(139, 148, 158, 0.4); }
    
    /* ── Recommendation cards ── */
    .rec-card {
        background: rgba(22, 27, 34, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 14px;
        transition: all 0.25s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .rec-card:hover {
        transform: translateX(4px);
        background: rgba(22, 27, 34, 0.55);
        border-color: rgba(255,255,255,0.12);
    }
    .rec-card-critical {
        border-left: 5px solid #F85149;
        animation: pulseRed 2.5s infinite ease-in-out;
    }
    .rec-card-high     { border-left: 5px solid #E3B341; }
    .rec-card-medium   { border-left: 5px solid #58A6FF; }
    .rec-card-low      { border-left: 5px solid #3FB950; }
    .rec-card-routine  {{ border-left: 5px solid #BC8CFF; }}
    .rec-card-demand   { border-left: 5px solid #8B949E; }
    
    /* ── Glowing Critical Card ── */
    .glowing-critical-card {
        background: linear-gradient(135deg, rgba(61, 26, 26, 0.45) 0%, rgba(22, 27, 34, 0.6) 100%);
        backdrop-filter: blur(12px) saturate(180%);
        border: 1px solid #F85149;
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 14px;
        animation: pulseRed 2s infinite ease-in-out, slideUp 0.6s ease-out;
        box-shadow: 0 0 20px rgba(248, 81, 73, 0.15);
    }
    
    /* ── Insight alert boxes ── */
    .insight-box {
        background: rgba(22, 27, 34, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .insight-box:hover {
        background: rgba(22, 27, 34, 0.5);
        border-color: rgba(255,255,255,0.1);
    }
    .insight-urgent  { border-left: 4px solid #F85149; }
    .insight-warning { border-left: 4px solid #E3B341; }
    .insight-info    { border-left: 4px solid #58A6FF; }
    .insight-success { border-left: 4px solid #3FB950; }
    
    /* ── Sidebar nav overrides ── */
    [data-testid="stSidebar"] div[data-testid="stButton"] > button {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        color: #8B949E !important;
        text-align: left !important;
        padding: 10px 14px !important;
        border-radius: 8px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        justify-content: flex-start !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #F0F6FC !important;
        transform: translateX(3px) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
        background-color: rgba(31, 111, 235, 0.15) !important;
        color: #58A6FF !important;
        border: 1px solid rgba(31, 111, 235, 0.3) !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }
    
    /* ── Dividers ── */
    .divider {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        margin: 20px 0;
    }
    
    /* ── Streamlit overrides ── */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        background: rgba(22, 27, 34, 0.4) !important;
        backdrop-filter: blur(10px);
    }
    .stSelectbox > label, .stMultiSelect > label, .stTextInput > label {
        color: #8B949E !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #F0F6FC !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }
    .stMetric label {
        color: #8B949E !important;
    }
    div[data-testid="metric-container"] {
        background: rgba(22, 27, 34, 0.45);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
    }
    
    /* Elegant tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(22, 27, 34, 0.3);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 6px;
        color: #8B949E;
        font-size: 13px;
        font-weight: 600;
        border: none;
        padding: 0 16px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #F0F6FC;
        background-color: rgba(255, 255, 255, 0.03);
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(31, 111, 235, 0.15) !important;
        color: #58A6FF !important;
        border: 1px solid rgba(31, 111, 235, 0.25) !important;
    }
    
    /* Smooth button styling */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1F6FEB 0%, #388BFD 100%) !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.25) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(31, 111, 235, 0.4) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: rgba(33, 38, 45, 0.5) !important;
        border: 1px solid rgba(240, 246, 252, 0.1) !important;
        color: #C9D1D9 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #F0F6FC !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# KPI CARD COMPONENT
# ══════════════════════════════════════════════════════════════════════════════

def kpi_card(label: str, value: str, icon: str = "",
             delta: str = "", delta_color: str = "#3FB950") -> None:
    """Render a styled KPI card."""
    delta_html = (
        f'<div class="kpi-delta" style="color:{delta_color};">{delta}</div>'
        if delta else ""
    )
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label} <span class="kpi-icon">{icon}</span></div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str) -> None:
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BUSINESS PRIORITY MAPPING  (ABC × XYZ → human label)
# ══════════════════════════════════════════════════════════════════════════════

# Mapping: (ABC, XYZ) → priority label
PRIORITY_MAP = {
    ("A", "X"): "Critical Priority",
    ("A", "Y"): "Critical Priority",
    ("A", "Z"): "High Priority",
    ("B", "X"): "High Priority",
    ("B", "Y"): "Planned Purchase",
    ("B", "Z"): "Planned Purchase",
    ("C", "X"): "Routine Stock",
    ("C", "Y"): "Routine Stock",
    ("C", "Z"): "Order On Demand",
}

PRIORITY_ORDER = [
    "Critical Priority",
    "High Priority",
    "Planned Purchase",
    "Routine Stock",
    "Order On Demand",
]

PRIORITY_CONFIG = {
    "Critical Priority": {
        "icon"      : "🔴",
        "color"     : "#F85149",
        "badge"     : "badge-critical",
        "card"      : "rec-card-critical",
        "reason"    : "High-value material with stable or variable demand — any stockout has immediate operational impact.",
        "action"    : "Maintain 2–3 months of safety stock. Review inventory weekly. Place orders immediately if below reorder point.",
        "impact"    : "Production stoppages or delivery failures if stock runs out.",
        "strategy"  : "Vendor-managed inventory or long-term blanket orders with weekly release.",
    },
    "High Priority": {
        "icon"      : "🟠",
        "color"     : "#E3B341",
        "badge"     : "badge-high",
        "card"      : "rec-card-high",
        "reason"    : "High-value erratic demand OR medium-value stable demand — requires close monitoring.",
        "action"    : "Review inventory every two weeks. Keep safety buffer. Dual-source if possible.",
        "impact"    : "Significant cost exposure or service disruption if mismanaged.",
        "strategy"  : "Monthly procurement with mid-month review. Safety stock at 1.5× lead time demand.",
    },
    "Planned Purchase": {
        "icon"      : "🟡",
        "color"     : "#58A6FF",
        "badge"     : "badge-medium",
        "card"      : "rec-card-medium",
        "reason"    : "Medium-value material with moderate demand predictability — manageable purchasing planning.",
        "action"    : "Standard monthly replenishment. Monitor reorder point closely.",
        "impact"    : "Moderate business impact if out of stock.",
        "strategy"  : "Periodic review system with monthly purchase cycle.",
    },
    "Routine Stock": {
        "icon"      : "🟢",
        "color"     : "#3FB950",
        "badge"     : "badge-low",
        "card"      : "rec-card-low",
        "reason"    : "Low-value stable demand — low financial risk, highly predictable consumption.",
        "action"    : "Order in bulk to reduce ordering cost. Quarterly review is sufficient.",
        "impact"    : "Minimal business disruption if out of stock briefly.",
        "strategy"  : "Economic order quantity (EOQ) model with quarterly replenishment.",
    },
    "Order On Demand": {
        "icon"      : "⚪",
        "color"     : "#8B949E",
        "badge"     : "badge-demand",
        "card"      : "rec-card-demand",
        "reason"    : "Low-value highly erratic demand — stocking this is not cost-effective.",
        "action"    : "Do NOT maintain standing inventory. Purchase only when specific demand exists.",
        "impact"    : "Minimal — these items are low-cost and sporadically needed.",
        "strategy"  : "Just-in-time purchasing. Source from spot market or local vendors.",
    },
}


def get_priority(abc: str, xyz: str) -> str:
    """Map ABC + XYZ class to a business-friendly priority label."""
    abc = str(abc).strip().upper() if pd.notna(abc) else "C"
    xyz = str(xyz).strip().upper() if pd.notna(xyz) else "Z"
    return PRIORITY_MAP.get((abc, xyz), "Routine Purchase")


def add_priority_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add Business_Priority column to a DataFrame containing abc_class and xyz_class."""
    abc_col = next((c for c in df.columns if c.lower() in ("abc_class", "abc")), None)
    xyz_col = next((c for c in df.columns if c.lower() in ("xyz_class", "xyz")), None)

    if abc_col and xyz_col:
        df["Business_Priority"] = df.apply(
            lambda r: get_priority(r[abc_col], r[xyz_col]), axis=1
        )
    else:
        df["Business_Priority"] = "Routine Purchase"
    return df


# ══════════════════════════════════════════════════════════════════════════════
# NUMBER FORMATTING
# ══════════════════════════════════════════════════════════════════════════════

def fmt_number(n: float, decimals: int = 0) -> str:
    """Format a number with comma separators."""
    if pd.isna(n):
        return "—"
    return f"{n:,.{decimals}f}"


def fmt_currency(n: float) -> str:
    """Format as Indian-style currency string."""
    if pd.isna(n):
        return "—"
    if n >= 1_00_00_000:
        return f"₹{n/1_00_00_000:.2f} Cr"
    if n >= 1_00_000:
        return f"₹{n/1_00_000:.2f} L"
    return f"₹{n:,.0f}"


def fmt_compact(n: float) -> str:
    """Compact number format for KPI cards."""
    if pd.isna(n):
        return "—"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:.0f}"
