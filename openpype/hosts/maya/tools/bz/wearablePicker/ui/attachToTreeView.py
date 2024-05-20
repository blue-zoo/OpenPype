from maya import cmds as mc, mel, OpenMayaUI as omui

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2 import __version__
from shiboken2 import wrapInstance

import os

# Package imports
from . import static


class AttachToTreeView(QTreeView):
    '''Lists all the available assets, props can attach to.

    All the already attached props are also going to be shown under the entries.

    Accepts drops in the form of props from the prop list view.
    '''

    def __init__(self):
        super(AttachToTreeView, self).__init__()

        # Set flags and options
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Initialize model
        self.setModel(QStandardItemModel())
        self.model().setHorizontalHeaderLabels(["Available assets to attach to"])

        # Add the empty message
        self.addEmptyMessage()

        # Alternate row colors - easier to see rows
        self.setAlternatingRowColors(True)

        # Load up the styles
        with open(os.path.join(os.path.split(__file__)[0], "styles.css"), "r") as f:
            self.setStyleSheet(f.read())

        # Lock the minimum size of the view
        self.setMinimumSize(300, 250)

    def addEmptyMessage(self):
        '''Creates an item in the view with an instructions message.'''
        emptyItem = QStandardItem("Select a wearable prop to see available assets")
        emptyItem.setData(QBrush(QColor(static.colours.disabled)))
        emptyItem.setFlags(Qt.NoItemFlags)
        self.model().appendRow(emptyItem)

    def dropEvent(self, e):
        '''Overrides default drop event to support "attach wearable" functionality.

        Finds the closest asset to the drop location and passes it to the
        attach function of it's parent - the WearablePicker class.

        Args:
            e: The drop QEvent
        '''
        closestId = self.indexAt(e.pos())
        closestRow = closestId.row() if closestId.parent().row() == -1 \
            else closestId.parent().row()
        closestItemName = self.model().item(closestRow).data(Qt.DisplayRole)

        # Call the WearablePicker.attach function
        self.parent().attach(closestItemName, closestRow)

        # Make sure the event is accepted as otherwise the base implementation
        # will run the default dropEvent
        e.accept()

        # Run the base implementation of this function to make sure all the ui
        # aspects of it are handled - ie. The helper outlines added to the
        # elements as indicators for where the dropped item will go need to be
        # properly cleaned up.
        return super(AttachToTreeView, self).dropEvent(e)

    def dragMoveEvent(self, e):
        '''Overwrite the base function, so we can change the cursor to disabled
        when it's not hovering over an acceptable location.
        
        Args:
            e: The dragMove QEvent
        '''
        if e.source() == self.parent().propsTableView:
            if self.indexAt(e.pos()).row() > -1:
                return super(AttachToTreeView, self).dragMoveEvent(e)

        # If the drag move is not supported, ignore the event so the drag and 
        # drop cursor is disabled
        e.ignore()

