from __future__ import annotations

import inspect
import logging
import re
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from typing import Optional

import pytest
from _pytest.nodes import Node
from rich.pretty import pretty_repr

from pytest_human._flags import HtmlLogLocationOption
from pytest_human.html_report import HtmlFileHandler
from pytest_human.log import SpanEndFilter, TestLogger, get_logger


class HtmlLogPlugin:
    """Pytest plugin to create HTML log files for each test."""

    HTML_LOG_PLUGIN_NAME = "html-log-plugin"
    log_location_key = pytest.StashKey[HtmlLogLocationOption]()
    log_path_key = pytest.StashKey[Path]()
    html_log_handler_key = pytest.StashKey[HtmlFileHandler]()

    def __init__(self) -> None:
        self.test_tmp_path = None

    @classmethod
    def register(cls, config: pytest.Config) -> HtmlLogPlugin:
        html_logger_plugin = HtmlLogPlugin()
        config.pluginmanager.register(
            html_logger_plugin, HtmlLogPlugin.HTML_LOG_PLUGIN_NAME
        )
        return html_logger_plugin

    @classmethod
    def unregister(cls, config: pytest.Config) -> None:
        html_logger_plugin = config.pluginmanager.get_plugin(
            HtmlLogPlugin.HTML_LOG_PLUGIN_NAME
        )
        if html_logger_plugin:
            config.pluginmanager.unregister(html_logger_plugin)

    @staticmethod
    def _get_test_logger(item: pytest.Item) -> TestLogger:
        return get_logger(item.name)

    @staticmethod
    def get_session_scoped_logs_dir(item: pytest.Item) -> Path:
        """Get the session-scoped logs directory."""
        path = item.session.config._tmp_path_factory.getbasetemp() / "session_logs"  # type: ignore # noqa: SLF001
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def session_scoped_test_log_path(cls, item: pytest.Item) -> Path:
        """Get the session-scoped test log path."""
        logs_dir = cls.get_session_scoped_logs_dir(item)
        return cls.create_test_log_path(item, logs_dir)

    @staticmethod
    def create_test_log_path(item: pytest.Item, logs_dir: Path) -> Path:
        """Create a test log path inside the given logs directory."""
        logs_dir = logs_dir.resolve()
        safe_test_name = re.sub(r"[^\w]", "_", item.name)[:35]
        log_path = logs_dir / f"{safe_test_name}.html"
        return log_path

    def get_test_doc_string(self, item: pytest.Item) -> str | None:
        """Get the docstring of the test function, if any."""
        if test := getattr(item, "obj", None):
            return inspect.getdoc(test)

        if not item.parent:
            return ""

        # class/module level docstring
        if module := getattr(item.parent, "obj", None):
            return inspect.getdoc(module)

        return ""

    def get_log_level(self, item: pytest.Item) -> int:
        """Get the log level for the test item."""
        log_level_name = "DEBUG"

        with suppress(ValueError):
            if ini_level := item.config.getini("log_level"):
                log_level_name = ini_level

        if cli_level := item.config.getoption("log_level"):
            log_level_name = cli_level

        if html_level := item.config.getoption("html_log_level"):
            log_level_name = html_level

        level = logging.getLevelName(log_level_name.upper())
        return level

    def get_log_location(self, item: pytest.Item) -> HtmlLogLocationOption:
        """Get the log location option for the test item."""
        return item.config.getoption("html_log_dir")

    @classmethod
    def write_html_log_path(
        cls, item: pytest.Item, log_path: Path, flush: bool = False
    ) -> None:
        """Log the HTML log path to the terminal."""
        terminal: pytest.TerminalReporter | None = item.config.pluginmanager.get_plugin(
            "terminalreporter"
        )
        if terminal is None:
            return

        terminal.ensure_newline()
        terminal.write("Test ")
        terminal.write(f"{item.name}", bold=True)
        terminal.write(" HTML log at ")
        terminal.write(f"{log_path.as_uri()}", bold=True, cyan=True)
        terminal.line("")

        if flush:
            terminal.flush()

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_protocol(
        self, item: pytest.Item, nextitem: Optional[pytest.Item]
    ) -> Iterator[None]:
        root_logger = logging.getLogger()
        location = self.get_log_location(item)
        log_path = self.get_log_path(item, location)

        # Test directory logs are moved later in the test lifecycle
        if location != HtmlLogLocationOption.TEST_DIR:
            self.write_html_log_path(item, log_path, flush=True)

        item.stash[self.log_location_key] = location
        item.stash[self.log_path_key] = log_path

        level = self.get_log_level(item)

        html_handler = HtmlFileHandler(
            log_path.as_posix(),
            title=item.name,
            description=self.get_test_doc_string(item),
        )
        item.stash[self.html_log_handler_key] = html_handler
        html_handler.setLevel(level)
        root_logger.addHandler(html_handler)

        filtered_handlers = []

        for handler in root_logger.handlers:
            if handler is not html_handler:
                # Remove span end messages noise from other handlers
                handler.addFilter(SpanEndFilter())
                filtered_handlers.append(handler)

        yield

        self.test_tmp_path = None
        root_logger.removeHandler(html_handler)
        html_handler.close()

        for handler in filtered_handlers:
            handler.removeFilter(SpanEndFilter())

        log_path = item.stash[self.log_path_key]
        self.write_html_log_path(item, log_path, flush=True)

    def get_log_path(self, item: pytest.Item, location: HtmlLogLocationOption) -> Path:
        match location:
            case HtmlLogLocationOption.SESSION_DIR:
                return self.session_scoped_test_log_path(item)
            case HtmlLogLocationOption.TEST_DIR:
                # Will be transferred on test setup to the correct location
                return self.session_scoped_test_log_path(item)
            case HtmlLogLocationOption.CUSTOM_DIR:
                log_path = item.config.getoption("html_custom_dir")
                if log_path is None:
                    raise ValueError("Custom log directory not specified")

                return self.create_test_log_path(item, log_path)
            case _:
                raise NotImplementedError(
                    f"{location} log location not implemented yet"
                )

    def format_fixture_call(
        self, fixturedef: pytest.FixtureDef, request: pytest.FixtureRequest
    ) -> str:
        s = f"{fixturedef.argname}("
        arg_list = []
        for arg in fixturedef.argnames:
            if arg == "request":
                arg_list.append("request")
                continue
            result = request.getfixturevalue(arg)
            arg_list.append(f"{arg}={pretty_repr(result)}")

        s += ", ".join(arg_list)

        if fixturedef.params is not None and len(fixturedef.params) > 0:
            s += f", params={fixturedef.params}"
        s += ")"
        return s

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(
        self, fixturedef: pytest.FixtureDef, request: pytest.FixtureRequest
    ) -> Iterator[None]:
        """
        Hook to wrap all fixture functions with the logging decorator.
        """

        logger = get_logger(fixturedef.argname)
        call_str = self.format_fixture_call(fixturedef, request)
        with logger.span_debug(f"setup fixture {call_str}", highlight=True):
            result = yield
            try:
                fix_result = result.get_result()
                logger.debug(
                    f"setup fixture {fixturedef.argname}() -> {pretty_repr(fix_result)}",
                    highlight=True,
                )
            except Exception as e:
                logger.error(
                    f"setup fixture {fixturedef.argname}() !-> {pretty_repr(e)}",
                    highlight=True,
                )

    @pytest.fixture(autouse=True)
    def relocate_test_log(self, request: pytest.FixtureRequest, tmp_path: Path) -> None:
        """Fixture to relocate the test log file to the test temporary directory if needed."""
        item = request.node
        if (
            item.stash.get(self.log_location_key, None)
            != HtmlLogLocationOption.TEST_DIR
        ):
            return

        new_log_path = tmp_path / "test.html"
        self.write_html_log_path(item, new_log_path)
        logging.info(f"Relocating HTML log file to {new_log_path}")

        handler = item.stash[self.html_log_handler_key]
        handler.relocate(new_log_path)
        item.stash[self.log_path_key] = new_log_path

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: pytest.Item) -> Iterator[None]:
        """Start a unified span covering all fixture setup for this test item."""
        logger = self._get_test_logger(item)
        with logger.span_info("Test setup"):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(
        self, item: pytest.Item, nextitem: object
    ) -> Iterator[None]:
        """Start a unified span covering all fixture cleanup (teardown) for this test item."""

        logger = self._get_test_logger(item)
        with logger.span_info("Test teardown"):
            yield

    def pytest_fixture_post_finalizer(
        self, fixturedef: pytest.FixtureDef, request: pytest.FixtureRequest
    ) -> None:
        """
        Hook to log when fixture finalizer finishes call.
        """

        # This method is only called after the fixture finished.
        # We can log each cleanup fixture in its own span, but it is
        # too hacky and involved.
        # Therefore currently logging a single line for teardown.

        if fixturedef.cached_result is None:
            # fixture was already cleaned up, skipping log
            return

        logger = get_logger(fixturedef.argname)
        logger.debug(f"Tore down fixture {fixturedef.argname}()", highlight=True)

    def pytest_exception_interact(
        self,
        node: Node,
        call: pytest.CallInfo,
        report: pytest.TestReport,
    ) -> None:
        logger = get_logger(node.name)
        excinfo = call.excinfo
        if excinfo is None:
            logger.error("Failed extracting exception info")
            return

        traceback = report.longreprtext

        with logger.span_error(
            f"Exception: {excinfo.type.__name__} {excinfo.value}", highlight=True
        ):
            logger.error(f"traceback: {traceback}", highlight=True)
