"""Test configuration for pytest."""
import pytest
import os
import sys
import logging

# Add the root directory to the Python path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Disable logging for tests to keep output clean


@pytest.fixture(autouse=True)
def disable_logging():
    """Disable logging during tests."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
