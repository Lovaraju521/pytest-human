import pytest


def test_human_log_only_html(pytester: pytest.Pytester) -> None:
    pytester.makepyfile("""
        def test_example(human, caplog):
            human.log.info("This is an INFO log message.")
            human.log.debug("This is a DEBUG log message.")
            human.log.trace("This is a TRACE log message.")

            assert len(caplog.messages) == 0, "No logs should go to standard logging."
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--html-log-level=info")
    assert result.ret == 0


def test_human_log_to_all_expects_only_html(pytester: pytest.Pytester) -> None:
    pytester.makepyfile("""
        def test_example(human, caplog):
            human.log.info("This is an INFO log message.")
            human.log.debug("This is a DEBUG log message.")
            human.log.trace("This is a TRACE log message.")

            captured_logs = [rec.message for rec in caplog.records]
            assert ["This is an INFO log message.",
                    "This is a DEBUG log message.",
                    "This is a TRACE log message."] == captured_logs
    """)

    result = pytester.runpytest_subprocess(
        "--enable-html-log", "--log-level=trace", "--html-log-to-all"
    )
    assert result.ret == 0


def test_get_logger_log_to_html_by_default(pytester: pytest.Pytester) -> None:
    pytester.makepyfile("""
        from pytest_human.log import get_logger

        def test_example(caplog):
            log = get_logger("custom.logger")
            log.info("This is an INFO log message.")
            log.debug("This is a DEBUG log message.")
            log.trace("This is a TRACE log message.")

            captured_logs = [rec.message for rec in caplog.records]
            assert len(captured_logs) == 0
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=trace")
    assert result.ret == 0


def test_get_logger_html_only_false(pytester: pytest.Pytester) -> None:
    pytester.makepyfile("""
        from pytest_human.log import get_logger

        def test_example(caplog):
            log = get_logger("custom.logger", html_only=False)
            log.info("This is an INFO log message.")
            log.debug("This is a DEBUG log message.")
            log.trace("This is a TRACE log message.")

            captured_logs = [rec.message for rec in caplog.records]
            assert ["This is an INFO log message.",
                    "This is a DEBUG log message.",
                    "This is a TRACE log message."] == captured_logs
        """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=trace")
    assert result.ret == 0


def test_get_logger_log_to_all_expect_caplog(pytester: pytest.Pytester) -> None:
    pytester.makepyfile("""
        from pytest_human.log import get_logger

        def test_example(caplog):
            log = get_logger("custom.logger")
            log.info("This is an INFO log message.")
            log.debug("This is a DEBUG log message.")
            log.trace("This is a TRACE log message.")

            captured_logs = [rec.message for rec in caplog.records]
            assert ["This is an INFO log message.",
                    "This is a DEBUG log message.",
                    "This is a TRACE log message."] == captured_logs
    """)

    result = pytester.runpytest_subprocess(
        "--enable-html-log", "--log-level=trace", "--html-log-to-all"
    )
    assert result.ret == 0


def test_get_global_logger_always_log_to_all(pytester: pytest.Pytester) -> None:
    pytester.makepyfile("""
        from pytest_human.log import get_global_logger

        def test_example(caplog):
            log = get_global_logger("custom.logger")
            log.info("This is an INFO log message.")
            log.debug("This is a DEBUG log message.")
            log.trace("This is a TRACE log message.")

            captured_logs = [rec.message for rec in caplog.records]
            assert ["This is an INFO log message.",
                    "This is a DEBUG log message.",
                    "This is a TRACE log message."] == captured_logs
    """)

    result = pytester.runpytest_subprocess("--enable-html-log", "--log-level=trace")
    assert result.ret == 0
