import pytest
from filter import PaintingFilter

def test_filter_valid_oil_landscape():
    f = PaintingFilter(['landscape'])
    valid_painting = {
        'medium_display': 'Oil on canvas',
        'subject_titles': ['Landscape']
    }
    assert f.passes_filter(valid_painting) == True

def test_filter_invalid_medium():
    f = PaintingFilter(['landscape'])
    invalid_painting = {
        'medium_display': 'Watercolor',
        'subject_titles': ['Landscape']
    }
    assert f.passes_filter(invalid_painting) == False

def test_filter_invalid_subject():
    f = PaintingFilter(['landscape'])
    invalid_painting = {
        'medium_display': 'Oil on panel',
        'subject_titles': ['Portrait']
    }
    assert f.passes_filter(invalid_painting) == False

def test_filter_veduta():
    f = PaintingFilter(['landscape', 'veduta'])
    valid_painting = {
        'medium_display': 'Oil',
        'subject_titles': ['Townscape', 'Veduta']
    }
    assert f.passes_filter(valid_painting) == True

def test_filter_rijksmuseum_format():
    f = PaintingFilter(['seascape'])
    valid_painting = {
        'material': ['oil paint (paint)', 'canvas'],
        'type': 'painting',
        'classification_titles': ['marine']
    }
    assert f.passes_filter(valid_painting) == True
