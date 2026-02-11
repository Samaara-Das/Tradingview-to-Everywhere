"""
TTE Combo Mode GUI — tkinter interface wrapping combo_main.py via subprocess.

Provides editable settings, Start/Stop buttons, and real-time log streaming.
Build with: pyinstaller --name TTE --onefile --windowed tte_gui.py
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
# Theme — Modern dark with blue accent
# ---------------------------------------------------------------------------


class Theme:
    # Base
    BG = "#1a1b2e"  # Deep navy background
    BG_CARD = "#232540"  # Slightly lighter card background
    BG_INPUT = "#2d2f4e"  # Input field background
    BG_HOVER = "#363860"  # Hover state

    # Text
    FG = "#e8e8f0"  # Primary text (soft white)
    FG_DIM = "#8b8da8"  # Secondary/label text
    FG_HEADING = "#ffffff"  # Headings

    # Accent
    ACCENT = "#6c7bff"  # Primary blue-purple accent
    ACCENT_HOVER = "#8490ff"

    # Status colors
    SUCCESS = "#4ade80"  # Green
    WARNING = "#fbbf24"  # Amber
    ERROR = "#f87171"  # Red
    INFO = "#60a5fa"  # Light blue

    # Buttons
    BTN_START = "#22c55e"
    BTN_START_HOVER = "#16a34a"
    BTN_STOP = "#ef4444"
    BTN_STOP_HOVER = "#dc2626"
    BTN_SAVE = "#6c7bff"
    BTN_SAVE_HOVER = "#8490ff"

    # Log
    LOG_BG = "#12132a"
    LOG_FG = "#c8c9e0"

    # Border / separator
    BORDER = "#3a3c5c"

    # Fonts
    FONT = "Segoe UI"
    FONT_MONO = "Cascadia Code"
    FONT_MONO_FALLBACK = "Consolas"


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
        self.root.configure(bg=Theme.BG)
        self.root.geometry("880x800")
        self.root.minsize(750, 650)

        self.process = None
        self.reader_thread = None
        self.running = False

        self.vars = {}

        self._configure_styles()
        self._build_ui()
        self._load_from_yaml()

    def _configure_styles(self):
        """Configure ttk styles for modern look."""
        style = ttk.Style()
        style.theme_use("clam")

        # Combobox
        style.configure(
            "Modern.TCombobox",
            fieldbackground=Theme.BG_INPUT,
            background=Theme.BG_INPUT,
            foreground=Theme.FG,
            arrowcolor=Theme.FG_DIM,
            borderwidth=0,
            padding=(8, 5),
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", Theme.BG_INPUT)],
            foreground=[("readonly", Theme.FG)],
            selectbackground=[("readonly", Theme.BG_INPUT)],
            selectforeground=[("readonly", Theme.FG)],
        )

        # Configure the Combobox dropdown (Listbox inside popdown)
        self.root.option_add("*TCombobox*Listbox.background", Theme.BG_INPUT)
        self.root.option_add("*TCombobox*Listbox.foreground", Theme.FG)
        self.root.option_add("*TCombobox*Listbox.selectBackground", Theme.ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", Theme.FG_HEADING)
        self.root.option_add("*TCombobox*Listbox.font", (Theme.FONT, 9))

    # =====================================================================
    # UI Construction
    # =====================================================================

    def _build_ui(self):
        # Outer container with padding
        outer = tk.Frame(self.root, bg=Theme.BG, padx=20, pady=16)
        outer.pack(fill="both", expand=True)

        # --- Header ---
        header = tk.Frame(outer, bg=Theme.BG)
        header.pack(fill="x", pady=(0, 16))

        tk.Label(
            header,
            text="TTE",
            font=(Theme.FONT, 22, "bold"),
            bg=Theme.BG,
            fg=Theme.ACCENT,
        ).pack(side="left")
        tk.Label(
            header,
            text="  Combo Mode",
            font=(Theme.FONT, 22),
            bg=Theme.BG,
            fg=Theme.FG_HEADING,
        ).pack(side="left")

        # Status indicator in header
        self.status_var = tk.StringVar(value="Ready")
        self.status_dot = tk.Label(
            header,
            text="\u2b24",  # Unicode filled circle
            font=(Theme.FONT, 8),
            bg=Theme.BG,
            fg=Theme.FG_DIM,
        )
        self.status_dot.pack(side="right", padx=(0, 6))
        self.status_label = tk.Label(
            header,
            textvariable=self.status_var,
            font=(Theme.FONT, 9),
            bg=Theme.BG,
            fg=Theme.FG_DIM,
        )
        self.status_label.pack(side="right")

        # --- Settings card ---
        card = tk.Frame(outer, bg=Theme.BG_CARD, padx=20, pady=16)
        card.pack(fill="x", pady=(0, 12))
        # Simulate rounded corners with a border frame
        card.configure(highlightbackground=Theme.BORDER, highlightthickness=1)

        # --- Chart row ---
        self._section_heading(card, "Chart")
        row = self._card_row(card)
        self._labeled_entry(row, "layout_name", "Layout", width=14)
        self._labeled_dropdown(
            row, "chart_timeframe", "Timeframe", TIMEFRAME_CHOICES, width=12
        )
        self._labeled_dropdown(
            row, "bar_style", "Bar Style", BAR_STYLE_CHOICES, width=14
        )
        self._modern_checkbox(row, "headless", "Headless")

        self._separator(card)

        # --- Screener row ---
        self._section_heading(card, "Screener")
        row = self._card_row(card)
        self._labeled_entry(row, "screener_shorttitle", "Short Title", width=14)
        self._labeled_entry(row, "screener_name", "Full Name", width=22)

        self._separator(card)

        # --- Alerts row ---
        self._section_heading(card, "Alerts")
        row = self._card_row(card)
        self._labeled_spinbox(row, "batch_size", "Batch Size", 1, 4, width=5)
        self._labeled_entry(row, "creation_delay", "Delay (s)", width=6)
        self._labeled_entry(row, "recalc_wait", "Recalc (s)", width=6)

        self._separator(card)

        # --- Maintenance + Webhook on same visual block ---
        cols = tk.Frame(card, bg=Theme.BG_CARD)
        cols.pack(fill="x", pady=(0, 4))

        left_col = tk.Frame(cols, bg=Theme.BG_CARD)
        left_col.pack(side="left", fill="x", expand=True)
        self._section_heading(left_col, "Maintenance")
        row = self._card_row(left_col)
        self._labeled_spinbox(
            row, "maintenance_interval", "Interval (s)", 60, 3600, width=7
        )

        right_col = tk.Frame(cols, bg=Theme.BG_CARD)
        right_col.pack(side="left", fill="x", expand=True)
        self._section_heading(right_col, "Webhook")
        row = self._card_row(right_col)
        self._labeled_entry(row, "webhook_url", "URL", width=38)

        # --- Options + Buttons row ---
        action_frame = tk.Frame(outer, bg=Theme.BG)
        action_frame.pack(fill="x", pady=(0, 12))

        # Options on the left
        opts = tk.Frame(action_frame, bg=Theme.BG)
        opts.pack(side="left")
        self._modern_checkbox(opts, "setup_only", "Setup Only")
        self._modern_checkbox(opts, "fresh", "Fresh (delete all)")
        self._modern_checkbox(opts, "maintain_only", "Maintain Only")

        # Buttons on the right
        btns = tk.Frame(action_frame, bg=Theme.BG)
        btns.pack(side="right")

        self.save_btn = self._action_button(
            btns, "Save Settings", Theme.BTN_SAVE, Theme.BTN_SAVE_HOVER, self._on_save
        )
        self.save_btn.pack(side="right", padx=(8, 0))

        self.stop_btn = self._action_button(
            btns, "Stop", Theme.BTN_STOP, Theme.BTN_STOP_HOVER, self._on_stop
        )
        self.stop_btn.pack(side="right", padx=(8, 0))
        self.stop_btn.configure(state="disabled")

        self.start_btn = self._action_button(
            btns, "Start", Theme.BTN_START, Theme.BTN_START_HOVER, self._on_start
        )
        self.start_btn.pack(side="right", padx=(8, 0))

        # --- Log output ---
        log_header = tk.Frame(outer, bg=Theme.BG)
        log_header.pack(fill="x", pady=(0, 6))
        tk.Label(
            log_header,
            text="Log Output",
            font=(Theme.FONT, 10, "bold"),
            bg=Theme.BG,
            fg=Theme.FG_DIM,
        ).pack(side="left")

        self.clear_log_btn = tk.Label(
            log_header,
            text="Clear",
            font=(Theme.FONT, 9),
            bg=Theme.BG,
            fg=Theme.ACCENT,
            cursor="hand2",
        )
        self.clear_log_btn.pack(side="right")
        self.clear_log_btn.bind("<Button-1>", lambda e: self._clear_log())
        self.clear_log_btn.bind(
            "<Enter>", lambda e: self.clear_log_btn.configure(fg=Theme.ACCENT_HOVER)
        )
        self.clear_log_btn.bind(
            "<Leave>", lambda e: self.clear_log_btn.configure(fg=Theme.ACCENT)
        )

        log_container = tk.Frame(
            outer,
            bg=Theme.LOG_BG,
            highlightbackground=Theme.BORDER,
            highlightthickness=1,
        )
        log_container.pack(fill="both", expand=True)

        # Try to use Cascadia Code, fall back to Consolas
        mono_font = Theme.FONT_MONO
        try:
            test = tk.Label(self.root, font=(Theme.FONT_MONO, 9))
            test.destroy()
        except tk.TclError:
            mono_font = Theme.FONT_MONO_FALLBACK

        self.log_text = tk.Text(
            log_container,
            bg=Theme.LOG_BG,
            fg=Theme.LOG_FG,
            font=(mono_font, 9),
            wrap="word",
            state="disabled",
            insertbackground=Theme.FG,
            relief="flat",
            bd=8,
            padx=4,
            pady=4,
        )
        scrollbar = tk.Scrollbar(
            log_container,
            command=self.log_text.yview,
            bg=Theme.BG_CARD,
            troughcolor=Theme.LOG_BG,
            activebackground=Theme.FG_DIM,
            width=10,
            relief="flat",
        )
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Log tag colors
        self.log_text.tag_configure("error", foreground=Theme.ERROR)
        self.log_text.tag_configure("warning", foreground=Theme.WARNING)
        self.log_text.tag_configure("success", foreground=Theme.SUCCESS)
        self.log_text.tag_configure("info", foreground=Theme.LOG_FG)

    # =====================================================================
    # Widget Helpers
    # =====================================================================

    def _section_heading(self, parent, text):
        tk.Label(
            parent,
            text=text.upper(),
            font=(Theme.FONT, 8, "bold"),
            bg=parent.cget("bg"),
            fg=Theme.FG_DIM,
            anchor="w",
        ).pack(fill="x", pady=(8, 4))

    def _card_row(self, parent):
        f = tk.Frame(parent, bg=parent.cget("bg"))
        f.pack(fill="x", pady=(0, 4))
        return f

    def _separator(self, parent):
        sep = tk.Frame(parent, bg=Theme.BORDER, height=1)
        sep.pack(fill="x", pady=(8, 4))

    def _labeled_entry(self, parent, key, label, width=20):
        container = tk.Frame(parent, bg=parent.cget("bg"))
        container.pack(side="left", padx=(0, 16))

        tk.Label(
            container,
            text=label,
            font=(Theme.FONT, 8),
            bg=parent.cget("bg"),
            fg=Theme.FG_DIM,
        ).pack(anchor="w")

        var = tk.StringVar()
        e = tk.Entry(
            container,
            textvariable=var,
            width=width,
            bg=Theme.BG_INPUT,
            fg=Theme.FG,
            insertbackground=Theme.FG,
            relief="flat",
            bd=0,
            font=(Theme.FONT, 10),
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
        )
        e.pack(ipady=4)
        self.vars[key] = var

    def _labeled_dropdown(self, parent, key, label, choices, width=12):
        container = tk.Frame(parent, bg=parent.cget("bg"))
        container.pack(side="left", padx=(0, 16))

        tk.Label(
            container,
            text=label,
            font=(Theme.FONT, 8),
            bg=parent.cget("bg"),
            fg=Theme.FG_DIM,
        ).pack(anchor="w")

        var = tk.StringVar()
        cb = ttk.Combobox(
            container,
            textvariable=var,
            values=choices,
            width=width,
            state="readonly",
            style="Modern.TCombobox",
            font=(Theme.FONT, 10),
        )
        cb.pack()
        self.vars[key] = var

    def _labeled_spinbox(self, parent, key, label, from_, to, width=5):
        container = tk.Frame(parent, bg=parent.cget("bg"))
        container.pack(side="left", padx=(0, 16))

        tk.Label(
            container,
            text=label,
            font=(Theme.FONT, 8),
            bg=parent.cget("bg"),
            fg=Theme.FG_DIM,
        ).pack(anchor="w")

        var = tk.IntVar()
        sb = tk.Spinbox(
            container,
            textvariable=var,
            from_=from_,
            to=to,
            width=width,
            bg=Theme.BG_INPUT,
            fg=Theme.FG,
            insertbackground=Theme.FG,
            relief="flat",
            bd=0,
            font=(Theme.FONT, 10),
            buttonbackground=Theme.BG_HOVER,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
        )
        sb.pack(ipady=4)
        self.vars[key] = var

    def _modern_checkbox(self, parent, key, label):
        var = tk.BooleanVar()
        cb = tk.Checkbutton(
            parent,
            text=label,
            variable=var,
            bg=parent.cget("bg"),
            fg=Theme.FG,
            selectcolor=Theme.BG_INPUT,
            activebackground=parent.cget("bg"),
            activeforeground=Theme.FG,
            font=(Theme.FONT, 9),
            cursor="hand2",
            highlightthickness=0,
            bd=0,
        )
        cb.pack(side="left", padx=(0, 16))
        self.vars[key] = var

    def _action_button(self, parent, text, bg_color, hover_color, command):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg="#ffffff",
            activebackground=hover_color,
            activeforeground="#ffffff",
            font=(Theme.FONT, 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=6,
            cursor="hand2",
            highlightthickness=0,
        )
        # Hover effects
        btn.bind("<Enter>", lambda e, b=btn, c=hover_color: b.configure(bg=c))
        btn.bind(
            "<Leave>",
            lambda e, b=btn, c=bg_color: (
                b.configure(bg=c) if b["state"] != "disabled" else None
            ),
        )
        return btn

    # =====================================================================
    # Load / Save YAML
    # =====================================================================

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
        self.vars["headless"].set(chart.get("headless", True))

        self.vars["screener_shorttitle"].set(screener.get("shorttitle", "Screener"))
        self.vars["screener_name"].set(screener.get("name", "TTE Screener"))

        self.vars["batch_size"].set(alerts.get("batch_size", 3))
        self.vars["creation_delay"].set(str(alerts.get("creation_delay", 1.5)))
        self.vars["recalc_wait"].set(str(alerts.get("recalc_wait", 2.0)))

        self.vars["maintenance_interval"].set(maintenance.get("interval", 300))

        self.vars["webhook_url"].set(webhook.get("url", ""))

        # CLI flags — setup, fresh, and maintenance enabled by default
        self.vars["setup_only"].set(False)
        self.vars["fresh"].set(True)
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

    # =====================================================================
    # Validation
    # =====================================================================

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

        if self.vars["setup_only"].get() and self.vars["maintain_only"].get():
            errors.append("Cannot use both Setup Only and Maintain Only")

        return errors

    # =====================================================================
    # Actions
    # =====================================================================

    def _on_save(self):
        errors = self._validate()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        try:
            data = self._build_yaml_data()
            save_settings(data)
            self._set_status("Settings saved", Theme.SUCCESS)
            self._log("Settings saved to combo_settings.yaml", "success")
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
        self._set_status("Running...", Theme.SUCCESS)

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
            self.start_btn.configure(state="disabled", bg=Theme.BG_HOVER)
            self.stop_btn.configure(state="normal")

            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()

        except Exception as e:
            self._log(f"Failed to start: {e}", "error")
            self._set_status("Error", Theme.ERROR)

    def _on_stop(self):
        if not self.process:
            return

        self._log("Sending stop signal...", "warning")
        self._set_status("Stopping...", Theme.WARNING)

        try:
            if sys.platform == "win32":
                os.kill(self.process.pid, signal.CTRL_BREAK_EVENT)
            else:
                self.process.send_signal(signal.SIGTERM)
        except OSError as e:
            self._log(f"Signal send failed: {e}", "error")

        threading.Thread(target=self._force_kill_after_timeout, daemon=True).start()

    def _force_kill_after_timeout(self):
        """Force-kill if process doesn't exit within 30 seconds."""
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self._log("Force-killing process (30s timeout)...", "error")
            self.process.kill()

    # =====================================================================
    # Output reading
    # =====================================================================

    def _read_output(self):
        """Read subprocess stdout line by line and append to log (runs in thread)."""
        try:
            for line in self.process.stdout:
                line = line.rstrip("\n")
                if line:
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
            exit_code = self.process.wait() if self.process else None
            self.root.after(0, self._on_process_ended, exit_code)

    def _on_process_ended(self, exit_code):
        self.running = False
        self.process = None
        self.start_btn.configure(state="normal", bg=Theme.BTN_START)
        self.stop_btn.configure(state="disabled")

        if exit_code == 0:
            self._set_status("Finished", Theme.SUCCESS)
            self._log("Process finished successfully.", "success")
        else:
            self._set_status(f"Stopped (code {exit_code})", Theme.WARNING)
            self._log(f"Process exited with code {exit_code}", "warning")

    # =====================================================================
    # Log + Status helpers
    # =====================================================================

    def _log(self, text: str, tag: str = "info"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n", tag)

        # Cap buffer
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        if line_count > LOG_MAX_LINES:
            self.log_text.delete("1.0", f"{line_count - LOG_MAX_LINES}.0")

        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _set_status(self, text: str, color: str = Theme.FG_DIM):
        self.status_var.set(text)
        self.status_label.configure(fg=color)
        self.status_dot.configure(fg=color)

    # =====================================================================
    # Run
    # =====================================================================

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        if self.running and self.process:
            if messagebox.askyesno(
                "Confirm Exit", "TTE is still running. Stop and exit?"
            ):
                self._on_stop()
                self.root.after(2000, self.root.destroy)
            return
        self.root.destroy()


if __name__ == "__main__":
    app = TTEGui()
    app.run()
