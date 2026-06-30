"""
run_pipeline.py
---------------
Orchestrator for the Safety Stock Automation pipeline.

Responsibilities
  - Accept paths to the two monthly client Excel uploads
  - Copy and rename them into Monthly_upload/
  - Execute the five pipeline scripts in order via subprocess
  - Stream stdout/stderr back to the caller through a queue
  - Return (success: bool, message: str)

Usage
  from python_script.run_pipeline import run_pipeline
  success, msg = run_pipeline(consumption_path, leadtime_path, log_queue)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


# ── Dynamic paths from config.paths ───────────────────────────────────────────
from config.paths import (
    PROJECT_ROOT,
    MONTHLY_UPLOAD as MONTHLY_UPLOAD_DIR,
    PYTHON_SCRIPT as SCRIPTS_DIR,
    DATA_SES,
    FINAL_PREDICTION,
    CLIENT_DELIVERABLE,
    FINAL_MONTH_DATA
)

# ── Pipeline stage definitions ────────────────────────────────────────────────
PIPELINE_STAGES = [
    {
        "label"  : "Data Validation & Cleaning",
        "script" : SCRIPTS_DIR / "01_Data_Validation_Cleaning.py",
    },
    {
        "label"  : "Feature Engineering",
        "script" : SCRIPTS_DIR / "02_Feature_Engineering.py",
    },
    {
        "label"  : "Update Historical Dataset",
        "script" : SCRIPTS_DIR / "03_Update_Historical_Data.py",
    },
    {
        "label"  : "SES Forecasting",
        "script" : SCRIPTS_DIR / "04_SES_Forecasting.py",
    },
    {
        "label"  : "Inventory Planning",
        "script" : SCRIPTS_DIR / "05_Inventory_Planning.py",
    },
]


def _ensure_dirs() -> None:
    """Create required output directories if they do not yet exist."""
    dirs = [
        MONTHLY_UPLOAD_DIR,
        MONTHLY_UPLOAD_DIR / "Clean",
        FINAL_MONTH_DATA,
        DATA_SES,
        FINAL_PREDICTION,
        CLIENT_DELIVERABLE,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def _copy_uploads(consumption_file: str, leadtime_file: str) -> None:
    """Copy client uploads into Monthly_upload/ with standardised names.

    Parameters
    ----------
    consumption_file : Absolute or relative path to the client's Consumption Excel.
    leadtime_file    : Absolute or relative path to the client's LeadTime Excel.
    """
    src_consumption = Path(consumption_file)
    src_leadtime    = Path(leadtime_file)

    if not src_consumption.exists():
        raise FileNotFoundError(f"Consumption file not found: {src_consumption}")
    if not src_leadtime.exists():
        raise FileNotFoundError(f"LeadTime file not found: {src_leadtime}")

    dest_consumption = MONTHLY_UPLOAD_DIR / "Consumption.xlsx"
    dest_leadtime    = MONTHLY_UPLOAD_DIR / "LeadTime.xlsx"

    shutil.copy2(src_consumption, dest_consumption)
    shutil.copy2(src_leadtime,    dest_leadtime)


def _run_script(script_path: Path, log_queue) -> tuple[bool, str]:
    """Execute a single Python script via subprocess.

    Streams every output line into log_queue so the GUI log window
    updates in real time.

    Parameters
    ----------
    script_path : Path to the .py script to execute.
    log_queue   : queue.Queue used for inter-thread GUI communication.

    Returns
    -------
    (True, "")          on success
    (False, traceback)  on non-zero exit
    """
    if not script_path.exists():
        msg = f"Script not found: {script_path}"
        log_queue.put(("LOG", f"[ERROR] {msg}\n"))
        return False, msg

    # Set PYTHONIOENCODING=utf-8 so subprocess stdout is always UTF-8 on Windows
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"]       = "1"       # Python 3.7+ UTF-8 mode

    process = subprocess.Popen(
        [sys.executable, "-X", "utf8", str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,       # merge stderr into stdout
        text=True,
        encoding="utf-8",
        errors="replace",              # replace any undecodable chars instead of crashing
        cwd=str(PROJECT_ROOT),         # scripts resolve relative paths from here
        env=env,
    )

    output_lines = []

    # Stream output line-by-line into the GUI log queue
    for line in process.stdout:
        log_queue.put(("LOG", line))
        output_lines.append(line)

    process.wait()

    if process.returncode != 0:
        error_text = "".join(output_lines)
        return False, error_text

    return True, ""


def run_pipeline(consumption_file: str, leadtime_file: str, log_queue) -> tuple[bool, str]:
    """Main entry point called by the GUI.

    Parameters
    ----------
    consumption_file : Path string to Consumption Excel chosen by user.
    leadtime_file    : Path string to LeadTime Excel chosen by user.
    log_queue        : queue.Queue for streaming log lines to the GUI.

    Returns
    -------
    (True,  success_message) if all five stages complete without error.
    (False, error_message)   if any stage fails.
    """
    try:
        # ── 0. Prepare directories ─────────────────────────────────────────────
        log_queue.put(("LOG", "[PIPELINE] Preparing workspace directories...\n"))
        _ensure_dirs()

        # ── 1. Copy uploads into standard location ─────────────────────────────
        log_queue.put(("LOG", f"[PIPELINE] Copying upload files...\n"))
        log_queue.put(("LOG", f"  Consumption : {consumption_file}\n"))
        log_queue.put(("LOG", f"  LeadTime    : {leadtime_file}\n"))
        _copy_uploads(consumption_file, leadtime_file)
        log_queue.put(("LOG", "[PIPELINE] Files copied successfully.\n\n"))

        # ── 2. Execute each pipeline stage in order ────────────────────────────
        for idx, stage in enumerate(PIPELINE_STAGES):
            label  = stage["label"]
            script = stage["script"]

            log_queue.put(("STAGE_START", idx))
            log_queue.put(("LOG", f"{'='*60}\n"))
            log_queue.put(("LOG", f"[STAGE {idx+1}/5] {label}\n"))
            log_queue.put(("LOG", f"{'='*60}\n"))

            success, error_text = _run_script(script, log_queue)

            if not success:
                log_queue.put(("STAGE_FAIL", idx))
                log_queue.put(("LOG", f"\n[ERROR] Stage '{label}' failed.\n"))
                log_queue.put(("LOG", f"{error_text}\n"))
                return False, f"Pipeline failed at stage: {label}\n\n{error_text}"

            log_queue.put(("STAGE_DONE", idx))
            log_queue.put(("LOG", f"\n[STAGE {idx+1}/5] ✓ {label} — Completed\n\n"))

        # ── 3. Success ─────────────────────────────────────────────────────────
        prediction_path = PROJECT_ROOT / "Client_deliverable" / "Prediction.csv"
        success_msg = (
            f"✅ Pipeline completed successfully.\n"
            f"Prediction.csv generated at:\n{prediction_path}"
        )
        log_queue.put(("LOG", f"\n{'='*60}\n"))
        log_queue.put(("LOG", success_msg + "\n"))
        log_queue.put(("LOG", f"{'='*60}\n"))
        return True, success_msg

    except FileNotFoundError as e:
        msg = f"File not found: {e}"
        log_queue.put(("LOG", f"[ERROR] {msg}\n"))
        return False, msg

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        log_queue.put(("LOG", f"[UNEXPECTED ERROR]\n{tb}\n"))
        return False, f"Unexpected error: {e}\n\n{tb}"
