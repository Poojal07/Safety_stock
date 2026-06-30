"""
modules/pipeline.py
-------------------
Executes the five pipeline scripts via subprocess.
Returns a generator of (step_label, progress_fraction) tuples
so the UI can show business-friendly step messages.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Generator

# ── Resolve the Final_Deployment root (two levels above this file) ────────────
# streamlit_app/ sits alongside Final_Deployment/ — adjust as needed.
# The pipeline scripts are in Final_Deployment/python_script/
# ============================================================
# Project Paths
# ============================================================

from config.paths import (
    PROJECT_ROOT as DEPLOYMENT_ROOT,
    PYTHON_SCRIPT as SCRIPTS_DIR,
    MONTHLY_UPLOAD as MONTHLY_DIR,
    FINAL_PREDICTION_FILE as PREDICTION_FILE,
    FINAL_MONTH_DATA,
    DATA_SES,
    FINAL_PREDICTION,
    CLIENT_DELIVERABLE,
    CONSUMPTION_FILE,
    LEADTIME_FILE
)

# ── Business-friendly step labels shown in the UI ────────────────────────────
STEPS = [
    (0.12, "Uploading Files",                   None),
    (0.25, "Checking Data",                     "01_Data_Validation_Cleaning.py"),
    (0.40, "Preparing Dataset",                 "02_Feature_Engineering.py"),
    (0.55, "Updating Historical Records",       "03_Update_Historical_Data.py"),
    (0.70, "Forecasting Demand",                 "04_SES_Forecasting.py"),
    (0.85, "Inventory Planning",                "05_Inventory_Planning.py"),
    (0.95, "Generating Prediction",              None),
    (1.00, "Prediction Ready",                   None),
]


def _ensure_dirs() -> None:
    """Create required output directories if missing."""
    for folder in [
        MONTHLY_DIR,
        MONTHLY_DIR / "Clean",
        FINAL_MONTH_DATA,
        DATA_SES,
        FINAL_PREDICTION,
        CLIENT_DELIVERABLE,
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def _copy_uploads(consumption_bytes: bytes, leadtime_bytes: bytes) -> None:
    """Write uploaded file bytes to the Monthly_upload directory."""
    CONSUMPTION_FILE.write_bytes(consumption_bytes)
    LEADTIME_FILE.write_bytes(leadtime_bytes)


def _run_script(script_name: str) -> tuple[bool, str]:
    """Execute a single pipeline script and return (success, error_output)."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return False, f"Script not found: {script_path}"

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"]       = "1"

    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(DEPLOYMENT_ROOT),
        env=env,
    )
    if result.returncode != 0:
        return False, (result.stdout + "\n" + result.stderr).strip()
    return True, ""


def run_pipeline(
    consumption_bytes: bytes,
    leadtime_bytes: bytes,
) -> Generator[tuple[float, str, bool, str], None, None]:
    """Generator that runs the pipeline step by step.

    Yields (progress: float, label: str, success: bool, error: str)
    Each yield updates the UI progress bar and status message.
    """
    try:
        _ensure_dirs()

        for progress, label, script in STEPS:

            # ── File copy step ────────────────────────────────────────────────
            if script is None and progress == 0.10:
                _copy_uploads(consumption_bytes, leadtime_bytes)
                yield progress, label, True, ""
                continue

            # ── Final done step ───────────────────────────────────────────────
            if script is None:
                yield progress, label, True, ""
                continue

            # ── Script execution step ─────────────────────────────────────────
            yield progress - 0.01, f"Running: {label}", True, ""   # pre-step
            ok, err = _run_script(script)
            if not ok:
                yield progress, label, False, err
                return                                              # stop pipeline

            yield progress, label, True, ""

    except Exception as e:
        import traceback
        yield 1.0, "Pipeline Error", False, traceback.format_exc()


def get_prediction_path() -> Path:
    return PREDICTION_FILE


def prediction_exists() -> bool:
    return PREDICTION_FILE.exists()
