"""Functions to be used throughout Bluebox."""

__all__ = [
    'ExtendedEnum', 'EnvSet', 'cache_timeout_valid',
    'local_icon_cache', 'logger',
]

import logging
import errno
import os
import time
from shutil import copyfile

from .constants import *


logger = logging.getLogger('bluebox')


class EnvSet(set):
    """Link a set to an environment variable."""

    def __init__(self, env):
        self.env = env
        if self.env not in os.environ:
            os.environ[self.env] = ''
        super(EnvSet, self).__init__(self._read())

    def add(self, value):
        super(EnvSet, self).add(value)
        if os.environ[self.env]:
            menus = set(self._read())
        else:
            menus = set()
        menus.add(value)
        os.environ[self.env] = ';'.join(map(str, menus))

    def remove(self, value):
        super(EnvSet, self).remove(value)
        menus = set(self._read())
        menus.remove(value)
        os.environ[self.env] = ';'.join(map(str, menus))

    def _read(self):
        return filter(bool, os.environ[self.env].split(';'))


def cache_timeout_valid(cache_time, current_time=None):
    """Determine if cache is valid based on a timeout.
    This stops old data becoming stale as things are updated.
    """
    if current_time is None:
        current_time = time.time()
    return current_time - cache_time < CACHE_TIMEOUT


def local_icon_cache(path, *subfolders):
    """Copy an icon to the local cache directory."""
    if not os.path.exists(path):
        return None

    # Skip if both paths are on same drive
    source_drive = os.path.splitdrive(os.path.abspath(path))[0]
    local_drive = os.path.splitdrive(os.path.abspath(ICON_CACHE))[0]
    if source_drive == local_drive:
        return path

    # Copy locally if it doesn't already exist
    filename = os.path.normpath(path).rsplit(os.path.sep, 1)[-1]
    local_dir = os.path.join(ICON_CACHE, *subfolders)
    local_path = os.path.join(local_dir, filename)
    if not os.path.exists(local_path):
        try:
            copyfile(path, local_path)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)
            copyfile(path, local_path)
    return local_path
