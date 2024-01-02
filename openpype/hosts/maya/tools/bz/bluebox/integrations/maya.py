import logging
from collections import defaultdict
from functools import partial
from operator import itemgetter
from getpass import getuser

import maya.cmds as mc

from .abstract import AbstractSetup
from .. import api_v2
from ..common import EnvSet
from ..everything_else import multi_function
from ... import inflection


logger = logging.getLogger('bluebox')

MENU_ENV_VAR = 'BLUEBOX_MAYA_MENUS'

SHELF_PREFIX = 'BB_'

# Define an order of scripts
# Each sublist is a group, separated by an empty icon
# This must have a wildcard to define where all "other" scripts go
SHELF_ORDER = dict(
    __default__=[
        ['*'],
    ],
    Animation=[
        ['project-browser', '*'],
        [
            'tween-machine', 'atools', 'animbot', 'anim-school-picker',
            'studio-library', 'kf-pro-maya-launch', 'kf-pro-maya-send',
        ],
    ],
    Lighting=[
        ['project-browser', 'deadline-submitter', 'deadline-submitter-2', '*'],
        [
            'open-render-view', 'open-render-settings', 'open-outliner',
            'open-reference-editor', 'open-namespace-editor', 'open-spreadsheet-editor',
            'open-hypershade', 'open-lightlinking-editor', 'open-approx-editor',
            'hypershade-thumbnail-enable', 'hypershade-thumbnail-disable',
        ],
        ['select-geometry', 'mms-attribute'],
    ],
    Surfacing=[
        ['project-browser'],
        [
            'open-render-view', 'open-render-settings', 'open-outliner',
            'open-reference-editor', 'open-namespace-editor', 'open-spreadsheet-editor',
            'open-hypershade', 'open-lightlinking-editor', 'open-approx-editor',
            'hypershade-thumbnail-enable', 'hypershade-thumbnail-disable',
        ],
        [
            'surface-library', 'material-finder',
            'hv1-chr-lookdev-scene', 'hv1-prop-lookdev-scene', 'hv1-prop-lookdev-2',
            'hv1-env-int-lookdev-scene', 'hv1-env-lookdev-scene',
            'set-all-cameras-renderable', 'set-render-path', 'set-farm-path',
            'deadline-submitter', 'deadline-submitter-2',
        ],
        ['quick-attribute', 'place2dtexture-connect', 'rename'],
        ['uv-transferer', 'export-u-vs', 'import-u-vs'],
        ['select-geometry', 'refresh-instances', 'sculpt-fbx-import-export'],
        ['current-directory', 'open-texturing-directory', 'force-texture-to-wip', 'udim-stitcher'],
        ['import-selected-references', 'import-all-references'],
        [
            'delete-unknown-nodes', 'shader-ref-clean-up', 'check-color-sets',
            'camera-clean-up', 'ultimate-checklist',
        ],
        ['*'],
    ],
)

# Override labels on individual scripts if needed
SHELF_LABELS = {
    'project-browser': '',
    'deadline-submitter': 'Submit',
    'deadline-submitter-2': 'Submit',
    'open-outliner': '',
    'open-reference-editor': '',
    'open-namespace-editor': '',
    'open-spreadsheet-editor': '',
    'open-hypershade': '',
    'open-lightlinking-editor': 'LightLink',
    'open-approx-editor': 'Approx',
    'hypershade-thumbnail-enable': '',
    'hypershade-thumbnail-disable': '',
    'open-render-settings': 'Settings',
    'select-geometry': '',
    'render-assets-manager': '',
    'lighting-helper': 'Helper',
    'kf-pro-maya-send': 'MtoKP',
    'kf-pro-maya-launch': 'KPro',
    'studio-library': '',
    'anim-school-picker': '',
    'animbot': '',
    'tween-machine': '',
    'orient-keyframes': '',
    'new-camera': '',
    'animation-extraction': '',
    'make-ref-layers': '',
    'asset-definition-systems': '',
    'definition-systems': '',
    'open-graph-editor': 'graph',
    'atools': '',
}

DEFAULT_HOTKEYSET_NAME = 'Bluebox'


class MayaSetup(AbstractSetup):
    """Run when Maya is loaded."""

    APP_NAME = 'Maya'

    APP_VERSION = mc.about(version=True).split('.')[0]

    def defer(self, fn):
        mc.evalDeferred(fn, lowestPriority=True)

    def buildMenus(self, **kwargs):
        """Create Maya menus."""
        from ..everything_else import createMenu, deleteMenu, addMenuItem, addSubmenu

        def addCategory(category):
            """Create a menu for a category."""
            icon = api_v2.get_icon('categories', category['identifier'],
                                   _='c8d31b15-f6c3-4e81-9b63-f82581352689')

            with addSubmenu(category['name'], icon=icon) as subMenu:
                # Add subcategories
                for subCategory in category['subcategories']:
                    addCategory(subCategory)

                # Add scripts
                addScripts(subMenu, category['scripts'], category=category['identifier'])

        def addScripts(menu, scripts, **sKwargs):
            """Create a menu item for a script."""
            for script in sorted(scripts, key=itemgetter('name')):
                if script['state'] != 'Enabled':
                    continue

                icon = api_v2.get_icon('scripts', script['identifier'],
                                       _='0e6efb28-89d4-4988-a590-f2c8d3cf0e0a')
                command = api_v2.generate_api_command(script['identifier'], environment='Menu',
                                                      _='6f92d9e6-c74e-4433-adc9-0d1c83fc0363', **sKwargs)
                addMenuItem(menu, script['name'], clickCommand=command, icon=icon)

        logger.info('Building menu...')
        menus = EnvSet(MENU_ENV_VAR)
        scripts = self.getScripts()

        for collection in self.getCollections():
            # Delete existing menu if it exists
            for menu in tuple(menus):
                curName, curMenu = menu.split(':')
                if curName != collection['display_name']:
                    continue
                try:
                    deleteMenu(curMenu)
                except (NameError, RuntimeError):
                    pass
                else:
                    menus.remove(menu)

            # Find all scripts in collection
            collectionScripts = self.getCollectionScripts(collection['identifier'])

            # Find categories containing Maya scripts
            _allCategories = self.getCollectionCategories(collection['identifier'])
            allCategories = {k: dict(v) for k, v in _allCategories.items()}
            filteredCategories = []
            for categoryIdentifier, category in sorted(allCategories.items()):
                categoryScripts = set(category['scripts']) & set(scripts)
                if category['parent'] is None and not categoryScripts:
                    continue

                category['scripts'] = list(map(scripts.__getitem__, sorted(categoryScripts)))
                category['subcategories'] = list(map(allCategories.__getitem__, sorted(category['subcategories'])))
                filteredCategories.append(category)

            if not (collectionScripts or filteredCategories):
                continue

            # Setup menu
            menu = createMenu(collection['display_name'])
            menus.add(collection['display_name'] + ':' + menu)

            # Make sure icons are preloaded
            self.getIcons()

            # Add top level categories
            for category in filteredCategories:
                if category['parent'] is None:
                    addCategory(category)

            # Add generic collection script
            addScripts(menu, collectionScripts, collection=collection['identifier'])

    def buildShelves(self, **kwargs):
        """Create Maya shelves."""
        from ..everything_else import listShelves, createShelf, createButton, deleteShelf

        logger.info('Cleaning old shelves...')
        for shelf in listShelves():
            if shelf.startswith(SHELF_PREFIX):
                deleteShelf(shelf)

        logger.info('Building shelves...')
        scripts = self.getScripts()

        # shelfScripts[(shelfID, categoryName)][scriptIdentifier] = categoryIdentifier
        shelfScripts = defaultdict(lambda: defaultdict(list))

        # Read all the shelves
        for collection in reversed(self.getCollections()):
            shelvesCategory = self.findCategory(collection['identifier'], 'Maya', 'Shelves')
            if shelvesCategory is None:
                continue

            for category in self.iterSubcategories(shelvesCategory):
                for scriptIdentifier in set(category['scripts']) & set(scripts):
                    shelfScripts[category['name']][scriptIdentifier] = category['identifier']

        # Read favourite scripts
        for favouriteScript in self.getFavouriteScripts():
            if favouriteScript['script'] in scripts:
                shelfScripts['Favourites'][favouriteScript['script']] = None

        # Stop here if no scripts found
        if not shelfScripts:
            return

        # Create shelves
        for shelf, scriptIdentifiers in shelfScripts.items():
            if not scriptIdentifiers:
                continue

            shelfName = SHELF_PREFIX + shelf
            createShelf(shelfName)

            # Order scripts
            popularitySort = list(sorted(map(scripts.__getitem__, scriptIdentifiers),
                                         key=itemgetter('execution_count_total'), reverse=True))
            finalSort = []
            wildcardIndex = None
            for group in SHELF_ORDER.get(shelf, SHELF_ORDER['__default__']):
                addSpace = False
                for groupedIdentifier in group:
                    # If a wildcard, then insert all unmatched scripts at this point
                    if groupedIdentifier == '*':
                        wildcardIndex = len(finalSort)

                    # Find the next item to add
                    else:
                        delIndex = None
                        for i, script in enumerate(popularitySort):
                            if script['identifier'] == groupedIdentifier:
                                delIndex = i
                                break
                        else:
                            continue
                        finalSort.append(popularitySort.pop(delIndex))
                        addSpace = True

                # Add a space between each group
                if addSpace:
                    finalSort.append(None)

            # Insert the remaining scripts
            if wildcardIndex is None:
                finalSort.extend(popularitySort)
            else:
                finalSort = finalSort[:wildcardIndex] + popularitySort + finalSort[wildcardIndex:-1]

            for script in finalSort:
                # Create an empty separator
                if script is None:
                    createButton(shelfName, icon='../icons/jtBlank.png')
                    continue

                # Hide legacy scripts if not in the favourites shelf
                if shelf != 'Favourites' and script['state'] != 'Enabled':
                    continue

                # Generate commands
                categoryIdentifier = scriptIdentifiers[script['identifier']]
                command = api_v2.generate_api_command(script['identifier'], category=categoryIdentifier,
                                                      environment='Shelf', _='8ff04588-7409-49c0-92e8-6c1c73dd9a63')

                # Generate tooltip
                if script['description']:
                    tooltip = '<strong>{}</strong><br/><br/>{}'.format(script['name'], script['description'])
                else:
                    tooltip = '<strong>{}</strong>'.format(script['name'])

                contextMenu = [
                    dict(name='Run Script', command=command, icon='../icons/cmd.png'),
                    dict(name='Edit', command='EDIT'),
                ]

                # Unfavourite script
                if script['identifier'] in shelfScripts['Favourites']:
                    contextMenu.append(dict(
                        name='Unfavourite Script',
                        command=partial(
                            multi_function,
                            partial(api_v2.delete, 'favourite-scripts', script=script['identifier'], user=getuser(),
                                    _='4f23c8cc-8dd7-4344-8aa6-fd7b5115effb'),
                            partial(mc.evalDeferred, partial(self.buildShelves, **kwargs)),
                        ),
                        icon='../icons/favourite.svg',
                    ))

                # Favourite script
                else:
                    contextMenu.append(dict(
                        name='Favourite Script',
                        command=partial(
                            multi_function,
                            partial(api_v2.post, 'favourite-scripts', script=script['identifier'], user=getuser(),
                                    _='1d030ca8-f6de-4dab-b6cc-65b2218cea8c'),
                            partial(mc.evalDeferred, partial(self.buildShelves, **kwargs)),
                        ),
                        icon='../icons/favourite.svg',
                    ))
                contextMenu.append(dict(
                    name='Reload Shelf',
                    command=partial(mc.evalDeferred, setup),
                    icon='../icons/refresh.png',
                ))

                icon = api_v2.get_icon('scripts', script['identifier'], _='db4fe6ea-5c86-4655-9041-a9e2d17432ef')
                # Create script button
                createButton(
                    shelfName,
                    label=SHELF_LABELS.get(script['identifier'], script['name']),
                    command=command,
                    #doubleClickCommand=script['code'],
                    icon=icon or 'cmdWndIcon.png',
                    tooltip=tooltip,
                    statustip=script['name'],
                    contextMenu=contextMenu,
                )

    def buildHotkeys(self, **kwargs):
        """Setup Maya hotkeys."""
        def ensureHotkeySet():
            """Make sure we're not on the default locked hotkeySet."""
            if mc.hotkeySet(query=True, current=True) == 'Maya_Default':
                if 'Bluebox' in mc.hotkeySet(query=True, hotkeySetArray=True):
                    logger.info('Switching from default hotkeySet to %r...', DEFAULT_HOTKEYSET_NAME)
                    mc.hotkeySet('Bluebox', edit=True, current=True)
                else:
                    logger.info('Creating %r hotkeySet...', DEFAULT_HOTKEYSET_NAME)
                    mc.hotkeySet('Bluebox', current=True)

        logger.info('Setting up hotkeys...')
        self.getScripts()

        for hotkey in self.getHotkeys():
            commandID = 'Bluebox' + inflection.titleize(hotkey['script']).replace(' ', '')
            script = api_v2.get('scripts', hotkey['script'], _='51763b67-c163-449b-8ac8-bdf77102c9c6')
            command = api_v2.generate_api_command(hotkey['script'], environment='Hotkey',
                                                 _='8cd6ad84-e545-44ae-9376-5715caad96d1')
            ensureHotkeySet()
            mc.nameCommand(commandID, annotation=script['name'], command='python("' + command.replace('\n', ';') + '")')
            mc.hotkey(
                keyShortcut=chr(hotkey['key']),
                ctrlModifier=hotkey['ctrl'],
                shiftModifier=hotkey['shift'],
                altModifier=hotkey['alt'],
                name=commandID,
            )
            logger.info('Set hotkey for %r: %s', hotkey['script'], hotkey['format'])


def setup(globals_=globals(), skipStartupScripts=False):
    """Run the setup."""
    ms = MayaSetup(skipStartupScripts=skipStartupScripts)
    ms.buildAll(globals_=globals_)


if __name__ == '__main__':
    setup()
