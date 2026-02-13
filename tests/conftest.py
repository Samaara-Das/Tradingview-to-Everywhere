"""pytest configuration and fixtures for TTE tests."""

import os
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_yaml_file():
    """Create a temporary YAML file for testing config loading."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as temp_file:
        yield Path(temp_file.name)
    # Cleanup
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing trim_file()."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as temp_file:
        yield Path(temp_file.name)
    # Cleanup
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass
