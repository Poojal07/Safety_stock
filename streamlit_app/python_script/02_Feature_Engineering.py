# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# %% [markdown]
# # 02 — Feature Engineering
# **Safety Stock Automation Pipeline | Notebook 2 of 5**
# 
# **Purpose:** Merge the cleaned monthly files and create the business features required for SES forecasting and inventory planning.
# 
# **Inputs:**
# - `clean_consumption.csv` (output of Notebook 01)
# - `clean_leadtime.csv` (output of Notebook 01)
# 
# **Output:**
# - `processed_monthly_data.csv`
# 
# ---
# ### Features created
# | Feature | Source | Description |
# |---------|--------|-------------|
# | `Year` | consumption | Year extracted from Date |
# | `Month` | consumption | Month name extracted from Date |
# | `mom_growth` | consumption | Month-over-Month demand growth |
# | `yoy_growth` | consumption | Year-over-Year demand growth (via Lag_1 & Lag_12) |
# | `CV` | consumption | Coefficient of Variation per material |
# | `High_Lead_Time_Flag` | leadtime | 1 if lead time ≥ 90th percentile |
# | `Lead_Time_Category` | leadtime | Short / Medium / Long / Very Long |
# | `XYZ_Class` | merged | X / Y / Z demand variability class |
# | `Reorder_Point` | merged | Lead Time Demand + Safety Stock |
# | `ABC_Class` | merged | A / B / C consumption value class |

# %% [markdown]
# ## 1. Imports & Configuration

# %%
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── Input & Output paths ──────────────────────────────────────────────
from config.paths import INPUT_CONSUMPTION, INPUT_LEADTIME, PROCESSED_MONTHLY_DATA as OUTPUT_FILE

print('Configuration loaded successfully.')

# %% [markdown]
# ## 2. Helper Functions

# %%
def log_step(msg: str) -> None:
    print(f'\n[PIPELINE] {msg}')
    print('-' * 60)


def classify_lead_time(x):
    """Data-driven lead time classification.
    Boundaries based on actual percentile distribution from project data:
      P25 ≈ 18 days  → Short cutoff at 21 (3 weeks, clean boundary)
      P50 ≈ 31 days  → Core of Medium bucket
      P75 ≈ 38 days  → Still Medium; Long starts at 45
      >90 days       → Very Long (genuine outlier tail)
    """
    if x < 21:
        return 'Short'
    elif x < 45:
        return 'Medium'
    elif x <= 90:
        return 'Long'
    else:
        return 'Very Long'


def xyz_class(cv):
    """XYZ classification based on Coefficient of Variation.
    X → stable demand   (CV <= 0.5)
    Y → moderate demand (CV <= 1.0)
    Z → erratic demand  (CV >  1.0)
    """
    if cv <= 0.5:
        return 'X'
    elif cv <= 1.0:
        return 'Y'
    else:
        return 'Z'


def abc_class(cumulative_pct):
    """ABC classification based on cumulative consumption value %.
    A → top 80% of value
    B → next 15% (80–95%)
    C → remaining 5%
    """
    if cumulative_pct <= 80:
        return 'A'
    elif cumulative_pct <= 95:
        return 'B'
    else:
        return 'C'


print('Helper functions defined.')

# %% [markdown]
# ## 3. Load Cleaned Data

# %%
log_step('Loading cleaned input files...')

consumption_df = pd.read_csv(INPUT_CONSUMPTION, parse_dates=['date'])
leadtime_df    = pd.read_csv(INPUT_LEADTIME)

# Standardize material_id to string
consumption_df['material_id'] = consumption_df['material_id'].astype(str).str.strip()
leadtime_df['material_id']    = leadtime_df['material_id'].astype(str).str.strip()

# Sort consumption by material_id and date
consumption_df = consumption_df.sort_values(['material_id', 'date']).reset_index(drop=True)

print(f'  Consumption → {consumption_df.shape[0]} rows, {consumption_df["material_id"].nunique()} materials')
print(f'  LeadTime    → {leadtime_df.shape[0]} rows')
print(f'\n  Consumption columns : {consumption_df.columns.tolist()}')
print(f'  LeadTime columns    : {leadtime_df.columns.tolist()}')

# %% [markdown]
# ## 4. Consumption Features — Date Parts

# %%
log_step('Creating date part features (Year, Month)...')

consumption_df['Year']  = consumption_df['date'].dt.year
consumption_df['Month'] = consumption_df['date'].dt.strftime('%b')   # e.g. Jan, Feb

print('  ✓ Year  created')
print('  ✓ Month created')
print(f'\n  Sample:\n{consumption_df[["material_id", "date", "Year", "Month", "demand"]].head(3).to_string(index=False)}')

# %% [markdown]
# ## 5. Consumption Features — MoM & YoY Growth
# 
# > **Note:** MoM and YoY growth require historical context (Lag_1 and Lag_12).  
# > For a single new month appended to history, these are computed across the full history per material.

# %%
log_step('Creating MoM and YoY growth features...')

# Lag_1 and Lag_12 are intermediate columns needed only for growth calculation
consumption_df['Lag_1'] = (
    consumption_df.groupby('material_id')['demand']
                  .shift(1)
)

consumption_df['Lag_12'] = (
    consumption_df.groupby('material_id')['demand']
                  .shift(12)
)

# Median per material — used to fill NaN lags for new/sparse materials
consumption_df['_median_demand'] = (
    consumption_df.groupby('material_id')['demand']
                  .transform('median')
)

consumption_df['Lag_1']  = consumption_df['Lag_1'].fillna(consumption_df['_median_demand'])
consumption_df['Lag_12'] = consumption_df['Lag_12'].fillna(consumption_df['_median_demand'])

# ── Month-over-Month Growth ──────────────────────────────────────────
consumption_df['mom_growth'] = (
    consumption_df.groupby('material_id')['demand']
    .transform(
        lambda x: (
            x.diff(1) /
            x.shift(1).replace(0, np.nan)
        )
    )
)
consumption_df['mom_growth'] = (
    consumption_df['mom_growth']
    .replace([np.inf, -np.inf], np.nan)
    .fillna(0)
)

# ── Year-over-Year Growth ────────────────────────────────────────────
consumption_df['yoy_growth'] = (
    (consumption_df['Lag_1'] - consumption_df['Lag_12'])
    / (consumption_df['Lag_12'] + 1)
)

# Drop intermediate helper columns
consumption_df.drop(columns=['Lag_1', 'Lag_12', '_median_demand'], inplace=True)

print('  ✓ mom_growth created')
print('  ✓ yoy_growth created')

# %% [markdown]
# ## 6. Consumption Features — CV (Coefficient of Variation)

# %%
log_step('Creating CV (Coefficient of Variation)...')

avg_demand  = consumption_df.groupby('material_id')['demand'].transform('mean')
std_demand  = consumption_df.groupby('material_id')['demand'].transform('std').fillna(0)

consumption_df['CV'] = (std_demand / (avg_demand + 1e-6)).round(4)

print('  ✓ CV created')
print(f'  CV stats: mean={consumption_df["CV"].mean():.3f}, max={consumption_df["CV"].max():.3f}')

# %% [markdown]
# ## 7. LeadTime Features — High_Lead_Time_Flag & Lead_Time_Category

# %%
log_step('Creating lead time features...')

# High Lead Time Flag: 1 if lead time >= 90th percentile
lt_threshold = leadtime_df['material_lead_time'].quantile(0.90)
print(f'  High Lead Time threshold (P90): {lt_threshold:.1f} days')

leadtime_df['High_Lead_Time_Flag'] = (
    leadtime_df['material_lead_time'] >= lt_threshold
).astype(int)

# Lead Time Category: Short / Medium / Long / Very Long
leadtime_df['Lead_Time_Category'] = (
    leadtime_df['material_lead_time']
    .apply(classify_lead_time)
)

print('  ✓ High_Lead_Time_Flag created')
print('  ✓ Lead_Time_Category created')
print(f'\n  Category distribution:')
print(leadtime_df['Lead_Time_Category'].value_counts().to_string())

# %% [markdown]
# ## 8. Merge Consumption & LeadTime

# %%
log_step('Merging consumption and lead time datasets...')

# Select only required columns from leadtime to keep output clean
lt_cols = ['material_id', 'material_lead_time', 'moving_price',
           'unrestricted', 'High_Lead_Time_Flag', 'Lead_Time_Category']

# Include Safety_Stock from leadtime if it exists (used for Reorder_Point)
if 'safety_stock' in leadtime_df.columns:
    lt_cols.append('safety_stock')

merged_df = consumption_df.merge(
    leadtime_df[[c for c in lt_cols if c in leadtime_df.columns]],
    on='material_id',
    how='inner'
)

unmatched = consumption_df['material_id'].nunique() - merged_df['material_id'].nunique()
if unmatched > 0:
    print(f'  ⚠  {unmatched} material(s) in Consumption had no match in LeadTime and were dropped.')
else:
    print('  ✓ All materials matched successfully.')

print(f'  Merged shape: {merged_df.shape}')

# %% [markdown]
# ## 9. Merged Features — XYZ Classification

# %%
log_step('Creating XYZ classification...')

merged_df['XYZ_Class'] = merged_df['CV'].apply(xyz_class)

print('  ✓ XYZ_Class created')
print(f'\n  XYZ distribution:')
print(merged_df.drop_duplicates('material_id')['XYZ_Class'].value_counts().to_string())

# %% [markdown]
# ## 10. Merged Features — Reorder Point

# %%
log_step('Creating Reorder Point...')

# Average demand per material (used for Lead Time Demand)
merged_df['_avg_demand'] = (
    merged_df.groupby('material_id')['demand'].transform('mean')
)

# Lead Time Demand = avg daily demand × lead time days
merged_df['_lead_time_demand'] = (
    merged_df['_avg_demand'] * (merged_df['material_lead_time'] / 30)
).round(4)

# Reorder Point = Lead Time Demand + Safety Stock
# If safety_stock column exists in data, use it; otherwise default to 0
if 'safety_stock' in merged_df.columns:
    ss_col = merged_df['safety_stock']
    print('  ✓ Using Safety_Stock from LeadTime file')
else:
    ss_col = 0
    print('  ℹ  Safety_Stock not in LeadTime file — Reorder_Point will equal Lead_Time_Demand.')
    print('     (Safety_Stock is computed in Notebook 05 — Inventory Planning)')

merged_df['Reorder_Point'] = (merged_df['_lead_time_demand'] + ss_col).round(4)

# Drop intermediate helper columns
merged_df.drop(columns=['_avg_demand', '_lead_time_demand'], inplace=True)

print('  ✓ Reorder_Point created')

# %% [markdown]
# ## 11. Merged Features — ABC Classification

# %%
log_step('Creating ABC classification...')

# Consumption Value = avg demand × unit price (one value per material)
abc_df = (
    merged_df[['material_id', 'demand', 'moving_price']]
    .groupby('material_id', as_index=False)
    .agg(avg_demand=('demand', 'mean'), moving_price=('moving_price', 'first'))
)
abc_df['Consumption_Value'] = (abc_df['avg_demand'] * abc_df['moving_price']).round(2)

# Sort descending and compute cumulative % of total consumption value
abc_df = abc_df.sort_values('Consumption_Value', ascending=False)
abc_df['Contribution_Pct']  = (abc_df['Consumption_Value'] / abc_df['Consumption_Value'].sum()) * 100
abc_df['Cumulative_Pct']    = abc_df['Contribution_Pct'].cumsum()
abc_df['ABC_Class']         = abc_df['Cumulative_Pct'].apply(abc_class)

# Merge ABC class back into merged_df
merged_df = merged_df.merge(
    abc_df[['material_id', 'ABC_Class']],
    on='material_id',
    how='left'
)

print('  ✓ ABC_Class created')
print(f'\n  ABC distribution:')
print(abc_df['ABC_Class'].value_counts().to_string())

# %% [markdown]
# ## 12. Select & Rename Final Columns

# %%
log_step('Selecting final output columns...')

# Rename columns to match original project naming convention
merged_df = merged_df.rename(columns={
    'date'               : 'Date',
    'demand'             : 'Demand',
    'material_lead_time' : 'Material_Lead_Time',
    'moving_price'       : 'Moving_price',
    'unrestricted'       : 'Unrestricted',
})

# Rename safety_stock if it came from leadtime file
if 'safety_stock' in merged_df.columns:
    merged_df.rename(columns={'safety_stock': 'Safety_Stock'}, inplace=True)

# Final column order — matching the index shown in the project screenshot
final_cols = [
    'material_id', 'Date', 'Demand', 'Year', 'Month',
    'mom_growth', 'yoy_growth', 'CV',
    'Unrestricted', 'Material_Lead_Time', 'Moving_price',
    'High_Lead_Time_Flag', 'Lead_Time_Category',
    'XYZ_Class', 'Reorder_Point', 'ABC_Class',
]

# Add Safety_Stock column if available from leadtime
if 'Safety_Stock' in merged_df.columns:
    final_cols.insert(final_cols.index('Unrestricted'), 'Safety_Stock')

# Keep only columns that exist (guards against optional columns being absent)
final_cols = [c for c in final_cols if c in merged_df.columns]
processed_df = merged_df[final_cols].copy()

processed_df = processed_df.sort_values(['material_id', 'Date']).reset_index(drop=True)

print(f'  Final columns : {processed_df.columns.tolist()}')
print(f'  Shape         : {processed_df.shape}')
print('\n  Sample rows:')
print(processed_df.head(5).to_string(index=False))

# %% [markdown]
# ## 13. Save Output

# %%
# OUTPUT_FILE = PROCESSED_MONTHLY_DATA
processed_df.to_csv(OUTPUT_FILE, index=False)

print(f'✅ Saved: {OUTPUT_FILE}  ({len(processed_df)} rows, {processed_df["material_id"].nunique()} materials)')
print('\n  Notebook 02 complete — proceed to Notebook 03: Update Historical Dataset.')

# %%
# %%
