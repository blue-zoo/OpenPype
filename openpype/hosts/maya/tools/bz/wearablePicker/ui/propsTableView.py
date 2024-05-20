from maya import cmds as mc, mel, OpenMayaUI as omui

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2 import __version__
from shiboken2 import wrapInstance

import os
import json

# Package imports
from . import static


class PropsTableView(QTableView):
    '''The list of available unattached props.

    On selection change this updates the attachTo list with all the available
    assets the currently selected wearable can connect to.

    Supports dragging to the assets lis.
    '''

    def __init__(self, parent, props):
        super(PropsTableView, self).__init__(parent)
        # Initialize data
        self.props = props

        # Internal variables for checks
        self._previousAttachTo = None
        self._internalSelectionChange = False

        # Set flags and options
        self.setShowGrid(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragEnabled(True)

        # Headers modifications
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setHighlightSections(False)

        # Alternate row colors - easier to see rows
        self.setAlternatingRowColors(True)

        #   Load up the styles
        with open(os.path.join(os.path.split(__file__)[0], "styles.css"), "r") as f:
            self.setStyleSheet(f.read())

        # Iniialize the model
        self.initModel()

        # Constrain minimum size
        self.setMinimumSize(300, 250)

    def initModel(self):
        '''Creates and populates the model for this view.'''
        if self.model():
            self.model().deleteLater()

        model = QStandardItemModel()
        self.setModel(model)

        # Populate if props if any otherwise add the empty message
        if self.props:
            # Set header labels and alignment
            model.setHorizontalHeaderLabels(['Unattached Wearables', 'Attaches to'])
            model.setHeaderData(0, Qt.Horizontal, Qt.AlignLeft, Qt.TextAlignmentRole)
            model.setHeaderData(1, Qt.Horizontal, Qt.AlignRight, Qt.TextAlignmentRole)

            # Populate list
            disabledBrush = QBrush(QColor(static.colours.disabled))

            for (prop, attachesTo) in self.props:
                itemWearable = QStandardItem(prop if prop else "{build}")
                itemAttachTo = QStandardItem(attachesTo)

                itemWearable.setIcon(QIcon(QPixmap(mc.getAttr(prop + ":C_characterNode_GRPIcon.iconName"))))

                itemAttachTo.setTextAlignment(Qt.AlignCenter | Qt.AlignRight)
                itemAttachTo.setData(disabledBrush, Qt.ForegroundRole)

                model.appendRow([itemWearable, itemAttachTo])

            # Set headers stretch policy
            self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        else:
            # Instantiate header for the empty message
            model.setHorizontalHeaderLabels(['Unattached Wearables'])
            model.setHeaderData(0, Qt.Horizontal, Qt.AlignLeft, Qt.TextAlignmentRole)
            self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

            self.addEmptyMessage()

    def addEmptyMessage(self):
        '''Creates an item in the view with an instructions message.'''
        emptyItem = QStandardItem("     No unattached <b>wearable</b> props.")
        emptyItem.setData(QBrush(QColor(static.colours.disabled)), Qt.ForegroundRole)
        emptyItem.setFlags(Qt.NoItemFlags)
        self.model().appendRow(emptyItem)

    def selectionChanged(self, selected, deselected):
        '''Repopulates the attachTo assets list based on the selection.

        We run the base implementation first to maintain proper selection 
        behaviour.

        Args:
            selected: The currently selected indices
            deselected: The deselected indices
        '''
        super(PropsTableView, self).selectionChanged(selected, deselected)

        # If the selection change happened because we attached a prop and removed
        # it from this list, then clear the selection and do nothing more as
        # otherwise it becomes a bit disruptive
        if self._internalSelectionChange:
            self.clearSelection()
            return

        # Grab the model of the attachTo view as we are going to need it
        attachToModel = self.parent().attachToTreeView.model()

        if selected:
            selectedIndices = selected.indexes()

            # The first one is the name of the prop and the second the asset(s)
            # it can attach to
            selectedProp = self.model().data(selectedIndices[0])
            attachesTo = self.model().data(selectedIndices[1])

            if attachesTo == self._previousAttachTo \
                    and attachToModel.rowCount():
                    # If the attach to asset hasn't changed since last selection
                    # and the attachTo list is populated, do nothing
                return

            self._previousAttachTo = attachesTo

            try:
                attachesToList = json.loads(attachesTo)
                attachesToList = attachesToList if not isinstance(attachesToList, (str,u''.__class__)) else [attachesToList]
            except ValueError as e:
                if '[' not in attachesTo:
                    attachesTo = attachesTo.replace('"', '')
                    attachesToList = [attachesTo]
                else:
                    raise e

            availableAttachToAssets = [each.split(':')[0] for a in attachesToList 
                                       for each in mc.ls('{}_ri*:C_characterNode_CTL'.format(a))]

            # Clear and repopulate the attachTo view with the appropriate assets
            while attachToModel.rowCount():
                attachToModel.removeRow(0)

            for asset in availableAttachToAssets:
                item = QStandardItem(asset)
                if mc.objExists(asset+":C_characterNode_GRPIcon.iconName"):
                    item.setIcon(QIcon(QPixmap(
                        mc.getAttr(asset + ":C_characterNode_GRPIcon.iconName"))))

                # Find the already attached wearables and add them as children
                attachedProps = [each for each in mc.listConnections(
                    asset + ":C_characterNode_CTL.message", d=1, p=1)
                    if each.endswith(".attachedTo")]

                for attached in attachedProps:
                    attachedItem = QStandardItem(attached.split(":")[0])
                    attachedItem.setIcon(QIcon(QPixmap(
                        mc.getAttr(
                            attached.split(":")[0] + ":C_characterNode_GRPIcon.iconName"))))
                    attachedItem.setFlags(Qt.NoItemFlags)

                    item.appendRow(attachedItem)

                attachToModel.appendRow(item)
