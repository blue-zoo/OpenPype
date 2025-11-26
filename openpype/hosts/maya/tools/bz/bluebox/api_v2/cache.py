"""Handle memory and disk caching for the API.

The memory cache is used constantly to optimise repeat API calls.
The disk cache will only be read if the API cannot be accessed.
"""

import errno
import logging
import json
import os
from collections import defaultdict
try:
    from collections import Mapping
except ImportError:
    from collections.abc import Mapping

import arrow

from . import exc
from .utils import build_url, flatten_dict
from ...symbol import NOT_SET


logger = logging.getLogger('bluebox')



def _generate_key(**params):
    """Generate a cache key based onfrom the parameters."""
    return tuple(v for k, v in sorted(flatten_dict(params).items()) if k[0] != '_')


def make_immutable(value):
    """Make a value immutable.
    This is very simple and may not work well with custom types.
    """
    if isinstance(value, list):
        return tuple(map(make_immutable, value))
    elif isinstance(value, dict):
        return ImmutableDict(value)
    elif isinstance(value, set):
        return frozenset(value)
    return value


class ImmutableDict(Mapping):
    """Create an immutable dict."""

    __slots__ = ['_data']

    def __init__(self, dct=None, **kwargs):
        self._data = {}
        if dct is not None:
            self._data.update({k: make_immutable(v) for k, v in dct.items()})
        self._data.update({k: make_immutable(v) for k, v in kwargs.items()})

    def __repr__(self):
        return self._data.__repr__()

    def __getitem__(self, item):
        return self._data.__getitem__(item)

    def __setitem__(self, item, value, force=False):
        if not force:
            raise TypeError('{!r} object does not support item assignment'.format(type(self).__name__))
        self._data.__setitem__(item, value)

    def __delitem__(self, item, force=False):
        if not force:
            raise TypeError('{!r} object does not support item assignment'.format(type(self).__name__))
        self._data.__delitem__(item)

    def __iter__(self):
        return self._data.__iter__()

    def __len__(self):
        return self._data.__len__()


class MemoryCache(object):
    """Local cache for the current session.

    This is meant to store the state of the API, where any request will
    update the cache. Each endpoint has separate cache for different
    query parameters. For example, GET `/scripts` is different to GET
    `/scripts?application=Maya`. If an individual item is updated, such
    as `PATCH /scripts/id`, then all cache for that endpoint will be
    updated to reflect the new data.
    """

    def __init__(self):
        self.results = defaultdict(dict)
        self.errors = defaultdict(dict)

    def clear(self):
        self.results.clear()
        self.errors.clear()

    def get(self, endpoint, identifier, params):
        """Get an item from cache cache.
        Returns None if no cache exists.

        If the API is down, this is caught elsewhere and results are
        set to `None`. If any of these results are found, then a
        `CacheNotFoundError` will be raised, as that means there is
        no remaining method to retrieve the data.
        """
        key = _generate_key(**params)
        output = None

        # If there is no identifier, then only get the full result set
        # and ignore any partial results
        if identifier is NOT_SET:
            if key in self.results[endpoint] and self.results[endpoint][key]['complete']:
                output = self.results[endpoint][key]['data']
                if output is None:
                    raise exc.CacheNotFoundError(build_url(endpoint, identifier, **params))

        # If there is an identifier, then search all parameters for it
        # They only affect what data exists, but not the data itself
        else:
            found_invalid_cache = False
            for cache in self.results[endpoint].values():
                if cache['data'] is None:
                    found_invalid_cache = True

                elif identifier in cache['data']:
                    output = cache['data'][identifier]
                    found_invalid_cache = False
                    break

            # API is down and no results can be found
            if found_invalid_cache:
                raise exc.CacheNotFoundError(build_url(endpoint, identifier, **params))

        return output

    def set(self, endpoint, identifier, params, value):
        """Set a new value for the cache.
        This is done after each GET query.

        Returns an immutable copy of the value.
        """
        key = _generate_key(**params)
        data = make_immutable(value)

        # Store the complete collection
        if identifier is NOT_SET:
            self.results[endpoint][key] = dict(data=data, complete=True)

        # Store an individual item
        else:
            if key not in self.results[endpoint]:
                self.results[endpoint][key] = dict(data=make_immutable({}), complete=False)
            self.results[endpoint][key]['data'].__setitem__(identifier, data, force=True)

        # Write to disk
        DiskCache(endpoint, key).save(self.results[endpoint][key]['data'])
        return data

    def load(self, endpoint, identifier, params):
        """Transfer an item of cache from the disk to memory.

        This is only done if the API is down, and works by loading the
        file into the local cache and marking it as complete, so that
        subsequent attempts to read the cache will succeed, even if
        it's only a partial result.

        Since this should only ever run when the parameter key has no
        cache associated with it, a `CacheNotFoundError` will be raised
        if the key already exists, since running this will always set
        the key, even if the loading itself fails. In case of failure,
        the cache value will be set to `None`, which is later detected
        and handled in `MemoryCache.get`.
        """
        key = _generate_key(**params)

        # Verify the cache has not already been loaded from the disk
        if key in self.results[endpoint]:
            # If the cache does not but should exist for the
            # identifier, it might indicate that the local
            # cache for a different parameter set has not yet
            # been loaded
            # At this point it is too late to fix
            if identifier is not NOT_SET:
                raise exc.CacheNotFoundError(build_url(endpoint, identifier, **params))

            # If this happens, the circumstances need figuring out
            raise RuntimeError('unknown cache error for {}'.format(endpoint))

        # Fetch from disk and mark as complete to prevent further requests
        self.results[endpoint][key] = dict(
            data=DiskCache(endpoint, key).load(), complete=True,
        )

    def update(self, endpoint, identifier, value):
        """Set new values for every instance of the identifier."""
        for cache_data in self.results[endpoint].values():
            cache_data['data'].__setitem__(identifier, value, force=True)

    def purge(self, endpoint, identifier=None, is_new=False):
        """Delete any cache when updating an endpoint.
        If the item is a new one, then mark all cache as incomplete.
        """
        if identifier:
            logger.debug("Deleting cache for '/%s/%s'...", endpoint, identifier)
        else:
            logger.debug("Deleting cache for '/%s'...", endpoint)

        # Delete value cache
        # If deleting (or creating) a single item,
        # then the whole batch will be marked as incomplete
        if endpoint in self.results:
            if identifier:
                for cache_data in self.results[endpoint].values():
                    # Delete existing key
                    if identifier in cache_data['data']:
                        cache_data['data'].__delitem__(identifier, force=True)

                    # If creating a new item, then all cache needs to
                    # be marked as incomplete
                    elif not is_new:
                        continue

                    # If an existing key or new item, mark as incomplete
                    cache_data['complete'] = False

            else:
                del self.results[endpoint]

        # Delete response error cache
        for _endpoint, _identifier in tuple(self.errors):
            if _endpoint != endpoint:
                continue

            if identifier is None or _identifier == identifier:
                del self.errors[(_endpoint, _identifier)]

    def record_error(self, response, endpoint, identifier, params):
        """Record a response error to check later.
        """
        self.errors[(endpoint, identifier)][build_url(endpoint, identifier, **params)] = response

    def check_error(self, endpoint, identifier, params):
        url = build_url(endpoint, identifier, **params)
        if url in self.errors[(endpoint, identifier)]:
            exc.check_response(self.errors[(endpoint, identifier)][url])


class DiskCache(json.JSONEncoder):
    """Save and load cache for if the API is ever inaccessible.
    This will copy the in-memory cache to the disk, which can be
    reloaded if the connection drops.
    """

    _ARROW_ATTR = '__arrow__'

    def __init__(self, endpoint, cache_key=None):
        self.endpoint = endpoint
        self.cache_key = cache_key
        self.path = os.path.expandvars('%LOCALAPPDATA%/Blue-Zoo/bluebox/cache/api/Maya')
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        super(DiskCache, self).__init__(indent=2)

    def default(self, o):
        """Handle encoding the data."""
        if isinstance(o, ImmutableDict):
            return dict(o)
        if isinstance(o, arrow.Arrow):
            return {self._ARROW_ATTR: o.format()}
        raise NotImplementedError(type(o).__name__)

    @property
    def filename(self):
        """Get the cache filename."""
        if not self.cache_key:
            return self.endpoint + '.json'

        # Annoyingly in Python 3 the hash is changed for each instance
        # This is a way to get a consistent hash
        cache_hash = 0
        for ch in '||'.join(map(str, self.cache_key)):
            cache_hash = (cache_hash * 281 ^ ord(ch) * 997) & 0xFFFFFFFF
        return '{}.{}.json'.format(self.endpoint, cache_hash)

    def save(self, data):
        """Save the cache."""
        with open(os.path.join(self.path, self.filename), 'w') as f:
            f.write(self.encode(data))

    def _load_hook(self, dct):
        """Intercept the loading to automatically convert some types."""
        if self._ARROW_ATTR in dct:
            return arrow.get(dct[self._ARROW_ATTR])
        return dct

    def load(self):
        """Load from the cache.
        If no cache exists, None is returned.
        """
        path = os.path.join(self.path, self.filename)
        logger.debug('Loading cached data from %s...', path)
        try:
            with open(path, 'r') as f:
                return json.load(f, object_hook=self._load_hook)

        # Ignore if the file doesn't exist
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
        # Ignore if file is corrupt
        except json.decoder.JSONDecodeError:
            pass
        return None
