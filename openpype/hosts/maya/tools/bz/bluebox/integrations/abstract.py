import logging
from functools import partial
from operator import itemgetter
from types import MethodType
from getpass import getuser

from .. import api_v2
from ...placeholders import getCurrentProject


logger = logging.getLogger('bluebox')


def runScript(identifier, globals_=globals()):
    api_v2.exec_(identifier, environment='Startup', globals_=globals_, _='9b60f2f3-35ba-4398-ae77-3c8f748d02fc')


class AbstractSetup(object):
    """Run when an application is loaded."""

    APP_NAME = 'Python'

    APP_VERSION = None

    DEFERRED_FN = lambda fn: fn()

    SUPPORTS_ICONS = True

    @api_v2.ThreadedSession.wrap
    def __init__(self, collectionNames=None, skipStartupScripts=False, thread=None):
        if collectionNames is None:
            collectionNames = [
                ('Global', 'global'),
                ('Named', getCurrentProject()),
                ('Personal', getuser().lower()),
            ]

        self.thread = thread
        self.skipStartupScripts = skipStartupScripts
        self.t = {}
        self.collectionNames = collectionNames
        self._startThreads()

    def defer(self, fn):
        return fn()

    def _startThreads(self):
        logger.info('Starting threads...')

        # Support both version and no version being given
        if self.APP_VERSION is None:
            app_version_key = 'application'
            app_version_val = self.APP_NAME
        else:
            app_version_key = 'application_version'
            app_version_val='{}:{}'.format(self.APP_NAME, self.APP_VERSION)

        # Load all scripts
        # TODO: selectively load scripts
        params = {
            app_version_key: app_version_val,
            'state': 'Legacy',
            'language.application': self.APP_NAME,  # Ensure the script language is supported
        }
        if self.APP_VERSION is not None:
            # Check the version actually exists, otherwise check the closest version
            # If this isn't done then 0 scripts will be found
            app = self.thread.get('applications', self.APP_NAME, _='ae9b0441-a1e0-4c60-b030-66c2fef7e8ad').join()
            if self.APP_VERSION not in app['versions']:
                latest_version = app['versions'][0] if self.APP_VERSION < app['versions'][0] else app['versions'][-1]
                params['application_version'] = '{}:{}'.format(self.APP_NAME, latest_version)
        self.t['scripts'] = self.thread.get('scripts', _='def9198e-3e47-42f7-bb2c-315430644ad3', **params)

        # Load favourite scripts
        self.t['favScripts'] = self.thread.get('favourite-scripts', user=getuser(),
                                               script={app_version_key: app_version_val, 'state': 'Enabled'},
                                               _='0169d42a-a4d4-4ed1-a390-1252c464f58e')

        # Load startup scripts
        if not self.skipStartupScripts:
            self.t['startupScripts'] = self.thread.get('startup-scripts', application=self.APP_NAME, user=getuser(),
                                                       project=getCurrentProject(), script=dict(state='Legacy'),
                                                       _='c2f06e0a-6583-44f4-968b-4fdf53248afc')

        # Load hotkeys
        params = {
            'user': getuser(),
            'application': self.APP_NAME,
            'script.state': 'Legacy',
        }
        self.t['hotkeys'] = self.thread.get('hotkeys', _='6957e27d-3cc5-46b6-8053-4ca25d225157', **params)

        collectionNames = ','.join(name for type, name in self.collectionNames)
        self.t['collections'] = self.thread.get('collections', _='6cf2d7da-1f7b-49ac-9349-f853e0c8f61d',
                                                names=collectionNames)
        self.t['categories'] = self.thread.get('categories', _='3cf11b2a-a5eb-4f03-b72b-2ead5bffe71a',
                                               state='Enabled', collections=dict(names=collectionNames))

        # Load icons
        if self.SUPPORTS_ICONS:
            params1 = {
                'script': {
                    app_version_key: app_version_val,
                    'collection.names': collectionNames,
                },
                'collections.names': collectionNames,
                'category.collections.names': collectionNames,
                'user': getuser(),
            }
            params2 = {
                'script': {
                    app_version_key: app_version_val,
                    'category.collection.names': collectionNames,
                },
            }
            self.t['icons'] = [
                self.thread.get('icons', _='7e2293ce-17f9-4b9a-8a9e-f307ee89f9d0', **params1),
                self.thread.get('icons', _='e31e55cc-42e2-4dd9-b96f-e7867695ff63', **params2),
            ]

    def getScripts(self):
        """Get the scripts."""
        scripts = self.t['scripts'].join()

        # Temporary fix until the API states are fixed
        return {k: v for k, v in scripts.items() if v['state'] in ('Legacy', 'Enabled')}

    def getFavouriteScripts(self):
        """Get the users favourite scripts."""
        return self.t['favScripts'].join()

    def getStartupScripts(self):
        """Get the users startup scripts."""
        return self.t['startupScripts'].join()

    def getIcons(self):
        """Get icons."""
        if not self.SUPPORTS_ICONS:
            raise NotImplementedError('icons')
        icons = {}
        for t in self.t['icons']:
            icons.update(t.join())
        return icons

    def getHotkeys(self):
        """Get the hotkeys."""
        return self.t['hotkeys'].join()

    def getCollections(self):
        """Get the collections in order."""
        result = self.t['collections'].join()
        collections = []
        for collectionType, collectionName in self.collectionNames:
            for collection in result.values():
                if collection['type'] == collectionType and collection['name'] == collectionName:
                    collections.append(collection)
        return collections

    def getCollectionScripts(self, collectionIdentifier):
        """Get scripts for a collection."""
        return [script for script in self.getScripts().values()
                if collectionIdentifier in script['collections']]

    def getCollectionCategories(self, collectionIdentifier):
        """Get a collection."""
        result = self.t['categories'].join()
        return {categoryIdentifier: category for categoryIdentifier, category in result.items()
                if category['collection'] == collectionIdentifier}

    def _searchCollectionCategories(self, collectionIdentifier, **kwargs):
        """Search a collection for categories matching the parameters."""
        for category in self.getCollectionCategories(collectionIdentifier).values():
            for k, v in kwargs.items():
                if category[k] != v:
                    break
            else:
                yield category

    def iterSubcategories(self, category, recursive=False):
        """Iterate through subcategories of a category.
        Setting the `recursive` flag will iterate through their
        children too.
        """
        for subcategory in self._searchCollectionCategories(category['collection'], parent=category['identifier']):
            yield subcategory
            if recursive:
                for subsubcategory in self.iterSubcategories(subcategory, recursive=True):
                    yield subsubcategory

    def findCategory(self, collectionIdentifier, *categoryNames):
        """Search for a subcategory in a collection.
        Multiple names can be used to search deeper.
        """
        parentIdentifier = None
        if not categoryNames:
            return None
        for name in categoryNames:
            for parent in self._searchCollectionCategories(collectionIdentifier, name=name, parent=parentIdentifier):
                parentIdentifier = parent['identifier']
                break
            else:
                return None
        return parent

    def buildAll(self, *args, **kwargs):
        """Run every method starting with the text "setup".
        Any arguments passed in here are sent to each method.
        """
        for name in dir(self):
            if name == 'buildAll' or not name.startswith('build'):
                continue
            fn = getattr(self, name)
            if isinstance(fn, MethodType):
                logger.info('Executing: %s', name)
                fn(*args, **kwargs)
                logger.debug('Finished executing: %s', name)

    def buildStartupScripts(self, globals_=globals(),**kwargs):
        """Load scripts on application startup."""
        if self.skipStartupScripts:
            return

        logger.info('Reading startup scripts...')
        for scriptIdentifier in map(itemgetter('script'), self.getStartupScripts()):
            fn = partial(runScript, scriptIdentifier, globals_=globals_)
            self.defer(fn)


if __name__ == '__main__':
    AbstractSetup()#.buildAll()
