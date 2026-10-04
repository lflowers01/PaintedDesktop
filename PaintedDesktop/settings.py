"""User settings persisted in settings.json."""

import json
from datetime import time
from pathlib import Path
from typing import List, Optional, Tuple

from history import write_json_atomic

APP_VERSION = "2.0.0"
STYLES = {"landscape": "Landscapes", "seascape": "Seascapes", "veduta": "Cityscapes (veduta)"}


class SettingsManager:
    DEFAULT_SETTINGS = {
        "settings_version": 2,
        "change_time": "08:00",
        "min_resolution": None,  # None = match the primary monitor
        "art_styles": ["landscape", "seascape"],
        "display_mode": "fit",  # "fit" = whole painting with black bars, "fill" = crop to cover
        "launch_at_startup": True,
    }

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.data_dir / "settings.json"
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        try:
            loaded = json.loads(self.settings_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            loaded = {}
        if not isinstance(loaded, dict):
            loaded = {}
        if loaded.get("settings_version", 1) < 2:
            # v1 never auto-detected the screen, so a stored 1920x1080 is just its old default
            if loaded.get("min_resolution") == {"width": 1920, "height": 1080}:
                loaded["min_resolution"] = None
            loaded.pop("last_wallpaper_date", None)  # schedule now derives from history
            loaded.pop("last_wallpaper_id", None)
            loaded["settings_version"] = 2
        return {**self.DEFAULT_SETTINGS, **loaded}

    def save(self):
        write_json_atomic(self.settings_file, self.settings)

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def set(self, key: str, value):
        self.settings[key] = value
        self.save()

    def get_change_time(self) -> time:
        try:
            hour, minute = str(self.settings.get("change_time", "08:00")).split(":")
            return time(int(hour), int(minute))
        except (ValueError, TypeError):
            return time(8, 0)

    def set_change_time(self, hour: int, minute: int):
        self.set("change_time", f"{hour:02d}:{minute:02d}")

    def get_min_resolution(self) -> Optional[Tuple[int, int]]:
        """Custom minimum (width, height), or None to match the screen."""
        res = self.settings.get("min_resolution")
        try:
            width, height = int(res["width"]), int(res["height"])
            return (width, height) if width > 0 and height > 0 else None
        except (KeyError, TypeError, ValueError):
            return None

    def set_min_resolution(self, width: Optional[int], height: Optional[int] = None):
        self.set("min_resolution", {"width": width, "height": height} if width and height else None)

    def get_art_styles(self) -> List[str]:
        styles = [s for s in self.settings.get("art_styles") or [] if s in STYLES]
        return styles or ["landscape"]

    def get_display_mode(self) -> str:
        return "fill" if self.settings.get("display_mode") == "fill" else "fit"
