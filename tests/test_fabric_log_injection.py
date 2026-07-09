"""Regression tests for single-line logging of user-derived Fabric fields."""

import logging

from torment_service.fabric import _safe_log_value


def test_safe_log_value_escapes_lf():
    sanitized = _safe_log_value("ok\nFAKE ERROR")

    assert "\n" not in sanitized
    assert sanitized == "ok\\nFAKE ERROR"


def test_safe_log_value_escapes_crlf():
    sanitized = _safe_log_value("ok\r\nFAKE ERROR")

    assert "\r" not in sanitized
    assert "\n" not in sanitized
    assert sanitized == "ok\\r\\nFAKE ERROR"


def test_sanitized_value_logs_as_single_record_message(caplog):
    logger = logging.getLogger("torment.fabric")

    with caplog.at_level(logging.INFO, logger="torment.fabric"):
        logger.info("field=%s", _safe_log_value("ok\r\nFAKE ERROR"))

    assert len(caplog.records) == 1
    assert caplog.records[0].message == "field=ok\\r\\nFAKE ERROR"
    assert "\r" not in caplog.records[0].message
    assert "\n" not in caplog.records[0].message
