# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# %% [markdown]
# # 03 — Update Historical Dataset
# **Safety Stock Automation Pipeline | Notebook 3 of 5**
# 
# **Purpose:** Append the current month's processed data to the master historical dataset. Remove any duplicate records and save the updated file.
# 
# **Inputs:**
# - `historical_dataset.csv` — master historical file (maintained across all months)
# - `processed_monthly_data.csv` — current month's processed data (output of Notebook 02)
# 
# **Output:**
# - `updated_historical_dataset.csv`
# 
# ---
# > ℹ️ **Only processed (feature-engineered) data is ever appended to the historical dataset.**  
# > Raw or cleaned-only data is never stored here.

# %% [markdown]
# ## 1. Imports & Configuration

# %%
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ── Input & Output paths ──────────────────────────────────────────────
from config.paths import HISTORICAL_DATA as HISTORICAL_FILE, PROCESSED_MONTHLY_DATA as MONTHLY_FILE, UPDATED_HISTORICAL_DATA as OUTPUT_FILE

# ── Date column name (matches Notebook 02 output) ────────────────────
DATE_COL = 'Date'

# ── Business key for deduplication ───────────────────────────────────
DEDUP_KEYS = ['material_id', DATE_COL]

print('Configuration loaded successfully.')

# %% [markdown]
# ## 2. Helper Functions

# %%
def log_step(msg: str) -> None:
    print(f'\n[PIPELINE] {msg}')
    print('-' * 60)


def load_csv_auto_date(path: str, date_col: str) -> pd.DataFrame:
    """Load a CSV and parse the date column safely regardless of its exact name casing.
    Avoids ValueError when parse_dates receives a column name that does not exist.
    """
    df = pd.read_csv(path)

    # Find the date column case-insensitively
    col_map = {c.lower(): c for c in df.columns}
    actual_date_col = col_map.get(date_col.lower())

    if actual_date_col is None:
        raise ValueError(f'Date column "{date_col}" not found in {path}. Available columns: {df.columns.tolist()}')

    df[actual_date_col] = pd.to_datetime(df[actual_date_col])

    # Rename to the standard name used throughout the pipeline
    if actual_date_col != date_col:
        df.rename(columns={actual_date_col: date_col}, inplace=True)

    return df


def load_historical(path: str, date_col: str) -> pd.DataFrame:
    """Load existing historical dataset, or return empty DataFrame on first run."""
    if os.path.exists(path):
        df = load_csv_auto_date(path, date_col)
        print(f'  ✓ Historical dataset loaded → {len(df)} rows, {df["material_id"].nunique()} materials')
        print(f'    Date range: {df[date_col].min().date()} → {df[date_col].max().date()}')
        return df
    else:
        print(f'  ℹ  No existing historical dataset found at "{path}".')
        print('  → First run: historical dataset will be created from this month\'s data.')
        return pd.DataFrame()


print('Helper functions defined.')

# %% [markdown]
# ## 3. Load Data

# %%
log_step('Loading historical and monthly datasets...')

historical_df = load_historical(HISTORICAL_FILE, DATE_COL)

monthly_df = load_csv_auto_date(MONTHLY_FILE, DATE_COL)
monthly_df['material_id'] = monthly_df['material_id'].astype(str).str.strip()

print(f'\n  Monthly data loaded → {len(monthly_df)} rows')
print(f'    Date range: {monthly_df[DATE_COL].min().date()} → {monthly_df[DATE_COL].max().date()}')

# %% [markdown]
# ## 4. Validate Month is Not Already in History

# %%
log_step('Checking for duplicate month in history...')

if not historical_df.empty:
    historical_df['material_id'] = historical_df['material_id'].astype(str).str.strip()

    monthly_periods = monthly_df[DATE_COL].dt.to_period('M').unique()
    hist_periods    = historical_df[DATE_COL].dt.to_period('M').unique()

    overlap = set(monthly_periods) & set(hist_periods)
    if overlap:
        print(f'  ⚠  Month(s) already in history — will be overwritten after dedup:')
        for p in sorted(overlap):
            print(f'     - {p}')
    else:
        print(f'  ✓ No overlap. Safe to append: {[str(p) for p in monthly_periods]}')
else:
    print('  ℹ  Historical dataset is empty — skipping overlap check.')

# %% [markdown]
# ## 5. Append Monthly Data to History

# %%
log_step('Appending monthly data to historical dataset...')

if historical_df.empty:
    combined_df = monthly_df.copy()
    print(f'  First-run mode → dataset initialized with {len(combined_df)} rows.')
else:
    combined_df = pd.concat([historical_df, monthly_df], ignore_index=True)
    print(f'  Combined rows (before dedup): {len(combined_df)}')

# %% [markdown]
# ## 6. Remove Duplicates on Business Key

# %%
log_step('Removing duplicate records (material_id + Date)...')

before = len(combined_df)

# Keep LAST occurrence — new monthly data wins over old history for same period
combined_df = combined_df.drop_duplicates(subset=DEDUP_KEYS, keep='last')

removed = before - len(combined_df)
if removed > 0:
    print(f'  → Removed {removed} duplicate record(s). Latest data kept for each (material_id, Date).')
else:
    print('  ✓ No duplicates found.')

print(f'  Final row count: {len(combined_df)}')

# %% [markdown]
# ## 7. Sort & Summarize

# %%
log_step('Sorting and summarizing the updated dataset...')

combined_df = combined_df.sort_values(['material_id', DATE_COL]).reset_index(drop=True)

print(f'  Total rows        : {len(combined_df)}')
print(f'  Unique materials  : {combined_df["material_id"].nunique()}')
print(f'  Date range        : {combined_df[DATE_COL].min().date()} → {combined_df[DATE_COL].max().date()}')
print(f'  Months in history : {combined_df[DATE_COL].dt.to_period("M").nunique()}')

print('\n  Sample (first 5 rows):')
print(combined_df.head(5).to_string(index=False))

# %% [markdown]
# ## 8. Save Updated Historical Dataset

# %%
combined_df.to_csv(OUTPUT_FILE, index=False)

print(f'  ✅ Saved: {OUTPUT_FILE}  ({len(combined_df)} rows)')
print('\n  Notebook 03 complete — proceed to Notebook 04: SES Forecasting.')


