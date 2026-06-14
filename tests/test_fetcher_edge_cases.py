"""Extended tests for fetcher module to identify edge cases and bugs."""

import pytest
from unittest.mock import Mock, patch
from PaintedDesktop.fetcher import ARTICFetcher, RijksmuseumFetcher
import requests


def test_artic_fetcher_empty_response():
    """Test ARTIC fetcher with empty response."""
    fetcher = ARTICFetcher()
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {'data': []}
        mock_post.return_value.status_code = 200
        result = fetcher.search('landscape', 10)
        assert result == []


def test_artic_fetcher_network_error():
    """Test ARTIC fetcher with network error."""
    fetcher = ARTICFetcher()
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        result = fetcher.search('landscape', 10)
        assert result == []


def test_artic_fetcher_invalid_json():
    """Test ARTIC fetcher with invalid JSON response."""
    fetcher = ARTICFetcher()
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value.status_code = 200
        result = fetcher.search('landscape', 10)
        assert result == []


def test_artic_fetcher_missing_image_id():
    """Test ARTIC fetcher with painting missing image_id."""
    fetcher = ARTICFetcher()
    painting = {
        'id': 123,
        'title': 'Test Painting',
        'artist_display': 'Test Artist'
        # No image_id field
    }
    result = fetcher.fetch_image(painting, (1920, 1080), Mock())
    assert result is None


def test_artic_fetcher_invalid_image_url():
    """Test ARTIC fetcher with invalid image URL."""
    fetcher = ARTICFetcher()
    painting = {
        'id': 123,
        'title': 'Test Painting',
        'artist_display': 'Test Artist',
        'image_id': 'test_image_id'
    }
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Invalid URL")
        result = fetcher.fetch_image(painting, (1920, 1080), Mock())
        assert result is None


def test_rijksmuseum_fetcher_empty_response():
    """Test Rijksmuseum fetcher with empty response."""
    fetcher = RijksmuseumFetcher()
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {'artObjects': []}
        mock_get.return_value.status_code = 200
        result = fetcher.search('landscape', 10)
        assert result == []


def test_rijksmuseum_fetcher_network_error():
    """Test Rijksmuseum fetcher with network error."""
    fetcher = RijksmuseumFetcher()
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        result = fetcher.search('landscape', 10)
        assert result == []


def test_rijksmuseum_fetcher_invalid_json():
    """Test Rijksmuseum fetcher with invalid JSON response."""
    fetcher = RijksmuseumFetcher()
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value.status_code = 200
        result = fetcher.search('landscape', 10)
        assert result == []


def test_rijksmuseum_fetcher_no_web_image():
    """Test Rijksmuseum fetcher with painting missing webImage."""
    fetcher = RijksmuseumFetcher()
    painting = {
        'id': 'test_id',
        'title': 'Test Painting',
        'artist': 'Test Artist'
        # No webImage field
    }
    result = fetcher.fetch_image(painting, (1920, 1080), Mock())
    assert result is None


def test_rijksmuseum_fetcher_invalid_image_url():
    """Test Rijksmuseum fetcher with invalid image URL."""
    fetcher = RijksmuseumFetcher()
    painting = {
        'id': 'test_id',
        'title': 'Test Painting',
        'artist': 'Test Artist',
        'webImage': {
            'url': 'http://invalid-url.com/image.jpg'
        }
    }
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Invalid URL")
        result = fetcher.fetch_image(painting, (1920, 1080), Mock())
        assert result is None


def test_rijksmuseum_fetcher_small_image():
    """Test Rijksmuseum fetcher with image below minimum resolution."""
    fetcher = RijksmuseumFetcher()
    painting = {
        'id': 'test_id',
        'title': 'Test Painting',
        'artist': 'Test Artist',
        'webImage': {
            'url': 'http://example.com/image.jpg',
            'width': 800,
            'height': 600
        }
    }
    with patch('requests.get') as mock_get:
        mock_get.return_value.content = b'test image content'
        mock_get.return_value.status_code = 200
        result = fetcher.fetch_image(painting, (1920, 1080), Mock())
        assert result is None


def test_rijksmuseum_fetcher_invalid_resolution_fields():
    """Test Rijksmuseum fetcher with invalid resolution fields."""
    fetcher = RijksmuseumFetcher()
    painting = {
        'id': 'test_id',
        'title': 'Test Painting',
        'artist': 'Test Artist',
        'webImage': {
            'url': 'http://example.com/image.jpg',
            'width': 'invalid',
            'height': 'invalid'
        }
    }
    with patch('requests.get') as mock_get:
        mock_get.return_value.content = b'test image content'
        mock_get.return_value.status_code = 200
        result = fetcher.fetch_image(painting, (1920, 1080), Mock())
        assert result is None


def test_artic_fetcher_multiple_resolution_attempts():
    """Test ARTIC fetcher with multiple resolution attempts."""
    fetcher = ARTICFetcher()
    painting = {
        'id': 123,
        'title': 'Test Painting',
        'artist_display': 'Test Artist',
        'image_id': 'test_image_id'
    }
    with patch('requests.get') as mock_get:
        # Mock multiple failed attempts
        mock_get.side_effect = [
            Mock(content=b'test image content', status_code=200),
            Mock(content=b'test image content', status_code=200),
            Mock(content=b'test image content', status_code=200)
        ]
        # Mock PIL to return small image
        with patch('PIL.Image.open') as mock_image:
            mock_image.return_value.size = (800, 600)  # Smaller than required
            result = fetcher.fetch_image(painting, (1920, 1080), Mock())
            # Should still return None because it can't find a large enough image
            assert result is None