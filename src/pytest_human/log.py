import functools
import inspect
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Callable, ContextManager, MutableMapping, Optional

from rich.pretty import pretty_repr

TRACE_LEVEL_NUM = logging.NOTSET + 5

_SPAN_START_TAG = "span_start"
_SPAN_END_TAG = "span_end"
_SYNTAX_HIGHLIGHT_TAG = "syntax"
_HIGHLIGHT_EXTRA = {_SYNTAX_HIGHLIGHT_TAG: True}


class TestLogger(logging.LoggerAdapter):
    """
    Custom logger class that adds a trace method, supports for spans and syntax highlighting
    """

    __test__ = False
    TRACE = TRACE_LEVEL_NUM

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger, {})

    def _log_with_highlight(
        self,
        level: int,
        message: str,
        args: tuple,
        highlight: bool = False,
        **kwargs,
    ) -> None:
        """Central method to handle the highlighting logic."""
        if self.isEnabledFor(level):
            if highlight:
                extra = kwargs.get("extra", {}) | _HIGHLIGHT_EXTRA
                kwargs["extra"] = extra

            self._log(level, message, args, **kwargs)

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:  # noqa: ANN401
        # pipethrough our custom extra fields, and prevent overwriting by class level extra
        return msg, kwargs

    def emit(self, log_level: int, message: str, *args, **kwargs) -> None:
        self._log_with_highlight(log_level, message, args, **kwargs)

    def trace(self, message: str, *args, highlight: bool = False, **kwargs) -> None:
        self._log_with_highlight(TRACE_LEVEL_NUM, message, args, highlight, **kwargs)

    def debug(self, message: str, *args, highlight: bool = False, **kwargs) -> None:
        self._log_with_highlight(logging.DEBUG, message, args, highlight, **kwargs)

    def info(self, message: str, *args, highlight: bool = False, **kwargs) -> None:
        self._log_with_highlight(logging.INFO, message, args, highlight, **kwargs)

    def warning(self, message: str, *args, highlight: bool = False, **kwargs) -> None:
        self._log_with_highlight(logging.WARNING, message, args, highlight, **kwargs)

    def error(self, message: str, *args, highlight: bool = False, **kwargs) -> None:
        self._log_with_highlight(logging.ERROR, message, args, highlight, **kwargs)

    def critical(self, message: str, *args, highlight: bool = False, **kwargs) -> None:
        self._log_with_highlight(logging.CRITICAL, message, args, highlight, **kwargs)

    @contextmanager
    def span(
        self,
        log_level: int,
        message: str,
        highlight: bool = False,
        extra: Optional[dict[str, Any]] = None,
        *args,
        **kwargs,
    ) -> Iterator[None]:
        """
        Creates a nested logging span.
        This is a logging message that can be expanded/collapsed in the HTML log viewer.
        """
        extra = extra or {}
        if highlight:
            extra |= _HIGHLIGHT_EXTRA
        try:
            self.log(
                log_level,
                message,
                *args,
                **kwargs,
                extra=extra | {_SPAN_START_TAG: True},
            )
            yield
        finally:
            self.log(log_level, "", extra={_SPAN_END_TAG: True})

    def span_trace(self, message: str, *args, **kwargs) -> ContextManager[None]:
        """
        Creates a nested TRACE logging span.
        This is a logging message that can be expanded/collapsed in the HTML log viewer.

        Using TRACE level requires enabling TRACE logging via TestLogger.setup_trace_logging()
        """
        return self.span(TRACE_LEVEL_NUM, message, *args, **kwargs)

    def span_debug(self, message: str, *args, **kwargs) -> ContextManager[None]:
        """
        Creates a nested DEBUG logging span.
        This is a logging message that can be expanded/collapsed in the HTML log viewer.
        """
        return self.span(logging.DEBUG, message, *args, **kwargs)

    def span_info(self, message: str, *args, **kwargs) -> ContextManager[None]:
        """
        Creates a nested INFO logging span.
        This is a logging message that can be expanded/collapsed in the HTML log viewer.
        """
        return self.span(logging.INFO, message, *args, **kwargs)

    def span_warning(self, message: str, *args, **kwargs) -> ContextManager[None]:
        """
        Creates a nested INFO logging span.
        This is a logging message that can be expanded/collapsed in the HTML log viewer.
        """
        return self.span(logging.WARNING, message, *args, **kwargs)

    def span_error(self, message: str, *args, **kwargs) -> ContextManager[None]:
        """
        Creates a nested ERROR logging span.
        This is a logging message that can be expanded/collapsed in the HTML log viewer.
        """
        return self.span(logging.ERROR, message, *args, **kwargs)

    def span_critical(self, message: str, *args, **kwargs) -> ContextManager[None]:
        """
        Creates a nested CRITICAL logging span.
        This is a logging message that can be expanded/collapsed in the HTML log viewer.
        """
        return self.span(logging.CRITICAL, message, *args, **kwargs)

    @classmethod
    def setup_trace_logging(cls) -> None:
        """
        Run this early enough to setup the TRACE log level
        For example the pytest_cmdline_main hook under the top-level conftest.py
        """
        logging.TRACE = TRACE_LEVEL_NUM  # pyright: ignore[reportAttributeAccessIssue]: monkey patching
        logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")


class SpanEndFilter(logging.Filter):
    """A logging filter that blocks log records marking the end of a span."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not getattr(record, _SPAN_END_TAG, False)


def get_class_name(func: Callable) -> str:
    """
    Gets a class name from a method or function.
    """
    if hasattr(func, "__self__"):
        return func.__self__.__class__.__name__

    func_components = func.__qualname__.split(".")

    if len(func_components) == 1:
        # last module component is actually interesting
        return func.__module__.split(".")[-1]

    # First qualifier is class
    return func_components[0]


def _format_call_string(func: Callable, args: tuple, kwargs: dict) -> str:
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    class_name = get_class_name(func)
    func_name = func.__name__
    params = []
    for name, value in bound_args.arguments.items():
        if name == "self":
            continue
        params.append(f"{name}={value!r}")

    return f"{class_name}.{func_name}({', '.join(params)})"


def log_method_call(*, log_level: int = logging.INFO, suppress_return: bool = False):  # noqa: ANN201
    """
    Decorator to log method calls with parameters and return values.

    :param log_level: The log level that will be used for logging. Errors are always logged with ERROR level.
    :param suppress_return: If True, do not log the return value.
    """

    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):  # noqa: ANN202
                if not logger.isEnabledFor(log_level):
                    return await func(*args, **kwargs)

                func_str = _format_call_string(func, args, kwargs)
                with logger.span(log_level, f"async {func_str}", highlight=True):
                    try:
                        result = await func(*args, **kwargs)
                        result_str = (
                            "<suppressed>" if suppress_return else pretty_repr(result)
                        )
                        logger.debug(
                            f"async {func_str} -> {result_str}", highlight=True
                        )
                        return result
                    except Exception as e:
                        logger.error(f"async {func_str} !-> {e!r}", highlight=True)
                        raise e

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):  # noqa: ANN202
                if not logger.isEnabledFor(log_level):
                    return func(*args, **kwargs)

                func_str = _format_call_string(func, args, kwargs)
                with logger.span(log_level, func_str, highlight=True):
                    try:
                        result = func(*args, **kwargs)
                        result_str = (
                            "<suppressed>" if suppress_return else pretty_repr(result)
                        )
                        logger.debug(f"{func_str} -> {result_str}", highlight=True)
                        return result
                    except Exception as e:
                        logger.error(f"{func_str} !-> {e!r}", highlight=True)
                        raise e

            return sync_wrapper

    return decorator


def get_logger(name: str) -> TestLogger:
    """
    Returns a logger customized for our tests

    :param name: Name of the logger, typically __name__
    """
    logger = logging.getLogger(name)
    return TestLogger(logger)
