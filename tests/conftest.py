"""pytest configuration and fixtures for TTE tests."""

import contextlib
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_yaml_file():
    """Create a temporary YAML file for testing config loading."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp_file:
        yield Path(temp_file.name)
    with contextlib.suppress(FileNotFoundError):
        os.unlink(temp_file.name)


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing trim_file()."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as temp_file:
        yield Path(temp_file.name)
    with contextlib.suppress(FileNotFoundError):
        os.unlink(temp_file.name)
