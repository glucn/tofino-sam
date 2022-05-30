class RetryableException(Exception):
    pass


class NotRetryableException(Exception):
    pass


class MalFormedMessageException(NotRetryableException):
    pass


class JobPostingParseError(NotRetryableException):
    pass
