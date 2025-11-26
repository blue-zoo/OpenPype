"""Constants to be used throughout Bluebox."""

import os


ICON_LIBRARY = 'R:/Global_Libraries/Icons_Library/Bluebox'

ICON_CACHE = os.path.expandvars('%PROGRAMDATA%/Blue-Zoo/cache/bluebox/icons')

CACHE_TIMEOUT = 300

SESSION_KEY = 'BLUEBOX_SESSION_IDENTIFIER'

DEFAULT_COLLECTION_NAME = 'Global'  # Set the name of the default global collection

DEFAULT_LANGUAGE_NAME = 'Unknown'  # Set the name for when script language is None
