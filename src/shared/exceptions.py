class BaseException(Exception):
    pass


class RateLimitException(BaseException):
    def __init__(self, retry_after=5):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")
