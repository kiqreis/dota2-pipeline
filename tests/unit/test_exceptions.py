from src.shared.exceptions import RateLimitException


def test_when_no_passed_retry_after_then_default_is_5():
    ex = RateLimitException()

    assert ex.retry_after == 5
    assert "5 seconds" in str(ex)
