import re
from contextlib import contextmanager

import maya.cmds as mc
import maya.mel as mel
from maya.app.general import shelfEditorWindow


def get_trailing_number(s, default=None):
    """Get the number from the end of a string.

    Source: https://stackoverflow.com/a/7085715/2403000
    """
    m = re.search(r'\d+$', s)
    return int(m.group()) if m else default


def multi_function(*fns):
    """Run multiple functions with lambda/partial."""
    for fn in fns:
        fn()


def getMayaWindow():
    return mel.eval('$tmp=$gMainWindow')


def formatCommand(func):
    """Handle the extra arguments given to callable functions."""
    if callable(func):
        return lambda checked, func=func: func()
    return func


def createMenu(name, tearOff=True):
    """Create a menu.

    Parameters:
        name (str): Name to give the menu
        tearOff (bool): If the menu can be detached from the window

    Returns:
        str: Unique identifier of the menu
    """
    return mc.menu(label=name.replace('&', '&&'), parent=getMayaWindow(), tearOff=tearOff)


def deleteMenu(identifier):
    """Delete a menu.

    Parameters:
        id (str): Unique identifier of the menu

    Returns:
        bool: If the menu was deleted
    """
    if mc.menu(identifier, exists=True):
        return mc.deleteUI(mc.menu(identifier, edit=True, deleteAllItems=True))
    return False


def addMenuItem(parent, name, clickCommand, optionCommand=None, icon=None, sourceType='python'):
    """Create a menu item.

    Parameters:
        parent (str): Internal name of the menu
        name (str): Name of item
        clickCommand (func) Execute when item clicked
        optionCommand (func) Execute when the option button is clicked
        icon (str): Path to image to use as the icon

    Returns:
        str: Unique identifier of the menu item
    """
    item = mc.menuItem(
        parent=parent,
        label=name,
        command=formatCommand(clickCommand),
        image=icon,
    )

    if optionCommand is not None:
        mc.menuItem(
            optionBox=True,
            command=formatCommand(optionCommand), sourceType=sourceType,
        )

    return item


@contextmanager
def addSubmenu(name, icon=None, tearOff=True):
    """Create a menu item to contain its own menu.
    It is vital setParent('..') is called after adding items, even if
    the parent is set in the child items.

    Yields:
        str: Unique identifier of submenu
    """
    yield mc.menuItem(
        label=name,
        subMenu=True,
        image=icon,
        tearOff=tearOff,
    )
    mc.setParent('..', menu=True)


def listShelves():
    """Get a list of all shelves."""
    topLevelShelf = mel.eval('string $m = $gShelfTopLevel')
    return mc.shelfTabLayout(topLevelShelf, query=True, childArray=True)


def shelfExists(name):
    """Check if a shelf exists."""
    return mc.shelfLayout(name, query=True, exists=True)


def createShelf(name, **kwargs):
    """Create a shelf."""
    return mc.shelfLayout(name, parent='ShelfLayout', **kwargs)


def clearShelf(name):
    """Clear a shelf.
    Warning: Only works if shelf is currently selected.
    """
    childItems = mc.shelfLayout(name, query=True, childArray=True)
    if childItems is not None:
        for item in childItems:
            mc.deleteUI(item)


def deleteShelf(name):
    """Delete a shelf."""
    clearShelf(name)
    mc.deleteUI(name)


def currentShelf():
    """Get the currently selected shelf tab."""
    topLevelShelf = mel.eval('string $m = $gShelfTopLevel')
    return mc.shelfTabLayout(topLevelShelf, query=True, selectTab=True)


def setCurrentShelf(name):
    """Set the currently selected shelf tab."""
    topLevelShelf = mel.eval('string $m = $gShelfTopLevel')
    try:
        mc.shelfTabLayout(topLevelShelf, edit=True, selectTab=name)
    except RuntimeError:
        return False
    return True


def createButton(shelf, label=None, command=None, icon=None, tooltip=None, statustip=None, contextMenu=None, **kwargs):
    kwargs['parent'] = shelf
    if label is not None:
        kwargs['label'] = label
    if command is not None:
        kwargs['command'] = command
    if label is not None:
        kwargs['imageOverlayLabel'] = label
    if icon is not None:
        kwargs['image1'] = icon
    if tooltip is not None:
        kwargs['annotation'] = tooltip
    if statustip is not None:
        kwargs['statusBarMessage'] = statustip
    if contextMenu is not None:
        kwargs['noDefaultPopup'] = True
    btn = mc.shelfButton(**kwargs)
    if contextMenu is not None:
        setButtonMenu(btn, *contextMenu)
    return btn


def setButtonMenu(shelfButton, *funcs):
    """Create a custom context menu for a shelf button.

    Example:
        >>> btn = createShelfButton('Custom Menu')
        >>> createButtonMenu(btn, ('Function 1', print(1)), ('Function 2', 'print(2)'))
    """
    contextMenu = mc.popupMenu(parent=shelfButton, button=3)
    for data in funcs:
        kwargs = {
            'label': data['name'],
        }
        if callable(data['command']):
            kwargs['command'] = lambda checked, data=data, *args, **kwargs: data['command'](*args, **kwargs)
        elif data['command'] == 'EDIT':
            kwargs['command'] = lambda checked: editButton(shelfButton)
        else:
            kwargs['command'] = data['command']
        if 'icon' in data:
            kwargs['image'] = data['icon']
        mc.menuItem(sourceType='python', parent=contextMenu, **kwargs)


def editButton(button):
    """Open the edit window for a shelf button."""
    return shelfEditorWindow.doIt(selectedShelfButton=button)
