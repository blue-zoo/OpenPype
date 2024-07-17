import logging
import os
import platform
import subprocess
import time
from getpass import getuser
from hashlib import sha256

try:
    import tzlocal
    from pytz import UnknownTimeZoneError
except ImportError:
    tzlocal = None


logger = logging.getLogger(__name__)


def get_username():
    """Get the current username."""
    return getuser().lower()


def get_computer_name():
    """Get the current computer name."""
    return os.environ.get('COMPUTERNAME', '').upper()


def _get_gpu_info(get):
    """Spawn a hidden console and get wmic GPU information."""
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = 'wmic path win32_VideoController get {}'.format(get)
    raw_output = subprocess.check_output(command, startupinfo=startupinfo)  # pylint: disable=unexpected-keyword-arg
    lines = raw_output.decode('ascii', errors='ignore').splitlines()
    if lines[0].startswith(get):
        str_type = type(lines[0])
        return ', '.join(line for line in map(str_type.strip, lines[1:]) if line)
    return ''


def get_gpu_name():
    """Get the GPU name."""
    return _get_gpu_info('Name')


def get_gpu_driver():
    """Get the GPU driver version."""
    return _get_gpu_info('DriverVersion')


def get_domain():
    """Get the current domain."""
    return os.environ.get('USERDOMAIN')


def get_system_name():
    """Get the current operating system."""
    return platform.system()


def get_timezone_offset():
    """Get the current timezone offset."""
    return time.strftime('%z')


def get_zoneinfo():
    """Get the current timezone in the Olson format.
    Will return None if unavailable.
    """
    if tzlocal is None:
        return None
    try:
        return tzlocal.get_localzone().zone
    except (ValueError, UnknownTimeZoneError):
        return None


def generate_hash(value):
    """Generate a 32 bit binary hash."""
    return sha256(value.encode('utf-8')).digest()


def generate_computer_uid():
    """Get a unique ID for the computer and user."""
    data = (get_username(), get_computer_name(), get_domain())
    return sha256(str(sorted(data)).encode('utf-8')).hexdigest()


def normpath(path):
    """Ensure forward slashes are used."""
    return path.replace('\\', '/')
