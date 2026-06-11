import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from fetcher import ARTICFetcher, RijksmuseumFetcher
from io import BytesIO
from PIL import Image

def create_mock_image(width, height):
    """Utility to create a mock Image response content."""
    img = Image.new('RGB', (width, height), color='blue')
    b = BytesIO()
    img.save(b, format='JPEG')
    return b.getvalue()

@patch('requests.get')
def test_artic_fetcher_resolution_valid(mock_get, temp_data_dir):
    """Test when the fetched image meets minimum resolution."""
    fetcher = ARTICFetcher()
    painting = {
        'id': 'abc',
        'image_id': 'def'
    }
    
    mock_resp = MagicMock()
    mock_resp.content = create_mock_image(2000, 1500)
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
    
    cache_dir = Path(temp_data_dir)
    result = fetcher.fetch_image(painting, (1920, 1080), cache_dir)
    
    assert result is not None
    assert "abc.jpg" in result
    assert Path(result).exists()

@patch('requests.get')
def test_artic_fetcher_resolution_invalid(mock_get, temp_data_dir):
    """Test when the fetched image is smaller than minimum resolution."""
    fetcher = ARTICFetcher()
    painting = {
        'id': 'abc',
        'image_id': 'def'
    }
    
    # Return a tool small image
    mock_resp = MagicMock()
    mock_resp.content = create_mock_image(1024, 768)
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
    
    cache_dir = Path(temp_data_dir)
    result = fetcher.fetch_image(painting, (1920, 1080), cache_dir)
    
    assert result is None

@patch('requests.post')
def test_artic_fetcher_search_format(mock_post):
    """Test if search payload is formatted correctly with a flat query string."""
    fetcher = ARTICFetcher()
    
    mock_resp = MagicMock()
    mock_resp.json.return_value = {'data': [{'id': '1'}]}
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp
    
    result = fetcher.search('landscape', limit=10)
    
    assert len(result) == 1
    mock_post.assert_called_once()
    kwargs = mock_post.call_args.kwargs
    payload = kwargs['json']
    assert payload['q'] == 'oil landscape'
    assert payload['limit'] == 10
