# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# %% [markdown]
# # 04 — SES Forecasting
# **Safety Stock Automation Pipeline | Notebook 4 of 5**
# 
# **Purpose:** Train a Simple Exponential Smoothing (SES) model for every material using its complete available history, then forecast the next month's demand.
# 
# **Input:**
# - `updated_historical_dataset.csv` (output of Notebook 03)
# 
# **Output:**
# - `forecast_results.csv`
# 
# ---
# > ✅ **Production model: Simple Exponential Smoothing (SES)**  
# > Selected for R² ≈ 0.68, Error Cost ≈ 29.23 Cr, ease of maintenance, and comparable performance to LightGBM.

# %% [markdown]
# ## 1. Imports & Configuration

# %%
import pandas as pd
import numpy as np
import warnings
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
warnings.filterwarnings('ignore')

# ── Setup path resolution for subprocess execution ────────────────────
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Input / Output paths ──────────────────────────────────────────────
from config.paths import UPDATED_HISTORICAL_DATA as INPUT_FILE, FORECAST_RESULTS as OUTPUT_FILE


# ── Column names (must match Notebook 02/03 output exactly) ──────────
DATE_COL     = 'Date'
DEMAND_COL   = 'Demand'
MATERIAL_COL = 'material_id'

# ── SES configuration ────────────────────────────────────────────────
MIN_HISTORY_MONTHS = 3    # minimum months of history to fit SES

print('Configuration loaded successfully.')

# %% [markdown]
# ## 2. Helper Functions

# %%
def log_step(msg: str) -> None:
    print(f'\n[PIPELINE] {msg}')
    print('-' * 60)


def load_csv_auto_date(path: str, date_col: str) -> pd.DataFrame:
    """Load CSV and parse the date column case-insensitively.
    Prevents ValueError when column is 'Date' but parse_dates expects 'date'.
    """
    df = pd.read_csv(path)

    # Find the date column regardless of casing
    col_map          = {c.lower(): c for c in df.columns}
    actual_date_col  = col_map.get(date_col.lower())

    if actual_date_col is None:
        raise ValueError(
            f'Date column "{date_col}" not found. Available columns: {df.columns.tolist()}'
        )

    df[actual_date_col] = pd.to_datetime(df[actual_date_col])

    # Standardize to the configured name
    if actual_date_col != date_col:
        df.rename(columns={actual_date_col: date_col}, inplace=True)

    return df


def forecast_ses(series: pd.Series, n_periods: int = 1) -> float:
    """Fit SES on a demand series and return the n-period-ahead forecast.

    Parameters
    ----------
    series    : Monthly demand values sorted chronologically (no NaN).
    n_periods : Steps ahead to forecast (default 1 = next month).

    Returns
    -------
    float : Forecasted demand (clipped to >= 0).
    """
    model = SimpleExpSmoothing(series.values, initialization_method='estimated')
    fit   = model.fit(optimized=True)
    return max(0.0, round(float(fit.forecast(n_periods)[-1]), 4))


def get_next_month(last_date: pd.Timestamp) -> pd.Timestamp:
    """Return the first day of the month following last_date."""
    return (last_date + relativedelta(months=1)).replace(day=1)


print('Helper functions defined.')

# %% [markdown]
# ## 3. Load Historical Data

# %%
log_step('Loading updated historical dataset...')

# Use auto-date loader — works whether column is 'Date' or 'date'
df = load_csv_auto_date(INPUT_FILE, DATE_COL)

df[MATERIAL_COL] = df[MATERIAL_COL].astype(str).str.strip()

# Sort using the correct column name from config
df = df.sort_values([MATERIAL_COL, DATE_COL]).reset_index(drop=True)

print(f'  Rows loaded       : {len(df)}')
print(f'  Unique materials  : {df[MATERIAL_COL].nunique()}')
print(f'  Date range        : {df[DATE_COL].min().date()} → {df[DATE_COL].max().date()}')
print(f'  Months of history : {df[DATE_COL].dt.to_period("M").nunique()}')

# %% [markdown]
# ## 4. Run SES Forecasting — One Model Per Material

# %%
log_step('Training SES model for each material and forecasting next month demand...')

results = []
skipped = []

materials = df[MATERIAL_COL].unique()
total     = len(materials)

for i, material in enumerate(materials, start=1):
    mat_df        = df[df[MATERIAL_COL] == material].sort_values(DATE_COL)
    demand_series = mat_df[DEMAND_COL].dropna()

    # Skip materials with insufficient history
    if len(demand_series) < MIN_HISTORY_MONTHS:
        skipped.append({
            MATERIAL_COL: material,
            'reason': f'Only {len(demand_series)} months of data (min: {MIN_HISTORY_MONTHS})'
        })
        continue

    try:
        forecast_value = forecast_ses(demand_series, n_periods=1)
        last_date      = mat_df[DATE_COL].max()
        forecast_date  = get_next_month(last_date)

        results.append({
            MATERIAL_COL          : material,
            'forecast_date'       : forecast_date,
            'forecast_demand'     : forecast_value,
            'history_months'      : len(demand_series),
            'last_actual_date'    : last_date.date(),
            'last_actual_demand'  : round(demand_series.iloc[-1], 4),
        })

    except Exception as e:
        skipped.append({MATERIAL_COL: material, 'reason': str(e)})

    if i % 100 == 0 or i == total:
        print(f'  Processed {i}/{total} materials...', end='\r')

print(f'\n  ✓ Forecasts generated : {len(results)}')
print(f'  ⚠  Materials skipped  : {len(skipped)}')

if skipped:
    print('\n  Skipped materials:')
    print(pd.DataFrame(skipped).to_string(index=False))

# %% [markdown]
# ## 5. Build Forecast Results DataFrame

# %%
log_step('Building forecast results and attaching master data...')

forecast_df = pd.DataFrame(results)

# Columns to carry forward from historical master data into forecast output
master_cols = [
    MATERIAL_COL, 'Material_Lead_Time', 'Moving_price', 'Unrestricted',
    'High_Lead_Time_Flag', 'Lead_Time_Category', 'XYZ_Class', 'ABC_Class'
]

# Use the most recent record per material for master data
latest_master = (
    df.sort_values(DATE_COL)
      .groupby(MATERIAL_COL)
      .last()
      .reset_index()
)[[c for c in master_cols if c in df.columns]]

forecast_df = forecast_df.merge(latest_master, on=MATERIAL_COL, how='left')

print(f'  Columns: {forecast_df.columns.tolist()}')
print(f'  Shape  : {forecast_df.shape}')
print('\n  Sample forecasts:')
print(forecast_df[[MATERIAL_COL, 'forecast_date', 'forecast_demand', 'history_months']].head(10).to_string(index=False))
print(f'\n  Forecast demand stats:')
print(forecast_df['forecast_demand'].describe().round(2).to_string())

# %% [markdown]
# ## 6. Save Output

# %%
forecast_df.to_csv(OUTPUT_FILE, index=False)

print(f'  ✅ Saved: {OUTPUT_FILE}  ({len(forecast_df)} materials forecasted)')
print('\n  Notebook 04 complete — proceed to Notebook 05: Inventory Planning.')


