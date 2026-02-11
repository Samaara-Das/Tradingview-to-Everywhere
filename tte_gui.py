"""
TTE Combo Mode GUI — tkinter interface wrapping combo_main.py via subprocess.

Provides editable settings, Start/Stop buttons, and real-time log streaming.
Build with: pyinstaller tte_gui.spec --onedir
"""

import os
import sys
import signal
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------


class DarkTheme:
    BG = "#2b2b2b"
    FG = "#ffffff"
    BUTTON_BG = "#404040"
    BUTTON_ACTIVE = "#505050"
    ENTRY_BG = "#3b3b3b"
    ENTRY_FG = "#ffffff"
    ERROR = "#ff5555"
    WARNING = "#ffb86c"
    SUCCESS = "#50fa7b"
    STATUS_BG = "#363636"
    LOG_BG = "#1e1e1e"
    LOG_FG = "#d4d4d4"
    ACCENT = "#6272a4"


# ---------------------------------------------------------------------------
# Settings YAML helpers
# ---------------------------------------------------------------------------

SETTINGS_FILE = Path(__file__).parent / "combo_settings.yaml"


def load_settings() -> dict:
    """Load combo_settings.yaml into nested dict."""
    if not SETTINGS_FILE.exists():
        return {}
    with open(SETTINGS_FILE, "r") as f:
        return yaml.safe_load(f) or {}


def save_settings(data: dict):
    """Write nested dict back to combo_settings.yaml, preserving structure."""
    with open(SETTINGS_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Main GUI
# ---------------------------------------------------------------------------

LOG_MAX_LINES = 5000

# Timeframe choices matching TradingView dropdown labels
TIMEFRAME_CHOICES = [
    "1 minute",
    "3 minutes",
    "5 minutes",
    "15 minutes",
    "30 minutes",
    "45 minutes",
    "1 hour",
    "2 hours",
    "3 hours",
    "4 hours",
    "1 day",
    "1 week",
    "1 month",
]

BAR_STYLE_CHOICES = [
    "candle",
    "line",
    "area",
    "ha",
    "hollowCandle",
    "bar",
    "lineWithMarkers",
    "stepline",
    "hlcArea",
    "baseline",
    "column",
    "hilo",
    "volCandles",
]


class TTEGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TTE Combo Mode")
        self.root.configure(bg=DarkTheme.BG)
        self.root.geometry("820x740")
        self.root.minsize(700, 600)

        self.process = None  # subprocess.Popen
        self.reader_thread = None
        self.running = False

        # Tkinter variables for fields
        self.vars = {}

        self._build_ui()
        self._load_from_yaml()

    # ----- UI construction -----

    def _build_ui(self):
        # Main scrollable area
        main = tk.Frame(self.root, bg=DarkTheme.BG, padx=16, pady=12)
        main.pack(fill="both", expand=True)

        # Title
        tk.Label(
            main,
            text="TTE Combo Mode",
            font=("Segoe UI", 18, "bold"),
            bg=DarkTheme.BG,
            fg=DarkTheme.FG,
        ).pack(anchor="w", pady=(0, 10))

        # Settings sections
        settings_frame = tk.Frame(main, bg=DarkTheme.BG)
        settings_frame.pack(fill="x")

        # --- Chart section ---
        self._section_label(settings_frame, "Chart")
        row = self._row(settings_frame)
        self._entry(row, "layout_name", "Layout", width=15)
        self._dropdown(row, "chart_timeframe", "Timeframe", TIMEFRAME_CHOICES, width=12)
        self._dropdown(row, "bar_style", "Bar Style", BAR_STYLE_CHOICES, width=14)
        self._checkbox(row, "headless", "Headless")

        # --- Screener section ---
        self._section_label(settings_frame, "Screener")
        row = self._row(settings_frame)
        self._entry(row, "screener_shorttitle", "Short Title", width=15)
        self._entry(row, "screener_name", "Full Name", width=20)

        # --- Alerts section ---
        self._section_label(settings_frame, "Alerts")
        row = self._row(settings_frame)
        self._spinbox(row, "batch_size", "Batch Size", 1, 4, width=5)
        self._float_entry(row, "creation_delay", "Delay (s)", width=6)
        self._float_entry(row, "recalc_wait", "Recalc (s)", width=6)

        # --- Maintenance section ---
        self._section_label(settings_frame, "Maintenance")
        row = self._row(settings_frame)
        self._spinbox(row, "maintenance_interval", "Interval (s)", 60, 3600, width=7)

        # --- Webhook section ---
        self._section_label(settings_frame, "Webhook")
        row = self._row(settings_frame)
        self._entry(row, "webhook_url", "URL", width=55)

        # --- Options (CLI flags) ---
        self._section_label(settings_frame, "Options")
        row = self._row(settings_frame)
        self._checkbox(row, "setup_only", "Setup Only")
        self._checkbox(row, "fresh", "Fresh (delete all)")
        self._checkbox(row, "maintain_only", "Maintain Only")

        # --- Buttons ---
        btn_frame = tk.Frame(main, bg=DarkTheme.BG)
        btn_frame.pack(fill="x", pady=(12, 6))

        self.start_btn = tk.Button(
            btn_frame,
            text="Start",
            width=12,
            command=self._on_start,
            bg="#2d6a4f",
            fg=DarkTheme.FG,
            activebackground="#40916c",
            activeforeground=DarkTheme.FG,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = tk.Button(
            btn_frame,
            text="Stop",
            width=12,
            command=self._on_stop,
            bg="#9b2226",
            fg=DarkTheme.FG,
            activebackground="#ae2012",
            activeforeground=DarkTheme.FG,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            state="disabled",
            cursor="hand2",
        )
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.save_btn = tk.Button(
            btn_frame,
            text="Save Settings",
            width=14,
            command=self._on_save,
            bg=DarkTheme.BUTTON_BG,
            fg=DarkTheme.FG,
            activebackground=DarkTheme.BUTTON_ACTIVE,
            activeforeground=DarkTheme.FG,
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2",
        )
        self.save_btn.pack(side="left")

        # --- Log output ---
        log_label = tk.Label(
            main,
            text="Log Output",
            font=("Segoe UI", 10, "bold"),
            bg=DarkTheme.BG,
            fg=DarkTheme.ACCENT,
        )
        log_label.pack(anchor="w", pady=(8, 2))

        log_frame = tk.Frame(main, bg=DarkTheme.LOG_BG)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            bg=DarkTheme.LOG_BG,
            fg=DarkTheme.LOG_FG,
            font=("Consolas", 9),
            wrap="word",
            state="disabled",
            insertbackground=DarkTheme.FG,
            relief="flat",
            bd=4,
        )
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Configure log tag colors
        self.log_text.tag_configure("error", foreground=DarkTheme.ERROR)
        self.log_text.tag_configure("warning", foreground=DarkTheme.WARNING)
        self.log_text.tag_configure("success", foreground=DarkTheme.SUCCESS)
        self.log_text.tag_configure("info", foreground=DarkTheme.LOG_FG)

        # --- Status bar ---
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            main,
            textvariable=self.status_var,
            bg=DarkTheme.STATUS_BG,
            fg=DarkTheme.FG,
            anchor="w",
            padx=8,
            pady=4,
            font=("Segoe UI", 9),
        )
        status_bar.pack(fill="x", pady=(6, 0))

    # ----- Widget helpers -----

    def _section_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=DarkTheme.BG,
            fg=DarkTheme.ACCENT,
        ).pack(anchor="w", pady=(8, 2))

    def _row(self, parent):
        f = tk.Frame(parent, bg=DarkTheme.BG)
        f.pack(fill="x", pady=2)
        return f

    def _entry(self, parent, key, label, width=20):
        tk.Label(
            parent,
            text=f"{label}:",
            bg=DarkTheme.BG,
            fg=DarkTheme.FG,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(0, 4))
        var = tk.StringVar()
        e = tk.Entry(
            parent,
            textvariable=var,
            width=width,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.FG,
            relief="flat",
            bd=3,
            font=("Segoe UI", 9),
        )
        e.pack(side="left", padx=(0, 12))
        self.vars[key] = var

    def _float_entry(self, parent, key, label, width=8):
        self._entry(parent, key, label, width)

    def _dropdown(self, parent, key, label, choices, width=12):
        tk.Label(
            parent,
            text=f"{label}:",
            bg=DarkTheme.BG,
            fg=DarkTheme.FG,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(0, 4))
        var = tk.StringVar()
        cb = ttk.Combobox(
            parent,
            textvariable=var,
            values=choices,
            width=width,
            state="readonly",
            font=("Segoe UI", 9),
        )
        cb.pack(side="left", padx=(0, 12))
        self.vars[key] = var

    def _spinbox(self, parent, key, label, from_, to, width=5):
        tk.Label(
            parent,
            text=f"{label}:",
            bg=DarkTheme.BG,
            fg=DarkTheme.FG,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=(0, 4))
        var = tk.IntVar()
        sb = tk.Spinbox(
            parent,
            textvariable=var,
            from_=from_,
            to=to,
            width=width,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.FG,
            relief="flat",
            bd=3,
            font=("Segoe UI", 9),
            buttonbackground=DarkTheme.BUTTON_BG,
        )
        sb.pack(side="left", padx=(0, 12))
        self.vars[key] = var

    def _checkbox(self, parent, key, label):
        var = tk.BooleanVar()
        cb = tk.Checkbutton(
            parent,
            text=label,
            variable=var,
            bg=DarkTheme.BG,
            fg=DarkTheme.FG,
            selectcolor=DarkTheme.ENTRY_BG,
            activebackground=DarkTheme.BG,
            activeforeground=DarkTheme.FG,
            font=("Segoe UI", 9),
            cursor="hand2",
        )
        cb.pack(side="left", padx=(0, 12))
        self.vars[key] = var

    # ----- Load / Save YAML -----

    def _load_from_yaml(self):
        data = load_settings()
        chart = data.get("chart", {})
        screener = data.get("screener", {})
        alerts = data.get("alerts", {})
        webhook = data.get("webhook", {})
        maintenance = data.get("maintenance", {})

        self.vars["layout_name"].set(chart.get("layout_name", "Screener"))
        self.vars["chart_timeframe"].set(chart.get("chart_timeframe", "1 minute"))
        self.vars["bar_style"].set(chart.get("bar_style", "line"))
        self.vars["headless"].set(chart.get("headless", False))

        self.vars["screener_shorttitle"].set(screener.get("shorttitle", "Screener"))
        self.vars["screener_name"].set(screener.get("name", "TTE Screener"))

        self.vars["batch_size"].set(alerts.get("batch_size", 3))
        self.vars["creation_delay"].set(str(alerts.get("creation_delay", 1.5)))
        self.vars["recalc_wait"].set(str(alerts.get("recalc_wait", 2.0)))

        self.vars["maintenance_interval"].set(maintenance.get("interval", 300))

        self.vars["webhook_url"].set(webhook.get("url", ""))

        # CLI flags default to unchecked
        self.vars["setup_only"].set(False)
        self.vars["fresh"].set(False)
        self.vars["maintain_only"].set(False)

    def _build_yaml_data(self) -> dict:
        """Build the nested dict from current GUI values."""
        return {
            "chart": {
                "layout_name": self.vars["layout_name"].get(),
                "chart_timeframe": self.vars["chart_timeframe"].get(),
                "bar_style": self.vars["bar_style"].get(),
                "headless": self.vars["headless"].get(),
            },
            "screener": {
                "shorttitle": self.vars["screener_shorttitle"].get(),
                "name": self.vars["screener_name"].get(),
            },
            "alerts": {
                "batch_size": self.vars["batch_size"].get(),
                "creation_delay": float(self.vars["creation_delay"].get()),
                "recalc_wait": float(self.vars["recalc_wait"].get()),
                "start_fresh": False,
            },
            "webhook": {
                "url": self.vars["webhook_url"].get(),
            },
            "maintenance": {
                "interval": self.vars["maintenance_interval"].get(),
            },
            "progress": {
                "file": "combo_progress.json",
            },
        }

    # ----- Validation -----

    def _validate(self) -> list[str]:
        errors = []
        if not self.vars["layout_name"].get().strip():
            errors.append("Layout name is required")
        if not self.vars["screener_shorttitle"].get().strip():
            errors.append("Screener short title is required")
        if not self.vars["screener_name"].get().strip():
            errors.append("Screener full name is required")

        try:
            bs = self.vars["batch_size"].get()
            if bs < 1 or bs > 4:
                errors.append("Batch size must be 1-4")
        except (ValueError, tk.TclError):
            errors.append("Batch size must be an integer")

        try:
            cd = float(self.vars["creation_delay"].get())
            if cd < 0:
                errors.append("Creation delay must be >= 0")
        except ValueError:
            errors.append("Creation delay must be a number")

        try:
            rw = float(self.vars["recalc_wait"].get())
            if rw < 0.5:
                errors.append("Recalc wait must be >= 0.5")
        except ValueError:
            errors.append("Recalc wait must be a number")

        try:
            mi = self.vars["maintenance_interval"].get()
            if mi < 60:
                errors.append("Maintenance interval must be >= 60")
        except (ValueError, tk.TclError):
            errors.append("Maintenance interval must be an integer")

        if not self.vars["webhook_url"].get().strip():
            errors.append("Webhook URL is required")

        # Mutual exclusion of setup_only and maintain_only
        if self.vars["setup_only"].get() and self.vars["maintain_only"].get():
            errors.append("Cannot use both Setup Only and Maintain Only")

        return errors

    # ----- Actions -----

    def _on_save(self):
        errors = self._validate()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        try:
            data = self._build_yaml_data()
            save_settings(data)
            self.status_var.set("Settings saved to combo_settings.yaml")
            self._log("Settings saved successfully.", "success")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _on_start(self):
        errors = self._validate()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        # Save settings first
        try:
            data = self._build_yaml_data()
            save_settings(data)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save settings:\n{e}")
            return

        # Build command
        cmd = [sys.executable, "combo_main.py"]
        if self.vars["setup_only"].get():
            cmd.append("--setup-only")
        if self.vars["maintain_only"].get():
            cmd.append("--maintain-only")
        if self.vars["fresh"].get():
            cmd.append("--fresh")

        self._log(f"Starting: {' '.join(cmd)}", "info")
        self.status_var.set("Running...")

        # Launch subprocess
        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(Path(__file__).parent),
                creationflags=creation_flags,
            )
            self.running = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")

            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()

        except Exception as e:
            self._log(f"Failed to start: {e}", "error")
            self.status_var.set("Error")

    def _on_stop(self):
        if not self.process:
            return

        self._log("Sending stop signal...", "warning")
        self.status_var.set("Stopping...")

        try:
            if sys.platform == "win32":
                # Send CTRL_BREAK_EVENT to the process group
                os.kill(self.process.pid, signal.CTRL_BREAK_EVENT)
            else:
                self.process.send_signal(signal.SIGTERM)
        except OSError as e:
            self._log(f"Signal send failed: {e}", "error")

        # Start timeout watcher
        threading.Thread(target=self._force_kill_after_timeout, daemon=True).start()

    def _force_kill_after_timeout(self):
        """Force-kill if process doesn't exit within 30 seconds."""
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self._log("Force-killing process (30s timeout)...", "error")
            self.process.kill()

    # ----- Output reading -----

    def _read_output(self):
        """Read subprocess stdout line by line and append to log (runs in thread)."""
        try:
            for line in self.process.stdout:
                line = line.rstrip("\n")
                if line:
                    # Determine tag based on content
                    tag = "info"
                    lower = line.lower()
                    if "error" in lower or "exception" in lower or "traceback" in lower:
                        tag = "error"
                    elif "warning" in lower or "warn" in lower:
                        tag = "warning"
                    elif "success" in lower or "created" in lower or "ready" in lower:
                        tag = "success"

                    self.root.after(0, self._log, line, tag)
        except Exception:
            pass
        finally:
            # Process has ended
            exit_code = self.process.wait() if self.process else None
            self.root.after(0, self._on_process_ended, exit_code)

    def _on_process_ended(self, exit_code):
        self.running = False
        self.process = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

        if exit_code == 0:
            self.status_var.set("Finished (exit code 0)")
            self._log("Process finished successfully.", "success")
        else:
            self.status_var.set(f"Stopped (exit code {exit_code})")
            self._log(f"Process exited with code {exit_code}", "warning")

    # ----- Log helper -----

    def _log(self, text: str, tag: str = "info"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n", tag)

        # Cap buffer
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        if line_count > LOG_MAX_LINES:
            self.log_text.delete("1.0", f"{line_count - LOG_MAX_LINES}.0")

        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ----- Run -----

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        if self.running and self.process:
            if messagebox.askyesno(
                "Confirm Exit", "TTE is still running. Stop and exit?"
            ):
                self._on_stop()
                # Wait briefly for process to end
                self.root.after(2000, self.root.destroy)
            return
        self.root.destroy()


if __name__ == "__main__":
    app = TTEGui()
    app.run()
