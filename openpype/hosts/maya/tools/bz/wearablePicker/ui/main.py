from maya import cmds as mc, mel, OpenMayaUI as omui

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2 import __version__
from shiboken2 import wrapInstance

import os

# Package imports
from .attachToTreeView import AttachToTreeView
from .propsTableView import PropsTableView
from ..functions import attachWearable
from . import static


class WearablePicker(QWidget):
    '''The tool window.

    This is the main widget of the tool and it acts as window
    in which the other UI elements (props and attachTo lists)
    are added.
    '''

    def __init__(self, parent):
        super(WearablePicker, self).__init__(parent)

        # Set flags and window options
        #   Name, icon and make sure change of focus doesn't hide it
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("bz Wearable Prop Picker")
        self.setWindowIcon(QIcon(QPixmap("C:/bz_pipeline/icons/rigging/rigType_prop.png")))

        # Get the available unattached wearable props
        self.props = self.getAvailableProps()

        # Actial GUI creation
        #   Load up the styles
        with open(os.path.join(os.path.split(__file__)[0], "styles.css"), "r") as f:
            self.setStyleSheet(f.read())

        #   Build the ui elements
        self.buildUI()

        # Resize to the minimum size
        self.resize(self.minimumSizeHint())

    def buildUI(self):
        '''Creates the actual UI elements.

        Creates the prop and attachTo lists, as well as,
        the buttons and menus, adding them to a grid layout.
        '''
        # Building elements from top to bottom
        # Help menu
        menuBar = QMenuBar(self)
        helpMenu = menuBar.addMenu("Help")

        documentationAction = QAction(QIcon(static.icons.documentation),
                                      "Documentation",
                                      self)
        documentationAction.setStatusTip("View Documentation")
        # documentationAction.triggered.connect()

        helpMenu.addAction(documentationAction)

        # Buttons
        buttonsLayout = QHBoxLayout()

        refreshButton = QPushButton(QIcon(QPixmap(static.icons.refresh)), "")
        refreshButton.clicked.connect(self.refresh)

        attachButton = QPushButton(QIcon(QPixmap(static.icons.attach)), "")
        attachButton.clicked.connect(self.attach)

        buttonsLayout.addStretch()
        buttonsLayout.addWidget(refreshButton)
        buttonsLayout.addWidget(attachButton)

        # List of available assets to attach TO
        self.attachToTreeView = AttachToTreeView()

        # List of available unattached wearable props
        self.propsTableView = PropsTableView(self, self.props)

        # Create the grid layout and add widgets and layout to it
        self.setLayout(QGridLayout())

        self.layout().addLayout(buttonsLayout, 0, 0, 1, 6)
        self.layout().addWidget(self.propsTableView, 1, 0, 1, 3)
        self.layout().addWidget(self.attachToTreeView, 1, 3, 1, 3)

    def getAvailableProps(self):
        wearableProps = [each.split(":")[0]
                         for each in mc.ls("*:C_characterNode_CTL")
                         if mc.objExists(each + ".wearable") and
                         not mc.getAttr(each + ".wearable.activated")]

        # If we are working in a rigging WIP scene
        if mc.objExists("C_characterNode_CTL.attachesTo"):
            wearableProps.append("")

        return [(prop, mc.getAttr(prop + ":C_characterNode_CTL.attachesTo"))
                for prop in wearableProps]

    def refresh(self):
        '''Refreshes the UI, getting the new lists of props and attachTo assets.'''
        # Clean up the props list view
        while self.propsTableView.model().rowCount():
            self.propsTableView.model().removeRow(0)

        # Clean up the attachTo list view
        while self.attachToTreeView.model().rowCount():
            self.attachToTreeView.model().removeRow(0)

        # Get a new list of props
        self.props = self.getAvailableProps()

        # Reinitialize props view
        self.propsTableView._previousAttachTo = None

        # Repopulate the props list
        self.propsTableView.props = self.props
        self.propsTableView.initModel()

        # Add the empty message to the attachTo view
        self.attachToTreeView.addEmptyMessage()

    def attach(self, attachToAsset=None, attachToAssetId=None):
        '''Performs the actual attaching of the wearable to the specified asset.

        Following is a brief overview of how the attaching is performed

        - 

        Args:
            attachToAsset: (Optional) The name of the asset to attachTo (default: {None})
            attachToAssetId: (Optional) The row of the specified attachTo QStandardItem (default: {None})
        '''
        # If an asset hasn't been passed, we need to find it or if is not
        # specified we do nothing
        if not attachToAsset:
            selectedAttachToIndices = self.attachToTreeView.selectedIndexes()
            if not selectedAttachToIndices:
                return

            attachToAsset = self.attachToTreeView.model().data(selectedAttachToIndices[0])
            attachToAssetId = selectedAttachToIndices[0].row()

        # If no prop is selected we do nothing
        selectedPropIndices = self.propsTableView.selectedIndexes()

        if not selectedPropIndices:
            return

        # Get the selected prop name and index in the model
        propId = selectedPropIndices[0].row()
        prop = self.propsTableView.model().data(self.propsTableView.model().index(propId, 0))

        # Accomodate testing in the rigging WIP file (no namespace)
        prop = prop if prop != "{build}" else ""

        # Do the actual attach
        attached = attachWearable(prop, attachToAsset)

        if not attached:
            mc.error("WEARABLE PICKER: Error attaching the wearable.")

        # Add the attached prop as a child to the attachTo asset
        propAttached = QStandardItem(prop if prop else "{build}")
        propAttached.setIcon(QIcon(QPixmap(
            mc.getAttr(prop + ":C_characterNode_GRPIcon.iconName"))))
        propAttached.setFlags(Qt.NoItemFlags)

        self.attachToTreeView.model().item(attachToAssetId).appendRow(propAttached)

        # Expand the attachTo asset, so we can visualise the functionality
        self.attachToTreeView.expand(
            self.attachToTreeView.model().index(attachToAssetId, 0))

        # Remove the prop from the unattached list
        # Set the internal flag first to make sure we disable the
        # selectionChanged callback while we perform the removal
        self.propsTableView._internalSelectionChange = True
        self.propsTableView.model().removeRow(propId)
        self.propsTableView._internalSelectionChange = False

        # If the props view is empty now, add the empty message
        if self.propsTableView.model().rowCount() == 0:
            self.propsTableView.props = []
            self.propsTableView.initModel()
