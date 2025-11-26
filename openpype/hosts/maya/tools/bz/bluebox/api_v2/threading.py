from functools import wraps
from threading import Thread

from .session import Session, get_session
from .exc import ResultNotFoundError, CacheNotFoundError


class ResultNotFound(str):
    """Pass a result not found error from the thread."""


class ResultProxy(object):
    """Hold the threaded result data."""

    def __init__(self, session, index):
        self._session = session
        self._index = index

    def join(self):
        """Ensure the thread has finished and read the result."""
        self._session._threads[self._index].join()
        value = self._session._results[self._index]
        if isinstance(value, ResultNotFound):
            raise ResultNotFoundError(value[1])
        return value


class ThreadedSession(object):

    def __init__(self):
        self.session = Session()
        self._threads = []
        self._results = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if any(args):
            return False
        return True

    @classmethod
    def wrap(cls, fn):
        """Wrap a thread as part of a function."""
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'thread' not in kwargs:
                kwargs['thread'] = cls()
            return fn(*args, **kwargs)
        return wrapper

    def join(self, *args, **kwargs):
        """Wait for all the threads to finish."""
        for thread in self._threads:
            thread.join(*args, **kwargs)
        return self._results

    def _get(self, index, endpoint, *args, **kwargs):
        """Run a threaded GET command."""
        try:
            result = self.session.get(endpoint, *args, **kwargs)
        except (ResultNotFoundError, CacheNotFoundError) as e:
            result = ResultNotFound(e)
        self._results[index] = result

    def get(self, endpoint, *args, **kwargs):
        """Create a threaded GET command."""
        # Ensure a session has already started
        get_session()

        # Create a new thread
        index = len(self._threads)
        thread = Thread(target=self._get, args=(index, endpoint) + args, kwargs=kwargs)

        # Record the thread
        self._threads.append(thread)
        self._results.append(None)

        # Start the thread
        thread.start()
        return ResultProxy(self, index)
