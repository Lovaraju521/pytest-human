import enum
import logging
from pathlib import Path

import pytest


class HtmlLogLocationOption(enum.Enum):
    SESSION_DIR = "session"
    """
    Store all test logs in a logs directory inside the session temporary directory.
    """

    TEST_DIR = "test"
    """
    Store each test log in a separate temporary directory for the test.
    """

    CUSTOM_DIR = "custom"
    """
    Store all test logs in a user-specified directory. The directory is specified via the
    --html-log-dir command line option.
    """

    def __str__(self) -> str:
        return self.value


def validate_dir_flags(config: pytest.Config) -> None:
    custom_dir: Path = config.option.html_custom_dir
    log_dir = config.option.html_log_dir

    if log_dir == HtmlLogLocationOption.CUSTOM_DIR and custom_dir is None:
        raise pytest.UsageError(
            "The --html-custom-dir argument is required when --html-log-dir custom is specified."
        )

    if log_dir != HtmlLogLocationOption.CUSTOM_DIR and custom_dir is not None:
        raise pytest.UsageError(
            "The --html-custom-dir argument can only be used when --html-log-dir custom is specified."
        )

    if log_dir == HtmlLogLocationOption.CUSTOM_DIR:
        if not custom_dir.exists() or not custom_dir.is_dir():
            raise pytest.UsageError(
                f"The specified custom HTML log directory '{custom_dir}' does not exist or is not a directory."
            )


def validate_flags(config: pytest.Config) -> None:
    validate_dir_flags(config)


def register_flags(parser: pytest.Parser) -> None:
    group = parser.getgroup("terminal reporting")
    group.addoption(
        "--enable-html-log",
        action="store_true",
        default=False,
        help="enable HTML nested test report.",
    )
    group.addoption(
        "--html-log-dir",
        type=HtmlLogLocationOption,
        choices=HtmlLogLocationOption,
        default=HtmlLogLocationOption.SESSION_DIR,
        help="""
        Directory to store HTML test logs. Test scoped will be stored in the test temporary directory,
        while session scoped will be stored in the session temporary directory.
        """,
    )
    group.addoption(
        "--html-custom-dir",
        type=Path,
        help="Custom directory to store HTML test logs, need to specify `--html-log-dir custom`.",
    )
