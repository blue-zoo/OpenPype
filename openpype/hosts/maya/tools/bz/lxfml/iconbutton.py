"""Clickable Qt icon."""

from __future__ import absolute_import

from Qt import QtCore, QtGui, QtWidgets


class IconButton(QtWidgets.QPushButton):

    STYLESHEET = """QPushButton::!pressed#iconButton{
        background-color: transparent;
        border:none;
    }"""

    def __init__(self, icon=None, *args, **kwargs):
        super(IconButton, self).__init__(*args, **kwargs)
        if isinstance(icon, QtGui.QIcon):
            self.setIcon(icon)
        elif isinstance(icon, QtGui.QPixmap):
            self.setPixmap(icon)
        elif icon is not None:
            self.setIconPath(icon)
        self.setObjectName('iconButton')
        self.setStyleSheet(self.STYLESHEET)

    def iconPath(self):
        return self._iconPath

    def setIconPath(self, path):
        if path is None:
            path = ''
        self._iconPath = path
        self._iconPixmap = QtGui.QPixmap(path)
        super(IconButton, self).setIcon(QtGui.QIcon(self._iconPixmap))

    def pixmap(self):
        return self._iconPixmap

    def setPixmap(self, pixmap):
        self._iconPath = ''
        self._iconPixmap = pixmap
        self.setIcon(QtGui.QIcon(pixmap))

    def setIcon(self, icon):
        self._iconPath = ''
        maxSize = max((size for size in icon.availableSizes()), key=lambda size: size.width() * size.height())
        self._iconPixmap = icon.pixmap(maxSize)
        super(IconButton, self).setIcon(icon)

    def setIconSize(self, size):
        return super(IconButton, self).setIconSize(size)

        # This doesn't yet work
        if not self._iconPixmap.isNull() and (size.width() > self._iconPixmap.width() or size.height() > self._iconPixmap.height()):
            newPixmap = self._iconPixmap.scaled(size)
            return super(IconButton, self).setIcon(QtGui.QIcon(newPixmap))
        return super(IconButton, self).setIconSize(size)

    def setFixedSize(self, size, sizeY=None):
        if sizeY is not None:
            size = QtCore.QSize(size, sizeY)
        super(IconButton, self).setFixedSize(size)
        size -= QtCore.QSize(2, 2)
        self.setIconSize(size)


class PromotedIconButton(IconButton):
    """Inherit IconButton to work with Qt Designer."""

    STYLESHEET = """QPushButton::!pressed{
        background-color: transparent;
        border:none;
    }"""
    def __init__(self, parent):
        super(PromotedIconButton, self).__init__(parent=parent)

    def setIcon(self, icon):
        if isinstance(icon, QtGui.QIcon):
            super(PromotedIconButton, self).setIcon(icon)
        else:
            self.setIconPath(icon)


class PromotedIcon(PromotedIconButton):
    """Create an icon the same size as the buttons to work with Qt Designer."""

    STYLESHEET = """QPushButton{
        background-color: transparent;
        border:none;
    }"""
