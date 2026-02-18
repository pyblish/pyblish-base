"""Pytest configuration and fixtures for pyblish tests."""
import pytest
from tests import lib


@pytest.fixture
def setup_and_teardown():
    """Fixture that runs setup() before test and teardown() after."""
    lib.setup()
    yield
    lib.teardown()


@pytest.fixture
def setup_empty_and_teardown():
    """Fixture that runs setup_empty() before test and teardown() after."""
    lib.setup_empty()
    yield
    lib.teardown()

