"""Fixtures provided by pytest-human."""

import pytest

from pytest_human.human import Human
from pytest_human.log import TestLogger, get_logger


def _get_test_log(request: pytest.FixtureRequest) -> TestLogger:
    test_name = request.node.name
    return get_logger(test_name)


@pytest.fixture
def human(request: pytest.FixtureRequest) -> Human:
    """Provide a human logger to the test."""
    return Human(request.node)


@pytest.fixture
def test_log(request: pytest.FixtureRequest) -> TestLogger:
    """Provides a test logger.

    This is equivalent to human.log or get_logger(request.node.name).
    """
    return _get_test_log(request)
