# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# %% [markdown]
# # 01 — Data Validation & Cleaning
# **Safety Stock Automation Pipeline | Notebook 1 of 5**
# 
# **Purpose:** Read the two monthly client uploads (`Consumption.xlsx` and `LeadTime.xlsx`), validate all business rules, clean the data, and save production-ready CSVs for the next notebook.
# 
# **Inputs:**
# - `Consumption.xlsx` — one month's consumption data uploaded by the client
# - `LeadTime.xlsx` — material master data uploaded by the client
# 
# **Outputs:**
# - `clean_consumption.csv`
# - `clean_leadtime.csv`
# 
# ---
# > ⚠️ **Do NOT perform any feature engineering in this notebook.**  
# > Only validation and cleaning steps are executed here.

# %% [markdown]
# ## 1. Imports & Configuration

# %%
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ── File paths ───────────────────────────────────────────────────────
from config.paths import CONSUMPTION_FILE, LEADTIME_FILE, OUTPUT_CONSUMPTION, OUTPUT_LEADTIME

# ── Required columns ─────────────────────────────────────────────────
REQUIRED_CONSUMPTION_COLS = ['material_id', 'date', 'demand']
REQUIRED_LEADTIME_COLS    = ['material_id', 'material_lead_time', 'moving_price', 'unrestricted']

print('Configuration loaded successfully.')

# %% [markdown]
# ## 2. Helper Functions

# %%
def log_step(msg: str) -> None:
    """Print a formatted pipeline step message."""
    print(f'\n[PIPELINE] {msg}')
    print('-' * 60)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and lowercase all column names, replacing spaces with underscores."""
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
    return df


def check_required_columns(df: pd.DataFrame, required: list, source: str) -> None:
    """Raise an error if any required column is missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f'[{source}] Missing required columns: {missing}')
    print(f'  ✓ All required columns present: {required}')


def check_missing_values(df: pd.DataFrame, required_cols: list, source: str) -> pd.DataFrame:
    """Report and drop rows with missing values in required columns."""
    before = len(df)
    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        print(f'  ⚠  Missing values detected in [{source}]:')
        print(null_counts[null_counts > 0].to_string())
        df = df.dropna(subset=required_cols)
        print(f'  → Dropped {before - len(df)} rows with missing required values.')
    else:
        print(f'  ✓ No missing values in required columns.')
    return df


def check_and_remove_duplicates(df: pd.DataFrame, subset: list, source: str) -> pd.DataFrame:
    """Report and remove duplicate rows based on a subset of columns."""
    before = len(df)
    duplicates = df.duplicated(subset=subset).sum()
    if duplicates > 0:
        print(f'  ⚠  Found {duplicates} duplicate row(s) in [{source}] on columns {subset}.')
        df = df.drop_duplicates(subset=subset, keep='first')
        print(f'  → Removed duplicates. Rows before: {before}, after: {len(df)}')
    else:
        print(f'  ✓ No duplicate rows found on columns {subset}.')
    return df


def flag_negative_values(df: pd.DataFrame, col: str, source: str, clip_to_zero: bool = True) -> pd.DataFrame:
    """Detect and handle negative values in a numeric column."""
    neg_count = (df[col] < 0).sum()
    if neg_count > 0:
        print(f'  ⚠  Found {neg_count} negative value(s) in [{source}].{col}.')
        if clip_to_zero:
            df[col] = df[col].clip(lower=0)
            print(f'  → Clipped negative values to 0 in column "{col}".')
    else:
        print(f'  ✓ No negative values in "{col}".')
    return df


print('Helper functions defined successfully.')

# %% [markdown]
# ## 3. Load Raw Data

# %%
log_step('Loading raw client files...')

# Load Consumption
if not os.path.exists(CONSUMPTION_FILE):
    raise FileNotFoundError(f'Consumption file not found: {CONSUMPTION_FILE}')
consumption_raw = pd.read_excel(CONSUMPTION_FILE)
print(f'  Consumption.xlsx loaded  → {consumption_raw.shape[0]} rows, {consumption_raw.shape[1]} columns')

# Load LeadTime
if not os.path.exists(LEADTIME_FILE):
    raise FileNotFoundError(f'LeadTime file not found: {LEADTIME_FILE}')
leadtime_raw = pd.read_excel(LEADTIME_FILE)
print(f'  LeadTime.xlsx loaded     → {leadtime_raw.shape[0]} rows, {leadtime_raw.shape[1]} columns')

# %% [markdown]
# ## 4. Standardize Column Names

# %%
log_step('Standardizing column names...')

consumption_df = standardize_columns(consumption_raw.copy())
leadtime_df    = standardize_columns(leadtime_raw.copy())

print(f'  Consumption columns : {consumption_df.columns.tolist()}')
print(f'  LeadTime columns    : {leadtime_df.columns.tolist()}')

# %%
consumption_df = consumption_df.melt(
    id_vars=['material_id'],
    var_name='date',
    value_name='demand'
)

# %% [markdown]
# ## 5. Validate Required Columns

# %%
log_step('Validating required columns...')

check_required_columns(consumption_df, REQUIRED_CONSUMPTION_COLS, 'Consumption')
check_required_columns(leadtime_df,    REQUIRED_LEADTIME_COLS,    'LeadTime')

# %%
consumption_df['date'] = pd.to_datetime(
    consumption_df['date'],
    format="%Y_%m"
)

# %% [markdown]
# ## 6. Validate & Fix Data Types

# %%
log_step('Validating and converting data types...')

# ── Consumption: material_id → str, date → datetime, demand → float ──
consumption_df['material_id'] = consumption_df['material_id'].astype(str).str.strip()

try:
    consumption_df['date'] = pd.to_datetime(consumption_df['date'])
    print('  ✓ Consumption "date" column converted to datetime.')
except Exception as e:
    raise ValueError(f'  ✗ Failed to parse "date" in Consumption: {e}')

# Check for invalid (NaT) dates after conversion
nat_count = consumption_df['date'].isna().sum()
if nat_count > 0:
    print(f'  ⚠  Found {nat_count} unparseable date(s) in Consumption → dropping those rows.')
    consumption_df = consumption_df.dropna(subset=['date'])

consumption_df['demand'] = pd.to_numeric(consumption_df['demand'], errors='coerce')
print('  ✓ Consumption "demand" converted to numeric.')

# ── LeadTime: material_id → str, numeric columns → float ─────────────
leadtime_df['material_id'] = leadtime_df['material_id'].astype(str).str.strip()

for col in ['material_lead_time', 'moving_price', 'unrestricted']:
    leadtime_df[col] = pd.to_numeric(leadtime_df[col], errors='coerce')
    print(f'  ✓ LeadTime "{col}" converted to numeric.')

# %% [markdown]
# ## 7. Handle Missing Values

# %%
log_step('Checking and handling missing values...')

consumption_df = check_missing_values(consumption_df, REQUIRED_CONSUMPTION_COLS, 'Consumption')
leadtime_df    = check_missing_values(leadtime_df,    REQUIRED_LEADTIME_COLS,    'LeadTime')

# %% [markdown]
# ## 8. Remove Duplicate Rows

# %%
log_step('Checking and removing duplicate rows...')

# Full-row duplicates
consumption_df = check_and_remove_duplicates(consumption_df, consumption_df.columns.tolist(), 'Consumption (all cols)')
leadtime_df    = check_and_remove_duplicates(leadtime_df,    leadtime_df.columns.tolist(),    'LeadTime (all cols)')

# Business key duplicates: material_id + date (one record per material per month)
print()
consumption_df = check_and_remove_duplicates(consumption_df, ['material_id', 'date'], 'Consumption (material_id + date)')

# material_id duplicates in lead time: aggregate numeric columns
dup_lt = leadtime_df['material_id'].duplicated().sum()
if dup_lt > 0:
    print(f'  ⚠  Found {dup_lt} duplicate material_id(s) in LeadTime → aggregating (mean for rates, sum for quantities).')
    agg_dict = {'material_lead_time': 'mean', 'moving_price': 'mean', 'unrestricted': 'sum'}
    # Include any extra business columns that are numeric
    extra_cols = [c for c in leadtime_df.columns if c not in ['material_id'] + list(agg_dict.keys())]
    for ec in extra_cols:
        if pd.api.types.is_numeric_dtype(leadtime_df[ec]):
            agg_dict[ec] = 'mean'
    leadtime_df = leadtime_df.groupby('material_id', as_index=False).agg(agg_dict)
    print(f'  → Aggregation complete. Unique materials: {len(leadtime_df)}')
else:
    print('  ✓ No duplicate material_id in LeadTime.')

# %% [markdown]
# ## 9. Validate Business Rules (Negative Values)

# %%
log_step('Checking for invalid negative values...')

# Consumption: negative demand → clip to 0
consumption_df = flag_negative_values(consumption_df, 'demand',              'Consumption', clip_to_zero=True)

# LeadTime: negative lead time, moving price, unrestricted → clip to 0
leadtime_df = flag_negative_values(leadtime_df, 'material_lead_time', 'LeadTime',    clip_to_zero=True)
leadtime_df = flag_negative_values(leadtime_df, 'moving_price',       'LeadTime',    clip_to_zero=True)
leadtime_df = flag_negative_values(leadtime_df, 'unrestricted',       'LeadTime',    clip_to_zero=True)

# %% [markdown]
# ## 10. Sort Data

# %%
log_step('Sorting data...')

consumption_df = consumption_df.sort_values(['material_id', 'date']).reset_index(drop=True)
leadtime_df    = leadtime_df.sort_values('material_id').reset_index(drop=True)

print('  ✓ Consumption sorted by material_id, date.')
print('  ✓ LeadTime sorted by material_id.')

# %% [markdown]
# ## 11. Final Summary & Save Outputs

# %%
log_step('Validation & Cleaning Summary')

print(f'  Consumption → {len(consumption_df)} rows | {consumption_df["material_id"].nunique()} unique materials')
print(f'  LeadTime    → {len(leadtime_df)} rows | {leadtime_df["material_id"].nunique()} unique materials')

# Preview
print('\n  Consumption sample:')
print(consumption_df.head(3).to_string(index=False))
print('\n  LeadTime sample:')
print(leadtime_df.head(3).to_string(index=False))

# Save
consumption_df.to_csv(OUTPUT_CONSUMPTION, index=False)
leadtime_df.to_csv(OUTPUT_LEADTIME,    index=False)

print(f'\n  ✅ Saved: {OUTPUT_CONSUMPTION}')
print(f'  ✅ Saved: {OUTPUT_LEADTIME}')
print('\n  Notebook 01 complete — proceed to Notebook 02: Feature Engineering.')


