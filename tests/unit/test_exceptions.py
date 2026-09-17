from src.shared.exceptions import RateLimitException


def test_when_no_passed_retry_after_then_default_is_5():
    ex = RateLimitException()

    assert ex.retry_after == 5
    assert f"{ex.retry_after} seconds" in str(ex)


def test_when_is_passed_custom_retry_after_then_value_and_message_are_set():
    ex = RateLimitException(retry_after=30)

    assert ex.retry_after == 30
    assert f"{ex.retry_after} seconds" in str(ex)
