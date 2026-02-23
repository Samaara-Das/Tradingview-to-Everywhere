"""
TTE Combo Mode GUI — tkinter interface wrapping combo_main.py via subprocess.

Provides editable settings, Start/Stop buttons, and real-time log streaming.
Build with: pyinstaller --name TTE --onefile --windowed tte_gui.py
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import pystray
import yaml
from dotenv import load_dotenv
from PIL import Image, ImageDraw

load_dotenv()


def _get_project_dir() -> Path:
    """Get the project root directory, handling both script and frozen exe."""
    if getattr(sys, "frozen", False):
        # Frozen exe in dist/ — project root is one level up
        return Path(sys.executable).parent.parent
    return Path(__file__).parent


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

SETTINGS_FILE = _get_project_dir() / "combo_settings.yaml"


def load_settings() -> dict:
    """Load combo_settings.yaml into nested dict."""
    if not SETTINGS_FILE.exists():
        return {}
    with open(SETTINGS_FILE) as f:
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

        # Start hidden — lives in system tray
        self.root.withdraw()

        self.process = None
        self.reader_thread = None
        self.running = False
        self.tray_icon = None

        self.vars = {}

        self._configure_styles()
        self._build_ui()
        self._load_from_yaml()

        # Auto-clear log every 3 hours (10_800_000 ms)
        self._schedule_log_clear()

        # Set up system tray icon
        self._setup_tray()

        # Auto-start in maintain-only mode after UI is ready
        self.root.after(1000, self._auto_start)

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
        self._labeled_dropdown(row, "chart_timeframe", "Timeframe", TIMEFRAME_CHOICES, width=12)
        self._labeled_dropdown(row, "bar_style", "Bar Style", BAR_STYLE_CHOICES, width=14)
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

        # --- Snapshot row ---
        self._section_heading(card, "Snapshot")
        row = self._card_row(card)
        self._modern_checkbox(row, "snapshot_enabled", "Enabled")
        self._labeled_entry(row, "snapshot_layout_name", "Layout", width=12)
        self._labeled_dropdown(row, "snapshot_bar_style", "Bar Style", BAR_STYLE_CHOICES, width=14)
        row = self._card_row(card)
        self._labeled_spinbox(row, "snapshot_batch_size", "Batch Size", 1, 20, width=5)
        self._labeled_spinbox(row, "snapshot_poll_interval", "Poll (s)", 30, 600, width=7)
        self._labeled_spinbox(row, "snapshot_bars_to_right", "Bars Right", 10, 200, width=7)

        self._separator(card)

        # --- Maintenance + Webhook on same visual block ---
        cols = tk.Frame(card, bg=Theme.BG_CARD)
        cols.pack(fill="x", pady=(0, 4))

        left_col = tk.Frame(cols, bg=Theme.BG_CARD)
        left_col.pack(side="left", fill="x", expand=True)
        self._section_heading(left_col, "Maintenance")
        row = self._card_row(left_col)
        self._labeled_spinbox(row, "maintenance_interval", "Interval (s)", 60, 3600, width=7)

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
        self.clear_log_btn.bind("<Leave>", lambda e: self.clear_log_btn.configure(fg=Theme.ACCENT))

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
            lambda e, b=btn, c=bg_color: (b.configure(bg=c) if b["state"] != "disabled" else None),
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
        self.vars["bar_style"].set(chart.get("bar_style", "candle"))
        self.vars["headless"].set(chart.get("headless", True))

        self.vars["screener_shorttitle"].set(screener.get("shorttitle", "Screener"))
        self.vars["screener_name"].set(screener.get("name", "TTE Screener"))

        self.vars["batch_size"].set(alerts.get("batch_size", 3))
        self.vars["creation_delay"].set(str(alerts.get("creation_delay", 1.5)))
        self.vars["recalc_wait"].set(str(alerts.get("recalc_wait", 2.0)))

        self.vars["maintenance_interval"].set(maintenance.get("interval", 300))

        snapshot = data.get("snapshot", {})
        self.vars["snapshot_enabled"].set(snapshot.get("enabled", True))
        self.vars["snapshot_layout_name"].set(snapshot.get("layout_name", "Snapshot"))
        self.vars["snapshot_bar_style"].set(snapshot.get("bar_style", "candle"))
        self.vars["snapshot_batch_size"].set(snapshot.get("batch_size", 5))
        self.vars["snapshot_poll_interval"].set(snapshot.get("poll_interval", 60))
        self.vars["snapshot_bars_to_right"].set(snapshot.get("bars_to_right", 60))

        default_url = "https://stock-buddy-app.vercel.app/api/tte/combo"
        env_url = os.environ.get("COMBO_WEBHOOK_URL", "")
        self.vars["webhook_url"].set(webhook.get("url", "") or env_url or default_url)

        # CLI flags — maintain-only enabled by default for background operation
        self.vars["setup_only"].set(False)
        self.vars["fresh"].set(False)
        self.vars["maintain_only"].set(True)

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
            "snapshot": {
                "enabled": self.vars["snapshot_enabled"].get(),
                "layout_name": self.vars["snapshot_layout_name"].get(),
                "bar_style": self.vars["snapshot_bar_style"].get(),
                "batch_size": self.vars["snapshot_batch_size"].get(),
                "poll_interval": self.vars["snapshot_poll_interval"].get(),
                "bars_to_right": self.vars["snapshot_bars_to_right"].get(),
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
        if getattr(sys, "frozen", False):
            python_exe = "python"
        else:
            python_exe = sys.executable

        project_dir = _get_project_dir()

        combo_main_path = project_dir / "combo_main.py"
        cmd = [python_exe, str(combo_main_path)]
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
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(project_dir),
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

        self._log("Stopping process...", "warning")
        self._set_status("Stopping...", Theme.WARNING)

        # Check if process is still running
        if self.process.poll() is not None:
            # Process already exited
            self._log("Process already stopped.", "info")
            self._on_process_ended(self.process.returncode)
            return

        # Send SIGBREAK to subprocess on Windows (allows graceful shutdown)
        try:
            if sys.platform == "win32":
                # Send Ctrl-Break signal (SIGBREAK) to the process group
                # This triggers the signal handler in tte/main.py
                import ctypes

                kernel32 = ctypes.windll.kernel32
                # CTRL_BREAK_EVENT = 1
                result = kernel32.GenerateConsoleCtrlEvent(1, self.process.pid)
                if result:
                    self._log(
                        f"Sent shutdown signal to process (PID {self.process.pid})",
                        "info",
                    )
                else:
                    self._log(
                        "Failed to send shutdown signal, will force terminate",
                        "warning",
                    )
                    raise Exception("GenerateConsoleCtrlEvent failed")
            else:
                # Unix: send SIGTERM
                self.process.terminate()
                self._log(f"Sent SIGTERM to process (PID {self.process.pid})", "info")
        except Exception as e:
            self._log(f"Error sending shutdown signal: {e}", "warning")
            # Fall back to force termination
            self._force_terminate()
            return

        # Wait up to 15 seconds for graceful shutdown
        threading.Thread(target=self._wait_for_graceful_shutdown, daemon=True).start()

    def _wait_for_graceful_shutdown(self):
        """Wait for process to exit gracefully, then force-kill if needed."""
        try:
            self.process.wait(timeout=15)
            self.root.after(0, self._log, "Process stopped gracefully", "success")
        except subprocess.TimeoutExpired:
            self.root.after(0, self._log, "Graceful shutdown timed out, force-killing...", "error")
            self.root.after(0, self._force_terminate)

    def _force_terminate(self):
        """Force-kill the subprocess and all Chrome/chromedriver children."""
        if not self.process:
            return

        try:
            if sys.platform == "win32":
                # Kill the entire process tree (Python subprocess + Chrome + chromedriver)
                # /F = force, /T = tree (all children), /PID = process ID
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                    capture_output=True,
                    timeout=10,
                )
                self._log(f"Force-killed process tree (PID {self.process.pid})", "warning")

                # Also kill any orphaned Chrome processes that might be from TTE
                # (in case they detached from the process tree)
                try:
                    ps_cmd = (
                        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' or Name='chromedriver.exe'\" | "
                        "Where-Object { $_.CommandLine -match 'TTE' } | "
                        "Select-Object -ExpandProperty ProcessId"
                    )
                    result = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_cmd],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    pids = [
                        p.strip() for p in result.stdout.strip().split("\n") if p.strip().isdigit()
                    ]
                    if pids:
                        for pid in pids:
                            subprocess.run(
                                ["taskkill", "/F", "/PID", pid],
                                capture_output=True,
                                timeout=5,
                            )
                        self._log(f"Cleaned up {len(pids)} orphaned Chrome processes", "info")
                except Exception as e:
                    self._log(f"Could not clean up orphaned Chrome processes: {e}", "warning")
            else:
                # Unix: send SIGKILL
                self.process.kill()
                self._log(f"Force-killed process (PID {self.process.pid})", "warning")

            # Wait for process to die
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._log("Force-kill timed out — process may still be running", "error")
        except Exception as e:
            self._log(f"Error during force termination: {e}", "error")

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
    # System Tray
    # =====================================================================

    def _create_tray_image(self):
        """Create a simple icon for the system tray."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Blue-purple filled circle (matches accent color)
        draw.ellipse([4, 4, 60, 60], fill=(108, 123, 255))
        # Dark inner circle for a ring look
        draw.ellipse([18, 18, 46, 46], fill=(26, 27, 46))
        return img

    def _setup_tray(self):
        """Set up the system tray icon with right-click menu."""
        image = self._create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._tray_show, default=True),
            pystray.MenuItem("Stop", self._tray_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._tray_exit),
        )
        self.tray_icon = pystray.Icon("TTE", image, "TTE Combo Mode", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _tray_show(self):
        """Show/restore the main window (called from tray)."""
        self.root.after(0, self._show_window)

    def _show_window(self):
        """Restore and bring the window to front."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _tray_stop(self):
        """Stop TTE process (called from tray)."""
        self.root.after(0, self._on_stop)

    def _tray_exit(self):
        """Exit the application completely (called from tray)."""
        self.root.after(0, self._exit_app)

    def _exit_app(self):
        """Stop process, remove tray icon, destroy window."""
        if self.running and self.process:
            self._on_stop()
            self.root.after(3000, self._cleanup_and_exit)
        else:
            self._cleanup_and_exit()

    def _cleanup_and_exit(self):
        """Remove tray icon and destroy the root window."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()

    # =====================================================================
    # Auto-start & Scheduled log clear
    # =====================================================================

    LOG_CLEAR_INTERVAL_MS = 3 * 60 * 60 * 1000  # 3 hours in milliseconds

    def _schedule_log_clear(self):
        """Schedule periodic log clearing every 3 hours."""
        self.root.after(self.LOG_CLEAR_INTERVAL_MS, self._auto_clear_log)

    def _auto_clear_log(self):
        """Clear the log and reschedule."""
        self._clear_log()
        self._log("Log auto-cleared (3-hour interval)", "info")
        self._schedule_log_clear()

    def _auto_start(self):
        """Automatically click Start on launch (for background/startup use)."""
        if not self.running:
            errors = self._validate()
            if errors:
                self._log("Auto-start skipped due to validation errors:", "warning")
                for err in errors:
                    self._log(f"  - {err}", "warning")
                return
            self._log("Auto-starting in maintain-only mode...", "info")
            self._on_start()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        """Window close (X) → hide to system tray instead of exiting."""
        self.root.withdraw()


if __name__ == "__main__":
    app = TTEGui()
    app.run()
