import sys
from pathlib import Path

# Resolve project root (streamlit_app/ directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ensure project root is in sys.path for subprocess scripts to import config
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Core Directories
MONTHLY_UPLOAD = PROJECT_ROOT / "Monthly_upload"
DATA = PROJECT_ROOT / "Data"
DATA_SES = PROJECT_ROOT / "Data_SES"
FINAL_MONTH_DATA = PROJECT_ROOT / "final_month_data"
FINAL_PREDICTION = PROJECT_ROOT / "Final_prediction"
CLIENT_DELIVERABLE = PROJECT_ROOT / "Client_deliverable"
PYTHON_SCRIPT = PROJECT_ROOT / "python_script"

# Specific Files
CONSUMPTION_FILE = MONTHLY_UPLOAD / "Consumption.xlsx"
LEADTIME_FILE = MONTHLY_UPLOAD / "LeadTime.xlsx"

OUTPUT_CONSUMPTION = MONTHLY_UPLOAD / "Clean" / "cleam_consumption.csv"
OUTPUT_LEADTIME = MONTHLY_UPLOAD / "Clean" / "clean_leadtime.csv"

INPUT_CONSUMPTION = OUTPUT_CONSUMPTION
INPUT_LEADTIME = OUTPUT_LEADTIME

PROCESSED_MONTHLY_DATA = FINAL_MONTH_DATA / "processed_monthly_data.csv"

HISTORICAL_DATA = DATA / "Final_dataset.csv"
UPDATED_HISTORICAL_DATA = DATA_SES / "updated_historical_dataset.csv"

FORECAST_RESULTS = FINAL_PREDICTION / "forecast_results.csv"
FINAL_PREDICTION_FILE = CLIENT_DELIVERABLE / "Prediction.csv"
