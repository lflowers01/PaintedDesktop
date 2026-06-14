"""Extended tests for filter module to identify edge cases and bugs."""

import pytest
from PaintedDesktop.filter import PaintingFilter


def test_filter_empty_painting():
    """Test filter with empty painting dict."""
    f = PaintingFilter(['landscape'])
    empty_painting = {}
    assert f.passes_filter(empty_painting) == False


def test_filter_none_values():
    """Test filter with None values."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': None,
        'subject_titles': None
    }
    assert f.passes_filter(painting) == False


def test_filter_mixed_case_medium():
    """Test filter with mixed case medium display."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'OIL ON CANVAS',
        'subject_titles': ['Landscape']
    }
    assert f.passes_filter(painting) == True


def test_filter_mixed_case_subject():
    """Test filter with mixed case subject titles."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['LANDSCAPE']
    }
    assert f.passes_filter(painting) == True


def test_filter_no_medium_field():
    """Test filter when medium field is missing."""
    f = PaintingFilter(['landscape'])
    painting = {
        'subject_titles': ['Landscape']
    }
    assert f.passes_filter(painting) == False


def test_filter_no_subject_field():
    """Test filter when subject field is missing."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'Oil on canvas'
    }
    assert f.passes_filter(painting) == False


def test_filter_unrecognized_medium():
    """Test filter with unrecognized medium."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'Acrylic on canvas',
        'subject_titles': ['Landscape']
    }
    assert f.passes_filter(painting) == False


def test_filter_multiple_subjects():
    """Test filter with multiple subjects where one matches."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Portrait', 'Landscape', 'Seascape']
    }
    assert f.passes_filter(painting) == True


def test_filter_no_matching_subject():
    """Test filter with subjects that don't match allowed styles."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Portrait', 'Abstract']
    }
    assert f.passes_filter(painting) == False


def test_filter_veduta_with_multiple_subjects():
    """Test filter with veduta style."""
    f = PaintingFilter(['veduta'])
    painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Townscape', 'Veduta', 'Architecture']
    }
    assert f.passes_filter(painting) == True


def test_filter_empty_subject_list():
    """Test filter with empty subject list."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': []
    }
    assert f.passes_filter(painting) == False


def test_filter_special_characters():
    """Test filter with special characters in fields."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'Oil on canvas (18th century)',
        'subject_titles': ['Landscape - Coastal']
    }
    assert f.passes_filter(painting) == True


def test_filter_very_long_medium():
    """Test filter with very long medium description."""
    f = PaintingFilter(['landscape'])
    painting = {
        'medium_display': 'Oil on canvas, with additional text that might be in the field but not match our keywords',
        'subject_titles': ['Landscape']
    }
    assert f.passes_filter(painting) == True


def test_filter_rijksmuseum_material_field():
    """Test filter with Rijksmuseum material field format."""
    f = PaintingFilter(['seascape'])
    painting = {
        'material': ['oil paint (paint)', 'canvas', 'oil paint'],
        'type': 'painting',
        'classification_titles': ['marine']
    }
    assert f.passes_filter(painting) == True


def test_filter_rijksmuseum_no_material():
    """Test filter with Rijksmuseum painting that has no material field."""
    f = PaintingFilter(['seascape'])
    painting = {
        'type': 'painting',
        'classification_titles': ['marine']
    }
    assert f.passes_filter(painting) == False


def test_filter_invalid_art_styles():
    """Test filter with invalid art styles."""
    f = PaintingFilter([])
    painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Landscape']
    }
    assert f.passes_filter(painting) == False