from functools import wraps

from qtpy import QtCore, QtGui, QtWidgets

import maya.cmds as mc


def getDescendants(nodes=None, nodeType=None, _intermediateObjects=None):
    """Get all the children of an object, with optional node type limits.

    Equivalent:
        `[name] + [node.longName for node in Node(name).descendents if node.type == nodeType]`
    """
    # Parse the input/selection
    if nodes is None:
        nodes = set(mc.ls(selection=True, long=True))
    else:
        nodes = set(mc.ls(nodes, long=True))

    # Remove intermediate objects
    if _intermediateObjects is None:
        _intermediateObjects = set(mc.ls(intermediateObjects=True, long=True))
    nodes -= _intermediateObjects

    # Re-run the function on all child nodes
    children = mc.listRelatives(nodes, children=True, fullPath=True)
    if children:
        nodes |= getDescendants(children, nodeType=nodeType,
                                _intermediateObjects=_intermediateObjects)

    # Filter the output
    if nodeType is not None:
        nodes = {node for node in nodes if mc.nodeType(node) == nodeType}

    return nodes


class UndoChunk(object):
    """Batch commands together in an undo chunk.
    Works as both a wrapper and context manager.
    """
    def __call__(self, fn):
        """Add as a function wrapper."""
        @wraps(fn)
        def wrapper(*args, **kwargs):
            with type(self)():
                return fn(*args, **kwargs)
        return wrapper

    def __enter__(self):
        mc.undoInfo(openChunk=True)
        return self

    def __exit__(self, *args):
        mc.undoInfo(closeChunk=True)
        return False


class TemporaryCursor(object):
    """Temporarily set a custom cursor during execution.
    This works as both a context manager and wrapper.
    """

    __slots__ = ('cursor', 'inst')

    def __init__(self, cursor=QtCore.Qt.WaitCursor):
        self.cursor = cursor
        self.inst = QtWidgets.QApplication.instance()

    def __call__(self, func):
        """Add as a function wrapper."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.__class__(self.cursor):
                return func(*args, **kwargs)
        return wrapper

    def __enter__(self):
        """Setup as a context manager."""
        if self.inst is not None and self.cursor is not None:
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(self.cursor))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the context manager and restore the cursor."""
        if self.inst is not None and self.cursor is not None:
            QtWidgets.QApplication.restoreOverrideCursor()
        if exc_tb is not None:
            return False
