"""General functions for the API to use."""

def build_url(*args, **kwargs):
    """Build a URL for the endpoint with parameters.
    Does not include the base URL.

    >>> build_url('scripts', author='peterh')
    'scripts?author=peterh'
    """
    url = '/'.join(filter(bool, args)).lstrip('/')
    fragment = kwargs.pop('_', None)
    if kwargs:
        params = sorted(flatten_dict(kwargs).items())
        url += '?' + '&'.join('{}={}'.format(k, 'null' if v is None else v) for k, v in params)
    if fragment:
        url += '#' + fragment
    return url


def flatten_dict(d, parent_key=None, sep='.'):
    """Flatten a dictionary to combine keys together."""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key is not None else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
