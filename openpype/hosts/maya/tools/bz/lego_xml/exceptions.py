"""Custom exceptions."""

class UserWarningError(Exception):
    """Warn a user that something needs fixing."""

    def __init__(self, *messages):
        self.__messages = messages
        super(UserWarningError, self).__init__(', '.join(messages))

    def __iter__(self):
        return self.__messages[:].__iter__()


class UserExceptionList(list):
    """List to act as a context manager for UserWarningError."""
    def __enter__(self):
        return self

    def __exit__(self, *args):
        if any(args):
            return False
        if self:
            raise UserWarningError(*self)
