"""
gui.py
------
Safety Stock Automation — Professional Desktop GUI
Built with CustomTkinter (dark mode, blue theme).

Window layout
  ┌─────────────────────────────────────────────────────┐
  │  [Logo]   Safety Stock Automation          [dark]   │
  ├─────────────────────────────────────────────────────┤
  │  File Selection Panel                               │
  │  ┌────────────────────────────────────────────┐     │
  │  │  [📂 Browse Consumption]  filename.xlsx    │     │
  │  │  [📂 Browse LeadTime  ]  filename.xlsx    │     │
  │  └────────────────────────────────────────────┘     │
  ├─────────────────────────────────────────────────────┤
  │  [          ▶  RUN PIPELINE          ]              │
  │  ████████████████░░░░░░░░░░░░  progress bar         │
  ├─────────────────────────────────────────────────────┤
  │  Pipeline Stages                                    │
  │  ○ Data Validation & Cleaning                       │
  │  ○ Feature Engineering                              │
  │  ○ Update Historical Dataset                        │
  │  ○ SES Forecasting                                  │
  │  ○ Inventory Planning                               │
  ├─────────────────────────────────────────────────────┤
  │  Live Log                                           │
  │  ┌────────────────────────────────────────────┐     │
  │  │  scrollable log output ...                 │     │
  │  └────────────────────────────────────────────┘     │
  └─────────────────────────────────────────────────────┘
"""

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

# ── Import the pipeline runner (same package) ─────────────────────────────────
# gui.py lives in Final_Deployment/ and run_pipeline.py in python_script/
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "python_script"))
from run_pipeline import run_pipeline, PIPELINE_STAGES  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

APP_TITLE    = "Safety Stock Automation"
WINDOW_SIZE  = "1100x750"
ACCENT_BLUE  = "#1F6FEB"
SUCCESS_GRN  = "#2EA44F"
ERROR_RED    = "#F85149"
WARN_ORANGE  = "#D29922"
BG_CARD      = "#1C1C1E"        # slightly lighter than default dark bg
TEXT_MUTED   = "#8B949E"
TEXT_BRIGHT  = "#E6EDF3"
FONT_MONO    = ("Consolas", 11)
FONT_LABEL   = ("Segoe UI", 12)
FONT_TITLE   = ("Segoe UI Semibold", 22)
FONT_STAGE   = ("Segoe UI", 12)
FONT_BTN     = ("Segoe UI Semibold", 13)

# Stage status indicators
ICON_PENDING  = "○"
ICON_RUNNING  = "◉"
ICON_DONE     = "✓"
ICON_FAIL     = "✗"


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION CLASS
# ══════════════════════════════════════════════════════════════════════════════

class SafetyStockApp(ctk.CTk):
    """Top-level application window for Safety Stock Automation."""

    def __init__(self):
        super().__init__()

        # ── Global appearance ──────────────────────────────────────────────────
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(900, 650)
        self.configure(fg_color="#0D1117")

        # ── State ──────────────────────────────────────────────────────────────
        self._consumption_path = tk.StringVar(value="")
        self._leadtime_path    = tk.StringVar(value="")
        self._pipeline_running = False
        self._log_queue: queue.Queue = queue.Queue()

        # Stage widgets stored for live updates
        self._stage_icons  : list[ctk.CTkLabel] = []
        self._stage_labels : list[ctk.CTkLabel] = []

        # ── Build UI ───────────────────────────────────────────────────────────
        self._build_header()
        self._build_file_panel()
        self._build_run_panel()
        self._build_stages_panel()
        self._build_log_panel()

        # ── Start polling log queue ────────────────────────────────────────────
        self._poll_log_queue()

    # ══════════════════════════════════════════════════════════════════════════
    # UI BUILDERS
    # ══════════════════════════════════════════════════════════════════════════

    def _build_header(self) -> None:
        """Logo placeholder + application title bar."""
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=72)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Logo placeholder (coloured square — replace with CTkImage for real logo)
        logo_box = ctk.CTkFrame(header, width=46, height=46,
                                fg_color=ACCENT_BLUE, corner_radius=8)
        logo_box.pack(side="left", padx=(20, 14), pady=13)
        logo_box.pack_propagate(False)
        ctk.CTkLabel(logo_box, text="SS", font=("Segoe UI Semibold", 16),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        # Title + subtitle
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", pady=10)
        ctk.CTkLabel(title_frame, text=APP_TITLE,
                     font=FONT_TITLE, text_color=TEXT_BRIGHT).pack(anchor="w")
        ctk.CTkLabel(title_frame,
                     text="SES-powered monthly inventory planning pipeline",
                     font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")

        # Appearance mode toggle (right side)
        ctk.CTkOptionMenu(
            header, values=["Dark", "Light", "System"],
            command=lambda m: ctk.set_appearance_mode(m),
            width=90, height=30,
            fg_color="#21262D", button_color="#21262D",
            font=("Segoe UI", 11),
        ).pack(side="right", padx=20, pady=20)

    def _build_file_panel(self) -> None:
        """Two file-browse rows: Consumption and LeadTime."""
        outer = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        outer.pack(fill="x", padx=20, pady=(14, 0))

        ctk.CTkLabel(outer, text="Monthly Upload Files",
                     font=("Segoe UI Semibold", 13),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(12, 4))

        # Consumption row
        self._consumption_row = self._make_file_row(
            parent   = outer,
            label    = "Consumption.xlsx",
            var      = self._consumption_path,
            callback = self._browse_consumption,
            icon     = "📊",
        )

        # LeadTime row
        self._leadtime_row = self._make_file_row(
            parent   = outer,
            label    = "LeadTime.xlsx",
            var      = self._leadtime_path,
            callback = self._browse_leadtime,
            icon     = "📋",
        )

        ctk.CTkFrame(outer, fg_color="transparent", height=8).pack()

    def _make_file_row(self, parent, label: str, var: tk.StringVar,
                       callback, icon: str) -> ctk.CTkFrame:
        """Create a single file-browse row and return the row frame."""
        row = ctk.CTkFrame(parent, fg_color="#21262D", corner_radius=8)
        row.pack(fill="x", padx=16, pady=5)

        # Icon + label
        ctk.CTkLabel(row, text=f"  {icon}  {label}",
                     font=FONT_LABEL, text_color=TEXT_BRIGHT,
                     width=220, anchor="w").pack(side="left", padx=(10, 0), pady=10)

        # Filename display
        name_lbl = ctk.CTkLabel(row, textvariable=var,
                                font=("Segoe UI", 11), text_color=TEXT_MUTED,
                                anchor="w")
        name_lbl.pack(side="left", fill="x", expand=True, padx=10)

        # Browse button
        btn = ctk.CTkButton(row, text="Browse…", width=90, height=32,
                            font=("Segoe UI", 11),
                            fg_color="#30363D", hover_color="#3D444D",
                            command=callback)
        btn.pack(side="right", padx=10, pady=8)

        # Store button reference so we can disable it during run
        row._browse_btn = btn  # type: ignore[attr-defined]
        return row

    def _build_run_panel(self) -> None:
        """RUN PIPELINE button + progress bar."""
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.pack(fill="x", padx=20, pady=14)

        # RUN button
        self._run_btn = ctk.CTkButton(
            panel,
            text="▶   RUN PIPELINE",
            font=("Segoe UI Semibold", 15),
            height=48,
            fg_color=ACCENT_BLUE,
            hover_color="#1A5DC8",
            corner_radius=10,
            command=self._on_run_clicked,
        )
        self._run_btn.pack(fill="x")

        # Status label
        self._status_label = ctk.CTkLabel(
            panel, text="Select both files then click Run Pipeline.",
            font=("Segoe UI", 11), text_color=TEXT_MUTED,
        )
        self._status_label.pack(pady=(6, 4))

        # Progress bar (hidden until run starts)
        self._progress_bar = ctk.CTkProgressBar(panel, mode="indeterminate",
                                                height=6, corner_radius=3)
        self._progress_bar.pack(fill="x", pady=(0, 2))
        self._progress_bar.pack_forget()   # hidden initially

    def _build_stages_panel(self) -> None:
        """Row of pipeline stage indicators."""
        panel = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        panel.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(panel, text="Pipeline Stages",
                     font=("Segoe UI Semibold", 13),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(10, 6))

        stages_row = ctk.CTkFrame(panel, fg_color="transparent")
        stages_row.pack(fill="x", padx=12, pady=(0, 12))

        for i, stage in enumerate(PIPELINE_STAGES):
            cell = ctk.CTkFrame(stages_row, fg_color="#21262D", corner_radius=8)
            cell.pack(side="left", fill="x", expand=True, padx=4)

            icon_lbl = ctk.CTkLabel(cell, text=ICON_PENDING,
                                    font=("Segoe UI", 16), text_color=TEXT_MUTED)
            icon_lbl.pack(pady=(10, 2))

            name_lbl = ctk.CTkLabel(cell, text=stage["label"],
                                    font=("Segoe UI", 10), text_color=TEXT_MUTED,
                                    wraplength=150)
            name_lbl.pack(pady=(0, 10), padx=6)

            self._stage_icons.append(icon_lbl)
            self._stage_labels.append(name_lbl)

    def _build_log_panel(self) -> None:
        """Scrollable live log output area."""
        panel = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        panel.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Header row with Clear button
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(10, 4))
        ctk.CTkLabel(hdr, text="Live Log",
                     font=("Segoe UI Semibold", 13),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkButton(hdr, text="Clear", width=60, height=26,
                      font=("Segoe UI", 11),
                      fg_color="#21262D", hover_color="#30363D",
                      command=self._clear_log).pack(side="right")

        # Scrollable text box
        self._log_box = ctk.CTkTextbox(
            panel,
            font=FONT_MONO,
            wrap="word",
            fg_color="#0D1117",
            text_color="#C9D1D9",
            corner_radius=8,
            scrollbar_button_color="#30363D",
        )
        self._log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._log_box.configure(state="disabled")

        # Colour tags for the underlying tk.Text widget
        self._log_box._textbox.tag_configure("error",   foreground=ERROR_RED)
        self._log_box._textbox.tag_configure("success", foreground=SUCCESS_GRN)
        self._log_box._textbox.tag_configure("warn",    foreground=WARN_ORANGE)
        self._log_box._textbox.tag_configure("stage",   foreground=ACCENT_BLUE)
        self._log_box._textbox.tag_configure("muted",   foreground=TEXT_MUTED)

    # ══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def _browse_consumption(self) -> None:
        """Open file dialog for Consumption Excel."""
        path = filedialog.askopenfilename(
            title="Select Consumption Excel file",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if path:
            self._consumption_path.set(Path(path).name)
            self._consumption_full_path = path

    def _browse_leadtime(self) -> None:
        """Open file dialog for LeadTime Excel."""
        path = filedialog.askopenfilename(
            title="Select LeadTime Excel file",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if path:
            self._leadtime_path.set(Path(path).name)
            self._leadtime_full_path = path

    def _on_run_clicked(self) -> None:
        """Validate inputs and start the pipeline thread."""
        # Guard: files must be selected
        c_path = getattr(self, "_consumption_full_path", "")
        l_path = getattr(self, "_leadtime_full_path",    "")

        if not c_path:
            messagebox.showwarning("Missing File", "Please select a Consumption Excel file.")
            return
        if not l_path:
            messagebox.showwarning("Missing File", "Please select a LeadTime Excel file.")
            return
        if self._pipeline_running:
            return

        # Reset UI for fresh run
        self._reset_stages()
        self._clear_log()
        self._set_controls_enabled(False)
        self._show_progress(True)
        self._set_status("Pipeline running…", TEXT_MUTED)

        # Launch pipeline in background thread (keeps GUI responsive)
        thread = threading.Thread(
            target=self._pipeline_thread,
            args=(c_path, l_path),
            daemon=True,
        )
        thread.start()

    def _pipeline_thread(self, consumption_path: str, leadtime_path: str) -> None:
        """Background thread that calls run_pipeline() and signals the GUI via queue."""
        self._pipeline_running = True
        try:
            success, message = run_pipeline(
                consumption_path,
                leadtime_path,
                self._log_queue,
            )
            if success:
                self._log_queue.put(("DONE", message))
            else:
                self._log_queue.put(("FAIL", message))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self._log_queue.put(("LOG",  f"[UNEXPECTED ERROR]\n{tb}\n"))
            self._log_queue.put(("FAIL", str(e)))
        finally:
            self._pipeline_running = False

    # ══════════════════════════════════════════════════════════════════════════
    # QUEUE POLLING — bridges background thread → GUI updates
    # ══════════════════════════════════════════════════════════════════════════

    def _poll_log_queue(self) -> None:
        """Poll the inter-thread queue every 50 ms and dispatch GUI updates."""
        try:
            while True:
                kind, payload = self._log_queue.get_nowait()

                if kind == "LOG":
                    self._append_log(payload)

                elif kind == "STAGE_START":
                    self._update_stage(payload, "running")

                elif kind == "STAGE_DONE":
                    self._update_stage(payload, "done")

                elif kind == "STAGE_FAIL":
                    self._update_stage(payload, "fail")

                elif kind == "DONE":
                    self._on_pipeline_done(payload)

                elif kind == "FAIL":
                    self._on_pipeline_fail(payload)

        except queue.Empty:
            pass

        # Re-schedule polling
        self.after(50, self._poll_log_queue)

    # ══════════════════════════════════════════════════════════════════════════
    # PIPELINE OUTCOME HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_pipeline_done(self, message: str) -> None:
        """Called when all stages complete successfully."""
        self._set_controls_enabled(True)
        self._show_progress(False)
        self._set_status("✓ Pipeline completed successfully.", SUCCESS_GRN)
        self._append_log(f"\n{message}\n", tag="success")

        # Success dialog
        dialog = SuccessDialog(self, message)
        dialog.grab_set()
        self.wait_window(dialog)

    def _on_pipeline_fail(self, message: str) -> None:
        """Called when any stage fails."""
        self._set_controls_enabled(True)
        self._show_progress(False)
        self._set_status("✗ Pipeline failed. See log for details.", ERROR_RED)
        self._append_log(f"\n[PIPELINE FAILED]\n{message}\n", tag="error")

        messagebox.showerror(
            "Pipeline Failed",
            f"The pipeline encountered an error.\n\nCheck the log window for the full traceback.\n\n"
            f"First line: {message.splitlines()[0] if message else 'Unknown error'}",
        )

    # ══════════════════════════════════════════════════════════════════════════
    # LOG HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _append_log(self, text: str, tag: str = "") -> None:
        """Append text to the log box, auto-scrolling to the bottom."""
        self._log_box.configure(state="normal")

        # Detect keywords for auto-colouring if no explicit tag given
        if not tag:
            lower = text.lower()
            if any(k in lower for k in ("error", "failed", "traceback", "exception")):
                tag = "error"
            elif any(k in lower for k in ("✓", "success", "completed", "saved")):
                tag = "success"
            elif any(k in lower for k in ("warning", "⚠", "skipped")):
                tag = "warn"
            elif text.startswith("[STAGE") or text.startswith("==="):
                tag = "stage"

        if tag:
            self._log_box._textbox.insert("end", text, tag)
        else:
            self._log_box.insert("end", text)

        self._log_box.configure(state="disabled")
        self._log_box.see("end")

    def _clear_log(self) -> None:
        """Clear all text from the log box."""
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE INDICATOR HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _update_stage(self, idx: int, state: str) -> None:
        """Update the icon and colour of a stage indicator cell.

        Parameters
        ----------
        idx   : 0-based stage index.
        state : 'running' | 'done' | 'fail'
        """
        if idx >= len(self._stage_icons):
            return

        icon_lbl  = self._stage_icons[idx]
        name_lbl  = self._stage_labels[idx]

        if state == "running":
            icon_lbl.configure(text=ICON_RUNNING, text_color=ACCENT_BLUE)
            name_lbl.configure(text_color=ACCENT_BLUE)
        elif state == "done":
            icon_lbl.configure(text=ICON_DONE, text_color=SUCCESS_GRN)
            name_lbl.configure(text_color=SUCCESS_GRN)
        elif state == "fail":
            icon_lbl.configure(text=ICON_FAIL, text_color=ERROR_RED)
            name_lbl.configure(text_color=ERROR_RED)

    def _reset_stages(self) -> None:
        """Reset all stage indicators to the pending state."""
        for icon_lbl, name_lbl in zip(self._stage_icons, self._stage_labels):
            icon_lbl.configure(text=ICON_PENDING, text_color=TEXT_MUTED)
            name_lbl.configure(text_color=TEXT_MUTED)

    # ══════════════════════════════════════════════════════════════════════════
    # CONTROL STATE HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable interactive controls during pipeline execution."""
        state = "normal" if enabled else "disabled"
        self._run_btn.configure(state=state)
        self._consumption_row._browse_btn.configure(state=state)  # type: ignore[attr-defined]
        self._leadtime_row._browse_btn.configure(state=state)     # type: ignore[attr-defined]

    def _show_progress(self, visible: bool) -> None:
        """Show or hide the indeterminate progress bar."""
        if visible:
            self._progress_bar.pack(fill="x", pady=(0, 2))
            self._progress_bar.start()
        else:
            self._progress_bar.stop()
            self._progress_bar.pack_forget()

    def _set_status(self, text: str, colour: str = TEXT_MUTED) -> None:
        """Update the status label below the Run button."""
        self._status_label.configure(text=text, text_color=colour)


# ══════════════════════════════════════════════════════════════════════════════
# SUCCESS DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class SuccessDialog(ctk.CTkToplevel):
    """Modal dialog shown when the pipeline completes successfully."""

    def __init__(self, parent: SafetyStockApp, message: str):
        super().__init__(parent)
        self._parent  = parent
        self._message = message

        self.title("Pipeline Complete")
        self.geometry("500x320")
        self.resizable(False, False)
        self.configure(fg_color="#0D1117")
        self.lift()
        self.attributes("-topmost", True)

        # Resolve prediction folder / file paths
        self._pred_folder = PROJECT_ROOT / "Client_deliverable"
        self._pred_file   = self._pred_folder / "Prediction.csv"

        self._build()

    def _build(self) -> None:
        # Success icon
        ctk.CTkLabel(self, text="✅", font=("Segoe UI", 48)).pack(pady=(28, 4))

        # Title
        ctk.CTkLabel(self, text="Pipeline Completed Successfully",
                     font=("Segoe UI Semibold", 16),
                     text_color=SUCCESS_GRN).pack()

        # Sub-message
        ctk.CTkLabel(self, text="Prediction.csv has been generated.",
                     font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(pady=(4, 20))

        # Divider
        ctk.CTkFrame(self, fg_color="#30363D", height=1).pack(fill="x", padx=20)

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkButton(
            btn_frame, text="📁  Open Folder",
            fg_color="#21262D", hover_color="#30363D",
            font=("Segoe UI", 12), height=36,
            command=self._open_folder,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="📄  Open Prediction.csv",
            fg_color="#21262D", hover_color="#30363D",
            font=("Segoe UI", 12), height=36,
            command=self._open_file,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="🔄  Run Again",
            fg_color=ACCENT_BLUE, hover_color="#1A5DC8",
            font=("Segoe UI Semibold", 12), height=36,
            command=self._run_again,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="Exit",
            fg_color=ERROR_RED, hover_color="#C0392B",
            font=("Segoe UI Semibold", 12), height=36,
            command=self._exit_app,
        ).pack(side="left", fill="x", expand=True)

    def _open_folder(self) -> None:
        """Open the Final_prediction folder in Windows Explorer."""
        folder = self._pred_folder
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))

    def _open_file(self) -> None:
        """Open Prediction.csv with the default application."""
        if self._pred_file.exists():
            os.startfile(str(self._pred_file))
        else:
            messagebox.showwarning(
                "File Not Found",
                f"Prediction.csv not found at:\n{self._pred_file}",
            )

    def _run_again(self) -> None:
        """Close dialog and reset the main window for another run."""
        self.destroy()
        self._parent._reset_stages()
        self._parent._clear_log()
        self._parent._set_status(
            "Select both files then click Run Pipeline.", TEXT_MUTED
        )

    def _exit_app(self) -> None:
        """Exit the entire application."""
        self.destroy()
        self._parent.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = SafetyStockApp()
    app.mainloop()
