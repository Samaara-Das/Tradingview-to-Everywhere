import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import re
from typing import Dict, Any
import main
from datetime import datetime
import threading
import open_tv
import logger_setup
import time as time_module

class DarkTheme:
    BG = "#2b2b2b"
    FG = "#ffffff"
    BUTTON_BG = "#404040"
    BUTTON_ACTIVE = "#505050"
    ENTRY_BG = "#3b3b3b"
    ERROR = "#ff5555"
    SUCCESS = "#50fa7b"
    STATUS_BG = "#363636"

class ConfigGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TradingView Configuration")
        self.root.configure(bg=DarkTheme.BG)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("Custom.TEntry",
                           fieldbackground=DarkTheme.ENTRY_BG,
                           foreground=DarkTheme.FG)
        
        self.entries: Dict[str, tk.Entry] = {}
        self.running = False
        
        self._create_widgets()
        self._load_defaults()
        
    def _create_widgets(self):
        # Create main frame
        main_frame = tk.Frame(self.root, bg=DarkTheme.BG, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # Title
        title = tk.Label(main_frame, 
                        text="TradingView Settings",
                        font=("Helvetica", 16, "bold"),
                        bg=DarkTheme.BG,
                        fg=DarkTheme.FG)
        title.pack(pady=(0, 20))
        
        # Create input fields
        fields = [
            ("SCREENER_SHORT", str, "Short title of the screener"),
            ("DRAWER_SHORT", str, "Short title of the trade drawer"),
            ("SCREENER_NAME", str, "Name of the screener"),
            ("DRAWER_NAME", str, "Name of the trade drawer"),
            ("REMOVE_LOG", bool, "Remove content of log file"),
            ("INTERVAL_MINUTES", int, "Minutes between refreshes"),
            ("START_FRESH", bool, "Start fresh")
        ]
        
        for field_name, field_type, description in fields:
            frame = tk.Frame(main_frame, bg=DarkTheme.BG)
            frame.pack(fill='x', pady=5)
            
            label = tk.Label(frame,
                           text=f"{description}:",
                           bg=DarkTheme.BG,
                           fg=DarkTheme.FG)
            label.pack(side='left')
            
            if field_type == bool:
                var = tk.BooleanVar()
                entry = tk.Checkbutton(frame,
                                     variable=var,
                                     bg=DarkTheme.BG,
                                     fg=DarkTheme.FG,
                                     selectcolor=DarkTheme.BUTTON_BG,
                                     activebackground=DarkTheme.BG)
                self.entries[field_name] = var
            else:
                entry = tk.Entry(frame,
                               bg=DarkTheme.ENTRY_BG,
                               fg=DarkTheme.FG,
                               insertbackground=DarkTheme.FG)
                self.entries[field_name] = entry
            
            entry.pack(side='right')
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg=DarkTheme.BG)
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(button_frame,
                                    text="Start",
                                    command=self.start,
                                    bg=DarkTheme.BUTTON_BG,
                                    fg=DarkTheme.FG,
                                    activebackground=DarkTheme.BUTTON_ACTIVE,
                                    activeforeground=DarkTheme.FG,
                                    width=10)
        self.start_button.pack(side='left', padx=5)

        # Status frame
        status_frame = tk.Frame(main_frame, bg=DarkTheme.STATUS_BG, relief="sunken", bd=1)
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.status_label = tk.Label(status_frame,
                                   text="Ready to start...",
                                   bg=DarkTheme.STATUS_BG,
                                   fg=DarkTheme.FG,
                                   padx=10,
                                   pady=5)
        self.status_label.pack(fill='x')
    
    def _load_defaults(self):
        """Load default values from main.py into the GUI"""
        defaults = {
            "SCREENER_SHORT": main.SCREENER_SHORT,
            "DRAWER_SHORT": main.DRAWER_SHORT,
            "SCREENER_NAME": main.SCREENER_NAME,
            "DRAWER_NAME": main.DRAWER_NAME,
            "REMOVE_LOG": main.REMOVE_LOG,
            "INTERVAL_MINUTES": main.INTERVAL_MINUTES,
            "START_FRESH": main.START_FRESH
        }
        
        for key, value in defaults.items():
            if isinstance(self.entries[key], tk.BooleanVar):
                self.entries[key].set(value)
            else:
                self.entries[key].insert(0, str(value))

    def _update_main_constants(self):
        """Update the constants in main.py with values from GUI"""
        main.SCREENER_SHORT = self.entries["SCREENER_SHORT"].get()
        main.DRAWER_SHORT = self.entries["DRAWER_SHORT"].get()
        main.SCREENER_NAME = self.entries["SCREENER_NAME"].get()
        main.DRAWER_NAME = self.entries["DRAWER_NAME"].get()
        main.REMOVE_LOG = self.entries["REMOVE_LOG"].get()
        main.INTERVAL_MINUTES = int(self.entries["INTERVAL_MINUTES"].get())
        main.START_FRESH = self.entries["START_FRESH"].get()
        main.interval_seconds = main.INTERVAL_MINUTES * 60
    
    def _run_main_loop(self):
        """Run the main application loop in a separate thread"""
        try:
            # Update main.py constants with GUI values
            self._update_main_constants()
            
            # Run the main trading view loop
            main.run_trading_view(
                on_status_change=lambda msg, is_error: self.root.after(
                    0, 
                    lambda: self.status_label.config(
                        text=msg,
                        fg=DarkTheme.ERROR if is_error else DarkTheme.SUCCESS
                    )
                )
            )

        except Exception as e:
            self.root.after(0, self._handle_error, str(e))
    
    def _handle_error(self, error_msg):
        """Handle errors from the main loop thread"""
        self.status_label.config(
            text=f"Error: {error_msg}",
            fg=DarkTheme.ERROR
        )
        self.start_button.config(state='normal')
        self.running = False
    
    def validate_inputs(self) -> bool:
        """Validate all inputs before starting"""
        try:
            # Validate string inputs aren't empty
            for field in ["SCREENER_SHORT", "DRAWER_SHORT", "SCREENER_NAME", "DRAWER_NAME"]:
                if not self.entries[field].get().strip():
                    messagebox.showerror("Error", f"{field} cannot be empty")
                    return False
            
            # Validate INTERVAL_MINUTES is a positive integer
            interval = int(self.entries["INTERVAL_MINUTES"].get())
            if interval <= 0:
                messagebox.showerror("Error", "Interval minutes must be a positive number")
                return False
            
            return True
            
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please check all fields.")
            return False
    
    def start(self):
        """Start the trading view application"""
        if not self.validate_inputs():
            return
        
        self.running = True
        self.start_button.config(state='disabled')
        
        # Update status with timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_label.config(
            text=f"Application started at {current_time}",
            fg=DarkTheme.SUCCESS
        )
        
        # Start the main loop in a separate thread
        thread = threading.Thread(target=self._run_main_loop, daemon=True)
        thread.start()
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ConfigGUI()
    app.run() 