"""
Pytest configuration and fixtures
"""

import pytest


def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--with-api-keys",
        action="store_true",
        default=False,
        help="Run tests that require API keys"
    )


@pytest.fixture
def config():
    """Fixture for test configuration"""
    return {
        "replicate_token": "test-token",
        "serpapi_key": "test-key"
    }
