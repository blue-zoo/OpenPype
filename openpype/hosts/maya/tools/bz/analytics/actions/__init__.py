import inspect
import json
from functools import wraps

from .. import log_action


def log_function_call(func):
    """Log a function and the arguments given to it."""
    def encode(value):
        """Encode a value to be safe for serialisation."""
        if isinstance(value, dict):
            return {encode(k): encode(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple, set)):
            return [encode(v) for v in value]
        elif isinstance(value, (str, int, float, type(u''), bool)):
            return value
        return repr(value)

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func_name = func.__name__
        except AttributeError:
            return func(*args, **kwargs)

        try:
            namespace = inspect.stack()[-1][0].f_globals['__name__']
            name = namespace + '.' + func_name
        except (KeyError, IndexError, AttributeError):
            name = func_name

        # Check length
        f = lambda val: val if len(json.dumps(val)) < 2048 else '<truncated>'
        args_repr = f(list(map(f, encode(args))))
        kwargs_repr = f({f(k): f(v) for k, v in encode(kwargs).items()})

        log_action(
            'BEFORE_FUNCTION_CALL',
            name=name,
            args=args_repr,
            kwargs=kwargs_repr,
        )

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            log_action(
                'AFTER_FUNCTION_CALL',
                name=name,
                args=args_repr,
                kwargs=kwargs_repr,
                exception=str(e),
            )
            raise
        else:
            log_action(
                'AFTER_FUNCTION_CALL',
                name=name,
                args=args_repr,
                kwargs=kwargs_repr,
            )
        return result

    return wrapper
