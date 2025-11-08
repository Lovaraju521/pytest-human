from pathlib import Path

from _pytest.config import ExitCode
from _pytest.pytester import Pytester

from tests import utils


def test_log_location_custom_does_not_exist_expect_dir_created(
    pytester: Pytester, tmp_path: Path
) -> None:
    """Make sure that pytest creates the log file in the right location."""
    pytester.makepyfile("""
        def test_something():
            assert True
    """)

    custom_dir = tmp_path / "custom_dir"
    expected_log_path = custom_dir / "test_something.html"

    result = pytester.runpytest(
        "--enable-html-log",
        "--html-log-dir=custom",
        f"--html-custom-dir={custom_dir.as_posix()}",
    )

    assert result.ret == ExitCode.OK
    log_path = utils.find_test_log_location(result)
    assert log_path == expected_log_path
    assert log_path.is_file()


def test_log_location_custom_expect_file_created(pytester: Pytester, tmp_path: Path) -> None:
    """Make sure that pytest creates the log file in the right location."""
    pytester.makepyfile("""
        def test_something():
            assert True
    """)

    custom_dir = tmp_path / "custom_dir"
    custom_dir.mkdir()
    expected_log_path = custom_dir / "test_something.html"

    result = pytester.runpytest(
        "--enable-html-log",
        "--html-log-dir=custom",
        f"--html-custom-dir={custom_dir.as_posix()}",
    )

    assert result.ret == ExitCode.OK

    log_path = utils.find_test_log_location(result)
    assert log_path == expected_log_path
    assert log_path.is_file()


def test_log_location_test_expect_file_created(pytester: Pytester) -> None:
    """Make sure that pytest creates the log file in the right location."""
    pytester.makepyfile("""
        def test_something():
            assert True
    """)

    result = pytester.runpytest("--enable-html-log", "--html-log-dir=test")

    assert result.ret == ExitCode.OK

    log_path = utils.find_test_log_location(result)
    assert log_path.name == "test.html"
    assert log_path.is_file()


def test_log_location_session_expect_file_created(pytester: Pytester) -> None:
    """Make sure that pytest creates the log file in the right location."""
    pytester.makepyfile("""
        def test_something():
            assert True
    """)

    result = pytester.runpytest("--enable-html-log", "--html-log-dir=session")

    assert result.ret == ExitCode.OK
    log_path = utils.find_test_log_location(result)
    assert log_path.name == "test_something.html"
    assert log_path.is_file()
