from qtpy import QtWidgets, QtCore
import maya.OpenMayaUI as mui
from shiboken2 import wrapInstance, getCppPointer
import maya.cmds as cmds

class ViewportWidget(QtWidgets.QWidget):
    panelName = "cats"
    def __init__(self, parent=None):
        super(ViewportWidget, self).__init__(parent=parent)
        self.makeViewport()

    def makeViewport(self):
        if self.panelName in cmds.lsUI(panels=1):
            cmds.deleteUI(self.panelName, panel=1)

        self.playbast_layout = QtWidgets.QVBoxLayout()
        self.playbast_layout.setContentsMargins(0,0,0,0)
        self.playbast_layout.setAlignment(QtCore.Qt.AlignHCenter)

        self.top_vertical = QtWidgets.QVBoxLayout()
        self.top_vertical.setContentsMargins(0,0,0,0)

        self.top_vertical.setObjectName("playblastTopLayout")
        self.playbast_layout.setContentsMargins(0,0,0,0)

        self.play_blast_frame = QtWidgets.QFrame()
        self.play_blast_frame.setObjectName("mainLayoutFrame")
        self.play_blast_frame.setLayout(self.playbast_layout)
        self.gridLayout_16 = QtWidgets.QGridLayout()
        self.gridLayout_16.addWidget(self.play_blast_frame, 0, 0, 1, 1)

        self.playbast_layout.setObjectName("mainLayout")
        layout = mui.MQtUtil.fullName(int( int(getCppPointer(self.playbast_layout)[0]) ))
        cmds.setParent(layout)

        self.paneLayoutName = cmds.paneLayout(p=layout)
        ptr = mui.MQtUtil.findControl(self.paneLayoutName)
        self.paneLayout = wrapInstance(int(ptr), QtWidgets.QWidget)

        # create panel and add the current settings
        model_editor, camera, display_app, use_default_ma = self.get_active_camera()
        self.modelPanelName = cmds.modelPanel(self.panelName, label="PlayblastView", cam=camera, menuBarVisible=False)

        self.editor = cmds.modelPanel(self.modelPanelName, q=1, modelEditor=1)

        # Set model editor for playblast flags
        cmds.modelEditor(self.editor, edit=True, udm=use_default_ma,
        displayTextures = True,
        displayAppearance="smoothShaded",
        selectionHiliteDisplay=False,
        headsUpDisplay=True)
        cmds.modelEditor(self.editor, edit=True, allObjects=False)
        cmds.modelEditor(self.editor, edit=True, pluginObjects=("gpuCacheDisplayFilter",True),polymeshes=True)

        ptr = mui.MQtUtil.findControl(self.modelPanelName)
        self.modelPanel = wrapInstance(int(ptr), QtWidgets.QWidget)
        self.playbast_layout.addWidget(self.paneLayout)

        self.setLayout(self.gridLayout_16)

    def get_active_camera(self):
        """ Find the active camera view
            and model panel.

            Return:
                model_editor (str): Current maya model panel.
                camera (str): Current active camera.
        """
        model_editor = cmds.playblast(ae=1)
        camera = cmds.modelEditor(model_editor,q=1,camera=1)
        display_app = cmds.modelEditor(model_editor, q=1, da=1)
        use_default_mat = cmds.modelEditor(model_editor, q=True, udm=True)
        return model_editor, camera, display_app, use_default_mat



        '''
        print(123)
        panel = cmds.playblast(activeEditor=True)

        #self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        #self.setAttribute(QtCore.Qt.WA_PaintOnScreen)
        #self.setObjectName("View")
        modelPanel = cmds.playblast(activeEditor=True).split('|')[-1]
        # get modelPanel: always proved a reliable way to get the active modelPanel
        if not modelPanel or not cmds.modelPanel(modelPanel, exists=True):
            modelPanel = cmds.playblast(activeEditor=True).split('|')[-1]

        # Grab the last active 3d viewport
        view = None
        if modelPanel is None:
            view = mui.M3dView.active3dView()
        else:
            try:
                view = mui.M3dView()
                mui.M3dView.getM3dViewFromModelEditor(modelPanel, view)
            except:
                # in case the given modelPanel doesn't exist!!
                view = mui.M3dView.active3dView()


        #view = mui.M3dView.getM3dViewFromModelEditor(panel)
        view =  mui.MQtUtil.findControl(panel)
        self._widget = wrapInstance(int(view),QtWidgets.QDialog)
        '''
