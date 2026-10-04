import json
from datetime import time
from pathlib import Path

from settings import SettingsManager


def test_defaults(temp_data_dir):
    manager = SettingsManager(temp_data_dir)
    assert manager.get_change_time() == time(8, 0)
    assert manager.get_min_resolution() is None  # match the screen
    assert manager.get_display_mode() == "fit"


def test_save_load(temp_data_dir):
    manager = SettingsManager(temp_data_dir)
    manager.set_change_time(10, 30)
    manager.set_min_resolution(2560, 1440)
    reloaded = SettingsManager(temp_data_dir)
    assert reloaded.get("change_time") == "10:30"
    assert reloaded.get_min_resolution() == (2560, 1440)


def test_v1_settings_migrate(temp_data_dir):
    Path(temp_data_dir, "settings.json").write_text(json.dumps({
        "change_time": "07:15", "min_resolution": {"width": 1920, "height": 1080},
        "last_wallpaper_date": "2026-06-23", "last_wallpaper_id": 138}))
    manager = SettingsManager(temp_data_dir)
    assert manager.get_change_time() == time(7, 15)
    assert manager.get_min_resolution() is None
    assert "last_wallpaper_date" not in manager.settings


def test_corrupted_or_invalid_values_fall_back(temp_data_dir):
    Path(temp_data_dir, "settings.json").write_text('{"invalid": json')
    manager = SettingsManager(temp_data_dir)
    assert manager.get("change_time") == "08:00"
    manager.settings.update(change_time="25:99", art_styles=["portrait"], min_resolution={"width": "x"})
    assert manager.get_change_time() == time(8, 0)
    assert manager.get_art_styles() == ["landscape"]
    assert manager.get_min_resolution() is None
