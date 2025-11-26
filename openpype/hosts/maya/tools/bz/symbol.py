"""Symbols are primitive data types which have a human readable form.

Example:
    >>> NOT_SET = Symbol('NOT_SET')

    >>> def func(val=NOT_SET):
    ...     if val is NOT_SET:
    ...         raise ValueError('no input')
    ...     return val

    >>> func(4)
    4
    >>> func(None)
    >>> func()
    Traceback (most recent call last):
    ValueError: no input

Source: https://bitbucket.org/ftrack/ftrack-python-api/src/master/source/ftrack_api/symbol.py
"""


class Symbol(object):
    """A constant symbol.

    >>> SYM_FALSE = Symbol('SYM_FALSE', value=False)
    >>> SYM_TRUE = Symbol('SYM_TRUE', value=True)

    >>> bool(SYM_FALSE)
    False
    >>> bool(SYM_TRUE)
    True
    >>> SYM_FALSE == 'SYM_FALSE'
    False
    >>> SYM_FALSE == Symbol('SYM_FALSE')
    False
    >>> str(SYM_FALSE) == 'SYM_FALSE'
    True
    """

    def __init__(self, name, value=True):
        """Initialise symbol.

        Parameters:
            name (str): Unique name of the symbol.
            value (bool): Used for nonzero testing.
        """
        self.name = name
        self.value = value

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.name)

    def __bool__(self):
        return bool(self.value)
    __nonzero__ = __bool__  # Python 2 fix


NOT_SET = Symbol('NOT_SET', False)

MULTIPLE_VALUES = Symbol('MULTIPLE_VALUES', True)

NOT_APPLICABLE = Symbol('N/A', False)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
