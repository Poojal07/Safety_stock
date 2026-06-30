# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# =============================================================================
# 05 — Inventory Planning
# Safety Stock Automation Pipeline | Script 5 of 5
#
# Purpose : Calculate inventory planning metrics using company-defined formulas
#           and produce the final Prediction.csv delivered to the client.
#
# Input   : forecast_results.csv  (output of Script 04)
# Output  : Prediction.csv        (final client deliverable)
#
# Company Business Formulas:
#   Safety Stock  = forecast_demand                          (if lead_time <= 30)
#                   forecast_demand × (lead_time / 30)       (if lead_time > 30)
#   Reorder Point = Forecast_Demand + Safety_Stock
#   Inventory Gap = Reorder_Point - Unrestricted
#   Order Qty     = max(0, Inventory Gap)
#   Order Cost    = Order_Qty × Moving_Price
#   Action        = "Order Material" if Unrestricted < Reorder_Point
#                   "No Action Required" otherwise
# =============================================================================

import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── Setup path resolution for subprocess execution ────────────────────
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Input / Output paths ──────────────────────────────────────────────────────
from config.paths import FORECAST_RESULTS as FORECAST_FILE, UPDATED_HISTORICAL_DATA as HISTORICAL_FILE, FINAL_PREDICTION_FILE as OUTPUT_FILE

WORKING_DAYS = 30

print('Configuration loaded successfully.')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_step(msg: str) -> None:
    print(f'\n[PIPELINE] {msg}')
    print('-' * 60)


def calc_safety_stock(forecast_demand: pd.Series,
                       lead_time_days: pd.Series) -> pd.Series:
    """Company-defined Safety Stock formula:
        If lead_time <= 30 : Safety_Stock = forecast_demand
        If lead_time >  30 : Safety_Stock = forecast_demand × (lead_time / 30)
    """
    return np.where(
        lead_time_days <= 30,
        forecast_demand,
        forecast_demand * (lead_time_days / 30)
    ).round(2)


def calc_reorder_point(forecast_demand: pd.Series,
                        safety_stock: pd.Series) -> pd.Series:
    """Company-defined Reorder Point:
        Reorder_Point = Forecast_Demand + Safety_Stock
    """
    return (forecast_demand + safety_stock).round(2)


def calc_inventory_gap(reorder_point: pd.Series,
                        unrestricted: pd.Series) -> pd.Series:
    """Inventory Gap = Reorder_Point - Unrestricted Stock"""
    return (reorder_point - unrestricted).round(2)


def calc_order_quantity(inventory_gap: pd.Series) -> pd.Series:
    """Order Quantity = max(0, Inventory Gap)"""
    return inventory_gap.clip(lower=0).round(2)


def calc_order_cost(order_quantity: pd.Series,
                     moving_price: pd.Series) -> pd.Series:
    """Order Cost = Order Quantity × Moving Price"""
    return (order_quantity * moving_price).round(2)


def assign_suggested_action(unrestricted: pd.Series,
                              reorder_point: pd.Series) -> pd.Series:
    """Company-defined action logic:
        'Order Material'       if Unrestricted < Reorder_Point
        'No Action Required'   otherwise
    """
    return np.where(
        unrestricted < reorder_point,
        'Order Material',
        'No Action Required'
    )


def assign_inventory_status(inventory_gap: pd.Series) -> pd.Series:
    """Inventory status based on gap magnitude.
        Sufficient : gap <= 0
        Low        : gap in lower 50% of positive gaps
        Critical   : gap in upper 50% of positive gaps
    """
    positive_gaps = inventory_gap[inventory_gap > 0]
    threshold = positive_gaps.median() if len(positive_gaps) > 0 else 0
    conditions = [
        inventory_gap <= 0,
        (inventory_gap > 0) & (inventory_gap <= threshold),
    ]
    return np.select(conditions, ['Sufficient', 'Low'], default='Critical')


# =============================================================================
# STEP 1: Load Forecast Results
# =============================================================================

log_step('Loading forecast results...')

forecast_df = pd.read_csv(FORECAST_FILE)
forecast_df['material_id'] = forecast_df['material_id'].astype(str).str.strip()
forecast_df['forecast_date'] = pd.to_datetime(forecast_df['forecast_date'])

print(f'  Materials loaded  : {len(forecast_df)}')
print(f'  Columns available : {forecast_df.columns.tolist()}')


# =============================================================================
# STEP 2: Standardise Column Names
# =============================================================================

log_step('Standardising column names from forecast file...')

rename_map = {
    'Material_Lead_Time' : 'material_lead_time',
    'Moving_price'       : 'moving_price',
    'Unrestricted'       : 'unrestricted',
    'Lead_Time_Category' : 'lead_time_category',
    'High_Lead_Time_Flag': 'high_lead_time_flag',
    'XYZ_Class'          : 'xyz_class',
    'ABC_Class'          : 'abc_class',
}
forecast_df.rename(columns={k: v for k, v in rename_map.items()
                              if k in forecast_df.columns}, inplace=True)

# Ensure numeric columns are clean and non-negative
for col in ['material_lead_time', 'moving_price', 'unrestricted']:
    forecast_df[col] = pd.to_numeric(
        forecast_df.get(col, 0), errors='coerce'
    ).fillna(0).clip(lower=0)

print(f'  Lead time  → mean: {forecast_df["material_lead_time"].mean():.1f} days')
print(f'  Unit price → mean: {forecast_df["moving_price"].mean():.2f}')
print(f'  Stock      → mean: {forecast_df["unrestricted"].mean():.1f}')


# =============================================================================
# STEP 3: Apply Company Business Formulas
# =============================================================================

log_step('Applying company inventory planning formulas...')

df = forecast_df.copy()

# ── 1. Safety Stock (company formula) ────────────────────────────────────────
df['Safety_Stock'] = calc_safety_stock(
    df['forecast_demand'], df['material_lead_time']
)
print(f'  Safety_Stock    → mean: {df["Safety_Stock"].mean():.2f}, '
      f'max: {df["Safety_Stock"].max():.2f}')

# ── 2. Reorder Point ──────────────────────────────────────────────────────────
df['Reorder_Point'] = calc_reorder_point(
    df['forecast_demand'], df['Safety_Stock']
)
print(f'  Reorder_Point   → mean: {df["Reorder_Point"].mean():.2f}, '
      f'max: {df["Reorder_Point"].max():.2f}')

# ── 3. Inventory Gap ──────────────────────────────────────────────────────────
df['Inventory_Gap'] = calc_inventory_gap(
    df['Reorder_Point'], df['unrestricted']
)
print(f'  Inventory_Gap   → mean: {df["Inventory_Gap"].mean():.2f}')

# ── 4. Order Quantity ─────────────────────────────────────────────────────────
df['Order_Quantity'] = calc_order_quantity(df['Inventory_Gap'])
print(f'  Order_Quantity  → mean: {df["Order_Quantity"].mean():.2f}, '
      f'max: {df["Order_Quantity"].max():.2f}')

# ── 5. Order Cost ─────────────────────────────────────────────────────────────
df['Order_Cost'] = calc_order_cost(df['Order_Quantity'], df['moving_price'])
print(f'  Order_Cost      → total: {df["Order_Cost"].sum():,.2f}')

# ── 6. Suggested Action (company formula) ─────────────────────────────────────
df['Suggested_Action'] = assign_suggested_action(
    df['unrestricted'], df['Reorder_Point']
)
print(f'  Suggested_Action → {df["Suggested_Action"].value_counts().to_dict()}')

# ── 7. Inventory Status ───────────────────────────────────────────────────────
df['Inventory_Status'] = assign_inventory_status(df['Inventory_Gap'])
print(f'  Inventory_Status → {df["Inventory_Status"].value_counts().to_dict()}')


# =============================================================================
# STEP 4: Build Final Client Deliverable
# =============================================================================

log_step('Assembling final Prediction.csv...')

# Core columns — always in output
output_cols = [
    'material_id',
    'forecast_date',
    'forecast_demand',
    'material_lead_time',
    'moving_price',
    'unrestricted',
    'Safety_Stock',
    'Reorder_Point',
    'Inventory_Gap',
    'Order_Quantity',
    'Order_Cost',
    'Suggested_Action',
    'Inventory_Status',
]

# Optional columns — included if present
optional_cols = [
    'lead_time_category', 'high_lead_time_flag',
    'xyz_class', 'abc_class',
    'history_months', 'last_actual_date', 'last_actual_demand',
]
for col in optional_cols:
    if col in df.columns:
        output_cols.append(col)

prediction_df = df[[c for c in output_cols if c in df.columns]].copy()
prediction_df = prediction_df.sort_values('material_id').reset_index(drop=True)

print(f'  Rows    : {len(prediction_df)}')
print(f'  Columns : {prediction_df.columns.tolist()}')


# =============================================================================
# STEP 5: Business Summary Report
# =============================================================================

log_step('Business Summary Report')

action_counts      = prediction_df['Suggested_Action'].value_counts()
status_counts      = prediction_df['Inventory_Status'].value_counts()
total_order_cost   = prediction_df['Order_Cost'].sum()
materials_to_order = (prediction_df['Order_Quantity'] > 0).sum()
forecast_month     = prediction_df['forecast_date'].iloc[0].strftime('%B %Y')

print(f'  Forecast Month          : {forecast_month}')
print(f'  Total Materials         : {len(prediction_df)}')
print(f'  Materials to Order      : {materials_to_order}')
print(f'  Estimated Total Cost    : {total_order_cost:,.2f}')

print(f'\n  Suggested Action Breakdown:')
for action, count in action_counts.items():
    pct = count / len(prediction_df) * 100
    print(f'    {action:<25}: {count:>5} materials ({pct:.1f}%)')

print(f'\n  Inventory Status Breakdown:')
for status, count in status_counts.items():
    pct = count / len(prediction_df) * 100
    print(f'    {status:<15}: {count:>5} materials ({pct:.1f}%)')

print('\n  Sample Output (first 5 rows):')
print(prediction_df[['material_id', 'forecast_demand', 'Safety_Stock',
                      'Reorder_Point', 'unrestricted',
                      'Order_Quantity', 'Suggested_Action']].head(5).to_string(index=False))

print('\n  Key Metric Statistics:')
print(prediction_df[['forecast_demand', 'Safety_Stock', 'Reorder_Point',
                      'Order_Quantity', 'Order_Cost']].describe().round(2).to_string())


# =============================================================================
# STEP 6: Save Prediction.csv
# =============================================================================

prediction_df.to_csv(OUTPUT_FILE, index=False)

print(f'\n  Saved: {OUTPUT_FILE}  ({len(prediction_df)} materials)')
print(f'\n  Pipeline complete. Prediction.csv is ready for the client.')
