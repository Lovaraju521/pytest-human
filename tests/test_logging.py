import pytest
from playwright.sync_api import Page, expect

from tests import utils


def test_logging_log_levels_trace(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            human.log.trace("This is a TRACE log message.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=trace")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    log_lines = page.locator("tr.log-level-trace")
    expect(log_lines).to_have_count(1)
    expect(log_lines.locator("td.level-cell")).to_have_text("TRACE")
    expect(log_lines.locator("td.source-cell")).to_contain_text("test_logging_log_levels_trace")
    expect(log_lines.locator("td.msg-cell")).to_have_text("This is a TRACE log message.")


def test_logging_log_levels_debug(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            human.log.debug("This is a DEBUG log message.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=debug")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    log_lines = page.locator("tr.log-level-debug").filter(visible=True)
    expect(log_lines).to_have_count(1)
    expect(log_lines.locator("td.level-cell")).to_have_text("DEBUG")
    expect(log_lines.locator("td.source-cell")).to_contain_text("test_logging_log_levels_debug")
    expect(log_lines.locator("td.msg-cell")).to_have_text("This is a DEBUG log message.")


def test_logging_log_levels_info(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            human.log.info("This is an INFO log message.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=info")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    log_lines = page.locator("tr.log-level-info").filter(visible=True)
    expect(
        log_lines,
        "There should only be 4 info messages, our log, test setup,"
        " test cleanup and test artifacts",
    ).to_have_count(4)
    log_lines = log_lines.nth(1)
    expect(log_lines.locator("td.level-cell")).to_have_text("INFO")
    expect(log_lines.locator("td.source-cell")).to_contain_text("test_logging_log_levels_info")
    expect(log_lines.locator("td.msg-cell")).to_have_text("This is an INFO log message.")


def test_logging_log_levels_warning(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            human.log.warning("This is a WARNING log message.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--html-log-level=warning")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    log_lines = page.locator("tr.log-level-warning").filter(visible=True)
    expect(log_lines).to_have_count(1)
    expect(log_lines.locator("td.level-cell")).to_have_text("WARNING")
    expect(log_lines.locator("td.source-cell")).to_contain_text("test_logging_log_levels_warning")
    expect(log_lines.locator("td.msg-cell")).to_have_text("This is a WARNING log message.")


def test_logging_log_levels_error(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            human.log.error("This is an ERROR log message.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    log_lines = page.locator("tr.log-level-error").filter(visible=True)
    expect(log_lines).to_have_count(1)
    expect(log_lines.locator("td.level-cell")).to_have_text("ERROR")
    expect(log_lines.locator("td.source-cell")).to_contain_text("test_logging_log_levels_error")
    expect(log_lines.locator("td.msg-cell")).to_have_text("This is an ERROR log message.")


def test_logging_log_levels_critical(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            human.log.critical("This is a CRITICAL log message.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    log_lines = page.locator("tr.log-level-critical").filter(visible=True)
    expect(log_lines).to_have_count(1)
    expect(log_lines.locator("td.level-cell")).to_have_text("CRITICAL")
    expect(log_lines.locator("td.source-cell")).to_contain_text("test_logging_log_levels_critical")
    expect(log_lines.locator("td.msg-cell")).to_have_text("This is a CRITICAL log message.")


def test_logging_span_simple(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            with human.span.info("Awesome Span"):
                human.log.info("This is an INFO log message inside a span.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=info")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    span = page.get_by_role("row", name="Awesome Span")
    expect(span).to_be_visible()

    span_content = page.get_by_role("cell", name="This is an INFO log message inside a span.")
    expect(span_content).to_be_hidden()

    expand_button = span.get_by_role("button")
    expect(expand_button).to_have_text("[+]")
    expand_button.click()
    expect(expand_button).to_have_text("[–]")  # noqa: RUF001

    open_block = span.locator("xpath=following-sibling::tr[1]").first
    expect(open_block).to_contain_text("This is an INFO log message inside a span.")


def test_logging_span_simple_in_log_api(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            with human.log.span.info("Awesome Span"):
                human.log.info("This is an INFO log message inside a span.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=info")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    span = page.get_by_role("row", name="Awesome Span")
    expect(span).to_be_visible()

    span_content = page.get_by_role("cell", name="This is an INFO log message inside a span.")
    expect(span_content).to_be_hidden()

    expand_button = span.get_by_role("button")
    expect(expand_button).to_have_text("[+]")
    expand_button.click()
    expect(expand_button).to_have_text("[–]")  # noqa: RUF001

    open_block = span.locator("xpath=following-sibling::tr[1]").first
    expect(open_block).to_contain_text("This is an INFO log message inside a span.")


def test_logging_span_error_propagates(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            with human.span.info("Awesome Span"):
                with human.span.info("Nested Span"):
                    human.log.error("This is an ERROR log message inside a span.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=info")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    span = page.get_by_role("row", name="Awesome Span")
    expect(span).to_have_class("log-level-error")

    expand_button = span.get_by_role("button")
    expand_button.click()

    nested_span = page.locator('tr[id^="header"]').filter(has_text="Nested Span")
    expect(nested_span).to_have_class("log-level-error")

    expand_button = nested_span.get_by_role("button")
    expand_button.click()

    inner_log_block = nested_span.locator("xpath=following-sibling::tr[1]").first
    inner_log = inner_log_block.get_by_role("row").first
    expect(inner_log).to_contain_text("This is an ERROR log message inside a span.")
    expect(inner_log).to_have_class("log-level-error")


def test_logging_span_critical_propagates(pytester: pytest.Pytester, page: Page) -> None:
    pytester.makepyfile("""
        def test_example(human):
            with human.span.warning("Awesome Span"):
                with human.span.critical("Nested Span"):
                    human.log.error("This is an ERROR log message inside a span.")
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=info")
    html_path = utils.find_test_log_location(result)
    assert result.ret == 0

    page.goto(html_path.as_uri())
    span = page.get_by_role("row", name="Awesome Span")
    expect(span).to_have_class("log-level-critical")

    expand_button = span.get_by_role("button")
    expand_button.click()

    nested_span = page.locator('tr[id^="header"]').filter(has_text="Nested Span")
    expect(nested_span).to_have_class("log-level-critical")

    expand_button = nested_span.get_by_role("button")
    expand_button.click()

    inner_log_block = nested_span.locator("xpath=following-sibling::tr[1]").first
    inner_log = inner_log_block.get_by_role("row").first
    expect(inner_log).to_contain_text("This is an ERROR log message inside a span.")
    expect(inner_log).to_have_class("log-level-error")
