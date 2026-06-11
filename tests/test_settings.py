import pytest
from settings import SettingsManager

def test_settings_default(temp_data_dir):
    manager = SettingsManager(temp_data_dir)
    assert manager.get("change_time") == "08:00"
    
    min_res = manager.get_min_resolution()
    assert min_res[0] == 1920
    assert min_res[1] == 1080

def test_settings_save_load(temp_data_dir):
    manager1 = SettingsManager(temp_data_dir)
    manager1.set_change_time(10, 30)
    manager1.set_min_resolution(2560, 1440)
    manager1.set("rijksmuseum_api_key", "secret123")
    
    manager2 = SettingsManager(temp_data_dir)
    assert manager2.get("change_time") == "10:30"
    assert manager2.get_min_resolution() == (2560, 1440)
    assert manager2.get("rijksmuseum_api_key") == "secret123"

def test_get_change_time_parsing(temp_data_dir):
    manager = SettingsManager(temp_data_dir)
    manager.set("change_time", "15:45")
    dt = manager.get_change_time()
    assert dt.hour == 15
    assert dt.minute == 45
