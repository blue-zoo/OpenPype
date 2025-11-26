"""Custom API exceptions."""

from __future__ import absolute_import

import logging
import requests


logger = logging.getLogger('bluebox')


class GenericError(RuntimeError):
    """Base class for all errors."""


class RequestError(GenericError, requests.exceptions.RequestException):
    """Unable to connect to the URL."""


class ResponseError(GenericError):
    """Handle response errors."""

    def __init__(self, response):
        if isinstance(response, ResponseError):
            response = response.response
        self.response = response
        self.flags = set()
        super(ResponseError, self).__init__(self.message)

    @property
    def status_code(self):
        """Return the status code."""
        return self.response.status_code

    @property
    def content(self):
        """Return the error message."""
        if self.response:
            return ''
        content = self.response.content.decode('utf-8')
        try:
            return content.split('<p>')[1].split('</p>')[0]
        except IndexError:
            return content

    @property
    def message(self):
        """Return the traceback message."""
        message = 'got status code {}'.format(self.status_code)
        error = self.content
        if error:
            message += ' ({})'.format(error.lower().rstrip('.'))
        return message


class ResultNotFoundError(GenericError):
    """Error when a result isn't found."""


class BadGatewayError(ResponseError):
    """Super serious error that means the API is not working."""


def check_response(response):
    """Raise an error if the request failed."""
    if isinstance(response, Exception) or isinstance(response, type) and Exception in response.__mro__:
        raise response
    elif response:
        return
    elif response.status_code == 404:
        raise ResultNotFoundError(response.url)
    elif response.status_code == 502:
        raise BadGatewayError(response)
    raise ResponseError(response)


class CacheNotFoundError(GenericError):
    """Error if no cache for an endpoint exists.
    This is only for if the API has gone down for whatever reason.
    """
    def __init__(self, url):
        logger.error('Local cache unavailable: %s', url)
        super(CacheNotFoundError, self).__init__(url)
