import inspect
import logging
import time

from pytest_human.log import get_logger, log_call


def test_example(human):
    """This test demonstrates pytest-human logging."""
    human.info("Starting test execution")

    with human.span_info("Processing data"):
        human.debug("Loading data...")
        data = [1, 2, 3, 4, 5]
        human.info(f"Loaded {len(data)} items", highlight=True)

        with human.span_debug("Calculating sum"):
            result = sum(data)
            human.debug(f"Sum result: {result}")

    human.info("Test completed successfully")
    assert result == 15


def test_logging_methods(human):
    # Basic logging at different levels
    human.trace("Trace level message")
    human.debug("Debug level message")
    human.info("Info level message")
    human.warning("Warning level message")
    human.error("Error level message")
    human.critical("Critical level message")

    # Syntax highlighting for code
    code = """
    import numpy as np

    def bark(volume: float) -> bool:
        return volume > 0.5:
    """
    code = inspect.cleandoc(code)
    human.info(code, highlight=True)


def load_config():
    return {}


def process_data():
    pass


def test_spans(human):
    human.info("Starting complex operation")

    # Top-level span
    with human.span_info("Phase 1: Initialization"):
        human.debug("Initializing resources...")

        # Nested span
        with human.span_debug("Loading configuration"):
            human.trace("Reading config file")
            config = load_config()
            human.debug(f"Config loaded: {config}")

        human.info("Initialization complete")

    # Another top-level span
    with human.span_info("Phase 2: Processing"):
        human.debug("Processing data...")
        process_data()

    human.info("Operation completed")


@log_call()
def save_login(login):
    log = get_logger(__name__)
    log.info("a log inside save_login")
    return update_db(login)


@log_call(log_level=logging.TRACE)
def update_db(login):
    log = get_logger(__name__)
    delay_time = 2
    log.info("delaying by 2 seconds")
    time.sleep(delay_time)
    return delay_time


def test_method_tracing(human):
    delay = save_login("hello")
    assert delay == 2
