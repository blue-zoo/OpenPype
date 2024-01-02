"""Interface to the web API."""

import base64
import logging
import os
import time
from functools import wraps
from getpass import getuser
from uuid import UUID

import arrow
import requests

import maya.cmds as mc

from . import exc
from .cache import MemoryCache
from .utils import build_url
from ..common import local_icon_cache
from ..constants import ICON_LIBRARY, SESSION_KEY
from ...placeholders import getCurrentProject
from ...symbol import NOT_SET


logger = logging.getLogger('bluebox')

URL = 'https://bluebox-ayon-dot-intranet-309108.nw.r.appspot.com/v1/'

CACHE = MemoryCache()

_ITEM_METADATA = dict(
    dates={
        'action-logs': ['date'],
        'applications': ['created', 'updated'],
        'categories': ['created', 'updated'],
        'collection-whitelist': ['created', 'expires'],
        'collection-blacklist': ['created', 'expires'],
        'collections': ['created', 'updated'],
        'executions': ['created'],
        'hotkeys': ['created'],
        'languages': ['created', 'updated'],
        'scripts': ['created', 'updated', 'execution_latest', 'exception_latest', 'revision_updated'],
        'tags': ['created', 'updated'],
        'users': ['created', 'updated', 'last_login', 'changelog_viewed'],
    },
)


class Session():
    """Core API methods."""

    def __init__(self, url=URL):
        self.url = url
        self.session = requests.Session()

    def __enter__(self):
        """Dummy entry method so it'll work as a context manager."""
        return self

    def __exit__(self, *args):
        """Dummy exit method so it'll work as a context manager."""
        self.session.close()
        return False

    @classmethod
    def wrap(cls, fn):
        """Wrap a session as part of a function."""
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'session' not in kwargs:
                kwargs['session'] = cls()
            return fn(*args, **kwargs)
        return wrapper

    @property
    def offline(self):
        """Determine if the API is offline."""
        return '__connection_error__' in os.environ.get(SESSION_KEY, '')

    @offline.setter
    def offline(self, offline):
        """Set a new offline state."""
        if offline:
            os.environ[SESSION_KEY] = '__connection_error__'
        elif SESSION_KEY in os.environ:
            del os.environ[SESSION_KEY]

    def get(self, endpoint, identifier=NOT_SET, timeout=20, **params):
        """Get a dict from the endpoint.

        The cache is automatic based on the endpoint and parameters.
        Purging the cache will be handled by POST/PUT/DELETE.

        A recommendation is to add a unique `_` parameter to each
        request for debugging purposes.
        """
        if not identifier and identifier is not NOT_SET:
            return None

        # Set if the cache should be ignored (if possible)
        # This may be when the live information is important
        # and it doesn't update often
        ignore_cache = params.pop('_ignore_cache', False)

        # Build URL
        request_params = _build_request_params(params.pop('_auth', True))
        url_params = dict(params)
        url = build_url(endpoint, identifier, **url_params)

        # Read cache
        # This may raise a CacheNotFoundError if the API is down
        # This indicates that the wrong value has already been cached
        output = CACHE.get(endpoint, identifier, params)

        # No local cache exists, so make an API request
        if output is None or ignore_cache:
            primary_key = None

            # Pagination of collections
            if identifier is None:
                url_params['page'] = 1
                url = build_url(endpoint, identifier, **url_params)

            output_list = []
            output_dict = {}
            while True:
                # Re-raise if query previously failed
                CACHE.check_error(endpoint, identifier, params)

                # Run query
                logger.info('GET %s...', url)
                try:
                    # If offline then completely skip the request
                    if self.offline:
                        raise requests.exceptions.RequestException('previous requests failed, marked as offline')

                    attempts = 0
                    while True:
                        response = self.session.get(self.url + url, timeout=timeout, **request_params)
                        logger.debug('Response: %s', response)

                        # If a 500 error then retry in case there's temporary downtime
                        if response.status_code == 500:
                            if attempts > 1:
                                raise exc.ResponseError(response)
                            time.sleep(2)
                            attempts += 1

                        # See below comments why this specific raise is necessary
                        elif response.status_code == 502:
                            raise exc.BadGatewayError(response)

                        else:
                            break

                # Fallback to using local cache if the API ever goes down
                # This is tested on a crashed server (bad gateway), and
                # invalid URL (requests connection error)
                except (requests.exceptions.RequestException, exc.BadGatewayError) as e:
                    logger.exception(e)

                    # In case of a bad gateway, force all GET requests to be skipped
                    # If they continue, it's likely a "please try again in 30 seconds"
                    # 500 status code will appear
                    if isinstance(e, exc.BadGatewayError):
                        self.offline = True

                    # Fallback to cache if set
                    if output is not None and ignore_cache:
                        return output

                    # Re-run this function
                    # The caching will ensure this doesn't run more than once
                    CACHE.load(endpoint, identifier, params)
                    return self.get(endpoint, identifier, **params)

                try:
                    result = _decode_response(response)

                # Remember 404 errors to prevent repeating the calls
                except exc.ResultNotFoundError:
                    logger.warning('No results found for %s(%r)', endpoint, identifier)
                    CACHE.record_error(response, endpoint, identifier, params)
                    raise

                if isinstance(result['data'], dict):
                    output = _process_item(endpoint, result['data'])
                    break

                # Handle items
                try:
                    primary_key = result['primary_key']
                except KeyError:
                    output = output_list
                    output.extend(_process_item(endpoint, item) for item in result['data'])
                else:
                    output = output_dict
                    output.update({item[primary_key]: _process_item(endpoint, item) for item in result['data']})

                # Get the next page
                try:
                    url_params['page'] = result['next_page']
                except KeyError:
                    break
                else:
                    url = build_url(endpoint, identifier, **url_params)

            # Update the cache
            if identifier is NOT_SET:
                logger.debug('Results found for %s: %d', endpoint, len(output))
            output = CACHE.set(endpoint, identifier, params, output)

        return output

    def post(self, endpoint, data, **params):
        """Post data to the endpoint.
        Each endpoint should accept `user` and `data` keys.
        """
        # Build URL
        request_params = _build_request_params(params.pop('_auth', True))
        url = build_url(endpoint, **params)

        logger.info('POST %s...', url)
        payload = dict(data=data)
        try:
            response = self.session.post(self.url + url, json=payload, **request_params)
            logger.debug('Response: %s', response)
        except requests.exceptions.RequestException as e:
            raise exc.RequestError(str(e))
        result = _decode_response(response)

        # Delete old cache / mark cache as not complete
        CACHE.purge(endpoint, result['data'], is_new=True)

        # Delete cache for any linked relationships
        for rel_endpoint, rel_identifier in result.get('relationships', {}).items():
            CACHE.purge(rel_endpoint, rel_identifier)

        return result['data']

    def put(self, endpoint, identifier, data, **params):
        """Put data to the endpoint.
        Each endpoint should accept `user` and `data` keys.
        """
        # Build URL
        request_params = _build_request_params(params.pop('_auth', True))
        url = build_url(endpoint, identifier, **params)

        logger.info('POST %s...', url)
        payload = dict(data=data)
        try:
            response = self.session.put(self.url + url, json=payload, **request_params)
            logger.debug('Response: %s', response)
        except requests.exceptions.RequestException as e:
            raise exc.RequestError(str(e))
        result = _decode_response(response)

        # Delete old cache / mark cache as not complete
        CACHE.purge(endpoint, result['data'], is_new=True)

        # Delete cache for any linked relationships
        for rel_endpoint, rel_identifier in result.get('relationships', {}).items():
            CACHE.purge(rel_endpoint, rel_identifier)

        return result['data']

    def patch(self, endpoint, identifier, data, **params):
        """Patch data in the endpoint.
        Each endpoint should accept `user` and `data` keys.
        """
        # Build URL
        request_params = _build_request_params(params.pop('_auth', True))
        url = build_url(endpoint, identifier, **params)
        logger.info('PATCH %s...', url)
        payload = dict(data=data)
        try:
            response = self.session.patch(self.url + url, json=payload, **request_params)
            logger.debug('Response: %s', response)
        except requests.exceptions.RequestException as e:
            raise exc.RequestError(str(e))
        result = _decode_response(response)

        # If the primary key was changed, then swap the cache to that
        # Otherwise just update the current cache
        if 'primary_key' in result:
            pk = result['primary_key']
            if pk in params:
                CACHE.purge(endpoint, params[pk])
            CACHE.update(endpoint, result['data'][pk], result['data'])

        # Delete cache for any linked relationships
        for rel_endpoint, rel_identifier in result.get('relationships', {}).items():
            CACHE.purge(rel_endpoint, rel_identifier)

        return _process_item(endpoint, result['data'])

    def delete(self, endpoint, identifier=None, **params):
        """Delete data from the endpoint.
        Each endpoint should accept `user` and `data` keys.
        """
        # Build URL
        request_params = _build_request_params(params.pop('_auth', True))
        url = build_url(endpoint, identifier, **params)
        logger.info('DELETE %s...', url)
        try:
            response = self.session.delete(self.url + url, **request_params)
            logger.debug('Response: %s', response)
        except requests.exceptions.RequestException as e:
            raise exc.RequestError(str(e))
        result = _decode_response(response)

        # Delete item from cache
        CACHE.purge(endpoint, identifier)

        # Delete cache for any linked relationships
        for rel_endpoint, rel_identifier in result.get('relationships', {}).items():
            CACHE.purge(rel_endpoint, rel_identifier)

        return result['data']


def _build_request_params(session_auth=True):
    """Build the parameters for each request.

    The session auth should always be enabled, unless when
    creating a new session during the first API call.
    """
    headers = {}
    if session_auth:
        application, version = get_current_application()
        token = '{}:{}:{}'.format(get_session(), application, version)
        headers['SessionKey'] = token

    user = 'bluebox'
    password = base64.b64encode(UUID('53df1c81fd4f4755adf96089ace6e514').bytes)
    return dict(headers=headers, auth=(user, password))


def _decode_response(response):
    """Get the data from a response, or raise an error."""
    exc.check_response(response)

    result = {}
    result.setdefault('data', None)

    # Ignore 204 No Content
    if response.status_code != 204:
        try:
            result.update(response.json())

        except ValueError:
            logger.error('Unable to decode: %s', response.content)
            raise RuntimeError('unable to decode response')

    return result


def _process_item(endpoint, item):
    """Convert the data types of an item retrieved from the endpoint.
    This is run on every item.
    """
    # Convert date columns
    if endpoint in _ITEM_METADATA['dates']:
        for key in _ITEM_METADATA['dates'][endpoint]:
            if item[key] is not None:
                item[key] = arrow.get(item[key])

    # Get the local icon path
    if endpoint == 'icons':
        item['path'] = local_icon_cache(os.path.join(ICON_LIBRARY, item['filename']))

    # Generate keyboard shortcut string
    if endpoint == 'hotkeys':
        parts = []
        if item['ctrl']:
            parts.append('CTRL')
        if item['shift']:
            parts.append('SHIFT')
        if item['alt']:
            parts.append('ALT')
        parts.append(chr(item['key']).upper())
        item['format'] = '+'.join(parts)
    return item


@Session.wrap
def get_current_application(session=None):
    """Get the current application and version."""
    application = session.get('applications', 'Maya', _auth=False)
    version = int(mc.about(version=True).split('.')[0])
    return application['name'], version


@Session.wrap
def get_session(session=None):
    """Get or create a session for the current application instance."""
    application, version = get_current_application()

    if session.offline:
        return None

    # Attempt to get the current session
    if SESSION_KEY in os.environ:
        for key in os.environ[SESSION_KEY].split(os.pathsep):
            try:
                session.get('sessions', key, application=application, version=version, _auth=False)
            except exc.ResultNotFoundError:
                pass
            else:
                return key

    # Create a new session
    payload = dict(user=getuser(), application=application, version=version, project=getCurrentProject())
    try:
        session_key = session.post('sessions', payload, _auth=False)
    except (requests.exceptions.RequestException, exc.BadGatewayError):
        session.offline = True
        return None

    # Add to environment
    if SESSION_KEY in os.environ:
        new_keys = os.environ[SESSION_KEY].split(os.pathsep) + [str(session_key)]
        os.environ[SESSION_KEY] = os.pathsep.join(new_keys[-8:])  # Prevent it getting too long
    else:
        os.environ[SESSION_KEY] = str(session_key)

    # Mark in cache so further requests not required
    CACHE.set('sessions', session_key, {}, {})
    return session_key
