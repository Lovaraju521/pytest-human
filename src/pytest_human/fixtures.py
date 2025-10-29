import pytest

from pytest_human.log import TestLogger, get_logger


def _get_test_log(request: pytest.FixtureRequest) -> TestLogger:
    test_name = request.node.name
    return get_logger(test_name)


@pytest.fixture
def human(request: pytest.FixtureRequest) -> TestLogger:
    """Provides a human logger to the test."""
    return _get_test_log(request)


@pytest.fixture
def test_log(request: pytest.FixtureRequest) -> TestLogger:
    """An alias to the human fixture."""
    return _get_test_log(request)
