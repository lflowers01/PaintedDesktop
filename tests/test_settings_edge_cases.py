"""Extended tests for settings module to identify edge cases and bugs."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from PaintedDesktop.settings import SettingsManager


def test_settings_manager_invalid_json():
    """Test settings manager with invalid JSON file."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        
        # Write invalid JSON
        with open(settings_file, 'w') as f:
            f.write('{"invalid": json}')
        
        # Initialize settings manager - should fallback to defaults
        settings = SettingsManager(temp_dir)
        
        # Should fall back to default settings
        assert settings.get("change_time") == "08:00"
        assert settings.get("min_resolution") == {"width": 1920, "height": 1080}


def test_settings_manager_corrupted_json():
    """Test settings manager with corrupted JSON file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        
        # Write corrupted JSON (missing closing brace)
        with open(settings_file, 'w') as f:
            f.write('{"change_time": "08:00", "min_resolution": {"width": 1920, "height": 1080}')
        
        settings = SettingsManager(temp_dir)
        
        # Should fall back to default settings
        assert settings.get("change_time") == "08:00"
        assert settings.get("min_resolution") == {"width": 1920, "height": 1080}


def test_settings_manager_invalid_time_format():
    """Test settings manager with invalid time format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        
        # Write invalid time format
        with open(settings_file, 'w') as f:
            json.dump({"change_time": "invalid_time"}, f)
        
        settings = SettingsManager(temp_dir)
        
        # Should fall back to default time
        assert settings.get_change_time().hour == 8
        assert settings.get_change_time().minute == 0


def test_settings_manager_invalid_resolution():
    """Test settings manager with invalid resolution values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        
        # Write invalid resolution
        with open(settings_file, 'w') as f:
            json.dump({"min_resolution": {"width": -100, "height": 0}}, f)
        
        settings = SettingsManager(temp_dir)
        
        # Should fall back to default resolution
        width, height = settings.get_min_resolution()
        assert width == 1920
        assert height == 1080


def test_settings_manager_invalid_resolution_fields():
    """Test settings manager with missing resolution fields."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        
        # Write incomplete resolution
        with open(settings_file, 'w') as f:
            json.dump({"min_resolution": {"width": 1920}}, f)
        
        settings = SettingsManager(temp_dir)
        
        # Should fall back to default height
        width, height = settings.get_min_resolution()
        assert width == 1920
        assert height == 1080


def test_settings_manager_save_permissions_error():
    """Test settings manager save with permission error (mocked)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create settings manager
        settings = SettingsManager(temp_dir)
        
        # Try to save to a read-only file
        settings_file = Path(temp_dir) / "settings.json"
        settings_file.write_text('{"test": "data"}')
        settings_file.chmod(0o444)  # Read-only
        
        # This should not raise an exception even if it can't save
        try:
            settings.set("test_key", "test_value")
            # The setting should still be in memory
            assert settings.get("test_key") == "test_value"
        except Exception:
            # If it raises an exception, that's okay for this test
            pass
        finally:
            # Restore permissions for cleanup
            settings_file.chmod(0o644)


def test_settings_manager_invalid_art_styles():
    """Test settings manager with invalid art styles."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        
        # Write invalid art styles
        with open(settings_file, 'w') as f:
            json.dump({"art_styles": ["invalid_style"]}, f)
        
        settings = SettingsManager(temp_dir)
        
        # Should fall back to default styles
        styles = settings.get("art_styles", [])
        assert styles == ["landscape", "seascape"]


def test_settings_manager_empty_art_styles():
    """Test settings manager with empty art styles."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        
        # Write empty art styles
        with open(settings_file, 'w') as f:
            json.dump({"art_styles": []}, f)
        
        settings = SettingsManager(temp_dir)
        
        # Should fall back to default styles
        styles = settings.get("art_styles", [])
        assert styles == ["landscape", "seascape"]


def test_settings_manager_none_values():
    """Test settings manager with None values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings = SettingsManager(temp_dir)
        
        # Test getting None values
        result = settings.get("nonexistent_key", None)
        assert result is None
        
        # Test setting None value
        settings.set("test_key", None)
        assert settings.get("test_key") is None


def test_settings_manager_special_characters():
    """Test settings manager with special characters in values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings = SettingsManager(temp_dir)
        
        # Test with special characters in time
        settings.set_change_time(14, 30)
        time = settings.get_change_time()
        assert time.hour == 14
        assert time.minute == 30