class ApiError(Exception):
    pass


class RateLimitError(Exception):
    def __init__(self, message, retry_time):
        super().__init__(message)
        self.retry_time = retry_time
