import pytest

from src.shared.exceptions import AppBaseException, RateLimitException


def test_when_no_passed_retry_after_then_default_is_5():
    ex = RateLimitException()

    assert ex.retry_after == 5
    assert "5 seconds" in str(ex)


def test_when_is_passed_custom_retry_after_then_value_and_message_are_set():
    ex = RateLimitException(retry_after=30)

    assert ex.retry_after == 30
    assert "30 seconds" in str(ex)


def test_when_catch_as_app_base_then_succeeds():
    with pytest.raises(AppBaseException):
        raise RateLimitException()


def test_when_default_message_then_exact_string():
    ex = RateLimitException()

    assert str(ex) == "Rate limit exceeded. Retry after 5 seconds"


def test_when_custom_message_then_exact_string():
    ex = RateLimitException(retry_after=30)

    assert str(ex) == "Rate limit exceeded. Retry after 30 seconds"


def test_when_raised_then_can_be_catch():
    with pytest.raises(RateLimitException) as ex_info:
        raise RateLimitException(retry_after=10)

    assert ex_info.value.retry_after == 10
    assert str(ex_info.value) == "Rate limit exceeded. Retry after 10 seconds"
