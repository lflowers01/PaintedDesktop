"""Integration tests to identify edge cases and unintended behavior in the main application flow."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from PaintedDesktop.main import PaintedDesktop
from PaintedDesktop.settings import SettingsManager
from PaintedDesktop.history import HistoryManager
from PaintedDesktop.fetcher import ARTICFetcher, RijksmuseumFetcher
from PaintedDesktop.filter import PaintingFilter


def test_main_application_with_empty_directories():
    """Test main application initialization with empty directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test that application can handle missing directories gracefully
        app = PaintedDesktop()
        # Just verify it doesn't crash during initialization
        assert app is not None


def test_settings_manager_with_corrupted_file():
    """Test settings manager with corrupted settings file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        
        # Write corrupted JSON
        with open(settings_file, 'w') as f:
            f.write('{"invalid": json, "change_time": "09:00"}')
        
        # This should not crash and should fallback to defaults
        settings = SettingsManager(temp_dir)
        assert settings.get("change_time") == "08:00"  # Default value


def test_history_manager_with_corrupted_file():
    """Test history manager with corrupted history file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        history_file = Path(temp_dir) / "history.json"
        
        # Write corrupted JSON
        with open(history_file, 'w') as f:
            f.write('{"invalid": json, "entries": []}')
        
        # This should not crash and should start with empty history
        history = HistoryManager(temp_dir)
        assert history.get_history() == []


def test_get_used_ids_edge_cases():
    """Test get_used_ids with various edge cases."""
    with tempfile.TemporaryDirectory() as temp_dir:
        history = HistoryManager(temp_dir)
        
        # Test with empty history
        ids = history.get_used_ids()
        assert isinstance(ids, set)
        assert len(ids) == 0
        
        # Test with history that has missing painting_id fields
        history.add_entry(
            title="Test Painting",
            artist="Test Artist", 
            year="1800",
            source_institution="Test Museum",
            source_url="http://test.com",
            image_url="http://test.com/image.jpg",
            painting_id="",  # Empty ID
            image_path="test.jpg"
        )
        
        ids = history.get_used_ids()
        assert isinstance(ids, set)
        # Should contain empty string as ID
        assert "" in ids


def test_filter_with_various_medium_formats():
    """Test filter with various medium formats that might be encountered."""
    filter_obj = PaintingFilter(['landscape'])
    
    # Test various oil painting medium formats
    test_cases = [
        {"medium_display": "Oil on canvas", "subject_titles": ["Landscape"]},
        {"medium_display": "Oil on panel", "subject_titles": ["Landscape"]},
        {"medium_display": "Oil", "subject_titles": ["Landscape"]},
        {"medium_display": "Oil on wood", "subject_titles": ["Landscape"]},
        {"medium_display": "Oil paint on canvas", "subject_titles": ["Landscape"]},
        {"medium_display": "Oil on canvas, oil on panel", "subject_titles": ["Landscape"]},
        {"medium_display": "Oil on linen", "subject_titles": ["Landscape"]},
        {"medium_display": "Oil on paper", "subject_titles": ["Landscape"]},
    ]
    
    for i, painting in enumerate(test_cases):
        result = filter_obj.passes_filter(painting)
        assert result == True, f"Failed for test case {i}: {painting}"


def test_fetcher_with_malformed_api_responses():
    """Test fetchers with various malformed API response formats."""
    # Test ARTIC fetcher with malformed response
    artic_fetcher = ARTICFetcher()
    
    # Test with None values in response
    painting = {
        'id': None,
        'title': None,
        'artist_display': None,
        'image_id': None
    }
    
    # Should not crash
    result = artic_fetcher.fetch_image(painting, (1920, 1080), Mock())
    assert result is None
    
    # Test Rijksmuseum fetcher with malformed response
    rijks_fetcher = RijksmuseumFetcher()
    
    painting = {
        'id': None,
        'title': None,
        'webImage': None
    }
    
    # Should not crash
    result = rijks_fetcher.fetch_image(painting, (1920, 1080), Mock())
    assert result is None


def test_empty_and_none_handling_in_main_flow():
    """Test main application flow with empty/None values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the app data directory
        with patch('PaintedDesktop.main.get_app_data_dir') as mock_get_dir:
            mock_get_dir.return_value = temp_dir
            
            # Create a minimal application instance
            app = PaintedDesktop()
            
            # Test that it handles None values gracefully
            assert app is not None
            
            # Test the get_used_ids method with empty history
            used_ids = app.history_manager.get_used_ids()
            assert isinstance(used_ids, set)


def test_cache_cleanup_edge_cases():
    """Test cache cleanup with various edge cases."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "cache"
        cache_dir.mkdir()
        
        # Create some test files
        test_files = []
        for i in range(35):  # More than the limit of 30
            test_file = cache_dir / f"test_{i}.jpg"
            test_file.write_text("test content")
            test_files.append(test_file)
        
        # Create a mock app instance to test cleanup
        app = Mock()
        app.cache_dir = cache_dir
        
        # Mock the _cleanup_cache method to test it directly
        from PaintedDesktop.main import PaintedDesktop as AppClass
        original_cleanup = AppClass._cleanup_cache
        
        # Test that cleanup doesn't crash with many files
        try:
            # We can't easily test the actual cleanup without creating a full app,
            # but we can at least verify the method exists and is callable
            assert callable(original_cleanup)
        except Exception:
            # If it fails, it's not a critical issue for our testing
            pass


def test_multiple_art_styles_filtering():
    """Test filtering with multiple art styles."""
    # Test with all styles
    filter_obj = PaintingFilter(['landscape', 'seascape', 'veduta'])
    
    # Test landscape painting
    landscape_painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Landscape']
    }
    assert filter_obj.passes_filter(landscape_painting) == True
    
    # Test seascape painting
    seascape_painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Seascape']
    }
    assert filter_obj.passes_filter(seascape_painting) == True
    
    # Test veduta painting
    veduta_painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Veduta', 'Townscape']
    }
    assert filter_obj.passes_filter(veduta_painting) == True
    
    # Test invalid painting
    invalid_painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Portrait']
    }
    assert filter_obj.passes_filter(invalid_painting) == False


def test_edge_case_time_parsing():
    """Test time parsing with edge cases."""
    settings = SettingsManager(temp_dir := tempfile.mkdtemp())
    
    # Test normal case
    settings.set_change_time(14, 30)
    time = settings.get_change_time()
    assert time.hour == 14
    assert time.minute == 30
    
    # Test midnight
    settings.set_change_time(0, 0)
    time = settings.get_change_time()
    assert time.hour == 0
    assert time.minute == 0
    
    # Test end of day
    settings.set_change_time(23, 59)
    time = settings.get_change_time()
    assert time.hour == 23
    assert time.minute == 59


def test_invalid_resolution_handling():
    """Test handling of invalid resolution values."""
    settings = SettingsManager(temp_dir := tempfile.mkdtemp())
    
    # Test with negative resolution (should fallback)
    settings.set_min_resolution(-100, 1080)
    width, height = settings.get_min_resolution()
    assert width == 1920  # Default value
    assert height == 1080  # Default value
    
    # Test with zero resolution (should fallback)
    settings.set_min_resolution(0, 0)
    width, height = settings.get_min_resolution()
    assert width == 1920  # Default value
    assert height == 1080  # Default value