import pytest
import json
from pathlib import Path
from history import HistoryManager

def test_history_creation(temp_data_dir):
    manager = HistoryManager(temp_data_dir)
    assert manager.history == []
    assert manager.get_last_entry() is None

def test_history_add_entry(temp_data_dir):
    manager = HistoryManager(temp_data_dir)
    entry = manager.add_entry(
        title="Test Painting",
        artist="Test Artist",
        year="1800",
        source_institution="Test Source",
        source_url="http://test.com",
        image_url="http://test.com/image.jpg",
        painting_id="12345",
        image_path="/path/to/image.jpg"
    )
    
    assert len(manager.history) == 1
    assert entry['title'] == "Test Painting"
    
    last = manager.get_last_entry()
    assert last['painting_id'] == "12345"

def test_history_save_load(temp_data_dir):
    # Add an entry
    manager1 = HistoryManager(temp_data_dir)
    manager1.add_entry(
        title="Test Painting 1",
        artist="Test Artist 1",
        year="1801",
        source_institution="Test Source",
        source_url="http://test.com",
        image_url="http://test.com/image.jpg",
        painting_id="999",
        image_path="/path/to/image.jpg"
    )
    
    # Reload from same dir
    manager2 = HistoryManager(temp_data_dir)
    assert len(manager2.history) == 1
    assert manager2.get_last_entry()['title'] == "Test Painting 1"
    
    # Check used IDs
    used = manager2.get_used_ids()
    assert "999" in used


def test_used_ids_are_strings_including_legacy_ints(temp_data_dir):
    Path(temp_data_dir, "history.json").write_text(json.dumps([{"painting_id": 138, "date_set": "2026-06-23T12:20:58.598895"}]))
    manager = HistoryManager(temp_data_dir)
    assert manager.get_used_ids() == {"138"}
    assert manager.last_set_time().day == 23


def test_corrupted_history_starts_empty(temp_data_dir):
    Path(temp_data_dir, "history.json").write_text('{"invalid": json')
    manager = HistoryManager(temp_data_dir)
    assert manager.get_history() == [] and manager.last_set_time() is None
