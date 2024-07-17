"""Track events in a database."""

import logging
import os
import sys
import time
from functools import wraps

import requests

from . import utils


logger = logging.getLogger(__name__)

URL = 'https://analytics-dot-intranet-309108.nw.r.appspot.com/v1'

TIMEOUT = 5

TIMEOUT_SESSION_START = 20  # Give App Engine a chance to launch

TIMEOUTS = []


def request_with_timeout(req, timeout, *args, **kwargs):
    """Wrap the request to handle timeouts.
    If more than 3 timeouts within 60 seconds, then stop analytics.

    Parameters:
        req (callable): The function such as `requests.get`.
    """
    # Stop here if too many timeouts occurred
    if TIMEOUTS and TIMEOUTS[0] is None:
        return None

    kwargs['timeout'] = timeout
    try:
        return req(*args, **kwargs)
    except (ZeroDivisionError, requests.exceptions.RequestException) as e:
        logger.warning(e)
        TIMEOUTS.append(time.time())
        if len(TIMEOUTS) >= 4:
            TIMEOUTS[:] = TIMEOUTS[-4:]
            if TIMEOUTS[0] > TIMEOUTS[-1] - 60:
                TIMEOUTS[0] = None
        return None


def validate_session(func):
    """Decorator to make sure the analytics session is valid."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Cancel if session doesn't exist
        if 'BZ_ANALYTICS_SID' not in os.environ:
            return None

        # Check existing session
        try:
            session_id, session_hash, computer_id = os.environ['BZ_ANALYTICS_SID'].split(os.pathsep)
        except ValueError:
            return None
        if not session_id or not session_hash or computer_id != utils.generate_computer_uid():
            return None

        return func(*args, **kwargs)
    return wrapper


def start_session():
    """Setup a new session and remember the ID."""
    # If a session exists, mark it as exited
    # This ideally shouldn't trigger
    _log_action('PIPELINE_EXIT', {})

    # Generate the request data
    url = URL + '/sessions'
    payload = dict(
        data=dict(
            username=utils.get_username(),
            computer_name=utils.get_computer_name(),
            gpu_name=utils.get_gpu_name(),
            gpu_driver=utils.get_gpu_driver(),
            sys_executable=utils.normpath(sys.executable),
            domain=utils.get_domain(),
            os_name=os.name,
            sys_platform=sys.platform,
            sys_name=utils.get_system_name(),
        ),
    )
    tz_info = utils.get_zoneinfo()
    if tz_info is not None:
        payload['data']['tz_info'] = tz_info
    tz_offset = utils.get_timezone_offset()
    if tz_offset is not None:
        payload['data']['tz_offset'] = tz_offset

    # Send the request
    response = request_with_timeout(requests.post, TIMEOUT_SESSION_START, url, json=payload)
    if not response:
        if response is not None:
            try:
                for error in response.json()['errors']:
                    logger.warning(error)
            except ValueError:
                logger.warning(response.content)
        os.environ['BZ_ANALYTICS_SID'] = ''
        return None

    # Parse the response
    response = response.json()['data']
    os.environ['BZ_ANALYTICS_SID'] = os.pathsep.join(map(str, (
        response['id'], response['hash'], utils.generate_computer_uid()
    )))

    _log_action(
        'PIPELINE_LAUNCH',
        dict(
            application='Maya',
            project_id=int(os.environ['AVALON_PROJECT'].split('_')[0]),
            project_name=os.environ['AVALON_PROJECT'],
            ayon=True,
        ),
    )
    return response['id'], response['hash']


@validate_session
def _log_action(action, data):
    """Log an action to the current analytics session."""
    # Generate the request data
    session_id, session_hash, computer_id = os.environ['BZ_ANALYTICS_SID'].split(os.pathsep)
    url = URL + '/actions'
    payload = dict(
        action=action,
        data=data,
        session_id=session_id,
        session_hash=session_hash,
    )

    # Send the request
    response = request_with_timeout(requests.post, TIMEOUT, url, json=payload)
    if not response:
        if response is not None:
            try:
                for error in response.json()['errors']:
                    logger.warning(error)
            except ValueError:
                logger.warning(response.content)
        return None

    # Parse the response
    response = response.json()['data']
    return response['id'], response['hash']


def log_action(action, **data):
    """Log an action to the current analytics session."""
    return _log_action(action, data)


@validate_session
def update_session_activity():
    """Update the current session to set latest activity to now."""
    # Generate the request data
    session_id, session_hash, computer_id = os.environ['BZ_ANALYTICS_SID'].split(os.pathsep)
    url = URL + '/sessions/{}'.format(session_id)
    payload = dict(session_hash=session_hash)

    # Send the request
    response = request_with_timeout(requests.patch, TIMEOUT, url, json=payload)
    try:
        response = requests.patch(url, json=payload, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        return False
    return bool(response)


@validate_session
def _add_action_data(action_id, action_hash, data):
    """Add data to an existing action in the current session."""
    # Generate the request data
    session_id, session_hash, computer_id = os.environ['BZ_ANALYTICS_SID'].split(os.pathsep)
    url = URL + '/actions/{}'.format(action_id)
    payload = dict(
        data=data,
        session_id=session_id,
        session_hash=session_hash,
        action_hash=action_hash,
    )

    # Send the request
    response = request_with_timeout(requests.post, TIMEOUT, url, json=payload)
    if not response:
        try:
            for error in response.json()['errors']:
                logger.warning(error)
        except ValueError:
            logger.warning(response.content)
    return bool(response)


def add_action_data(action, **data):
    """Add data to an existing action in the current session."""
    action_id, action_hash = action
    return _add_action_data(action_id, action_hash, data)
