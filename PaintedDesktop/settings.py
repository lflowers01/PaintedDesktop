"""Settings management for PaintedDesktop app."""

import json
import os
from pathlib import Path
from datetime import datetime, time
import tkinter as tk
from tkinter import ttk
import threading


class SettingsManager:
    """Manages settings.json read/write operations."""
    
    DEFAULT_SETTINGS = {
        "change_time": "08:00",
        "min_resolution": {"width": 1920, "height": 1080},
        "art_styles": ["landscape", "seascape"],
        "launch_at_startup": True,
        "last_wallpaper_date": None,
        "last_wallpaper_id": None,
    }
    
    def __init__(self, data_dir: str):
        """Initialize settings manager with app data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.data_dir / "settings.json"
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from JSON file or create with defaults."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**self.DEFAULT_SETTINGS, **loaded}
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()
    
    def save(self):
        """Save current settings to JSON file."""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set a setting value."""
        self.settings[key] = value
        self.save()
    
    def get_change_time(self) -> time:
        """Parse change time from settings."""
        time_str = self.settings.get("change_time", "08:00")
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))
    
    def set_change_time(self, hour: int, minute: int):
        """Set change time."""
        self.settings["change_time"] = f"{hour:02d}:{minute:02d}"
        self.save()
    
    def get_min_resolution(self) -> tuple:
        """Get minimum resolution as (width, height) tuple."""
        res = self.settings.get("min_resolution", {})
        return (res.get("width", 1920), res.get("height", 1080))
    
    def set_min_resolution(self, width: int, height: int):
        """Set minimum resolution."""
        self.settings["min_resolution"] = {"width": width, "height": height}
        self.save()


class SettingsWindow:
    """Settings UI window using tkinter."""
    
    def __init__(self, settings_manager: SettingsManager, on_close_callback=None):
        """Initialize settings window."""
        self.settings_manager = settings_manager
        self.on_close_callback = on_close_callback
        self.window = None
    
    def show(self):
        """Show the settings window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Tk()
        self.window.title("PaintedDesktop - Settings")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Change time setting
        ttk.Label(main_frame, text="Change Time (HH:MM):").grid(row=0, column=0, sticky=tk.W, pady=5)
        time_str = self.settings_manager.get("change_time", "08:00")
        time_var = tk.StringVar(value=time_str)
        ttk.Entry(main_frame, textvariable=time_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Min resolution
        ttk.Label(main_frame, text="Minimum Resolution:").grid(row=1, column=0, sticky=tk.W, pady=5)
        res_frame = ttk.Frame(main_frame)
        res_frame.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        min_res = self.settings_manager.get_min_resolution()
        width_var = tk.StringVar(value=str(min_res[0]))
        height_var = tk.StringVar(value=str(min_res[1]))
        
        ttk.Label(res_frame, text="Width:").pack(side=tk.LEFT)
        ttk.Entry(res_frame, textvariable=width_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(res_frame, text="Height:").pack(side=tk.LEFT)
        ttk.Entry(res_frame, textvariable=height_var, width=8).pack(side=tk.LEFT, padx=5)
        
        # Art styles
        ttk.Label(main_frame, text="Art Styles:").grid(row=2, column=0, sticky=tk.W, pady=5)
        styles_frame = ttk.Frame(main_frame)
        styles_frame.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        current_styles = set(self.settings_manager.get("art_styles", ["landscape", "seascape"]))
        landscape_var = tk.BooleanVar(value="landscape" in current_styles)
        seascape_var = tk.BooleanVar(value="seascape" in current_styles)
        veduta_var = tk.BooleanVar(value="veduta" in current_styles)
        
        ttk.Checkbutton(styles_frame, text="Landscape", variable=landscape_var).pack(anchor=tk.W)
        ttk.Checkbutton(styles_frame, text="Seascape", variable=seascape_var).pack(anchor=tk.W)
        ttk.Checkbutton(styles_frame, text="Veduta", variable=veduta_var).pack(anchor=tk.W)
        
        # Launch at startup
        startup_var = tk.BooleanVar(value=self.settings_manager.get("launch_at_startup", True))
        ttk.Checkbutton(main_frame, text="Launch at startup", variable=startup_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        def save_settings():
            """Save all settings."""
            # Parse and validate time
            try:
                time_parts = time_var.get().split(":")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                if 0 <= hour < 24 and 0 <= minute < 60:
                    self.settings_manager.set_change_time(hour, minute)
            except (ValueError, IndexError):
                pass
            
            # Parse and validate resolution
            try:
                width = int(width_var.get())
                height = int(height_var.get())
                if width > 0 and height > 0:
                    self.settings_manager.set_min_resolution(width, height)
            except ValueError:
                pass
            
            # Save other settings            
            styles = []
            if landscape_var.get():
                styles.append("landscape")
            if seascape_var.get():
                styles.append("seascape")
            if veduta_var.get():
                styles.append("veduta")
            self.settings_manager.set("art_styles", styles)
            
            self.settings_manager.set("launch_at_startup", startup_var.get())
            
            self.window.destroy()
            if self.on_close_callback:
                self.on_close_callback()
        
        ttk.Button(button_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        self.window.mainloop()
    
    def show_threaded(self):
        """Show settings window in a separate thread."""
        thread = threading.Thread(target=self.show, daemon=True)
        thread.start()
