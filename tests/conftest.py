import pytest
import os
import tempfile
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "PaintedDesktop"))

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for tests to use as app_data_dir."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
