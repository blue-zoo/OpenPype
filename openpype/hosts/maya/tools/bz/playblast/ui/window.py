import sys
import time
import os
import logging
import importlib
import re
from functools import partial

from qtpy import QtWidgets, QtCore, QtGui
from openpype.hosts.maya.tools.bz.playblast.ui import windowUI
importlib.reload(windowUI)

from openpype.hosts.maya.tools.bz.playblast.core import playblast

from openpype.hosts.maya.tools.bz.playblast.core import utils
importlib.reload(utils)

from openpype.hosts.maya.tools.bz.playblast.core.utils import (
    getAyonShotAttributes,
    getMayaShotAttributes,
    getRenderableCamera,
    getVideoRoot
)

from openpype.pipeline import get_current_project_name
from openpype.tools.utils.lib import qt_app_context
from openpype.hosts.maya.api.lib import (
    get_main_window
)
from openpype.hosts.maya.api import (
    lib,
    plugin
)
from ayon_api import (
    get_folder_by_name,
    get_folder_by_path,
    get_folders,
)
from maya import cmds  # noqa: F401

from openpype.hosts.maya.api import plugin
from openpype.pipeline import (
    get_current_asset_name,
    get_current_project_name,
)

from maya import cmds
# old api for MFileIO
import maya.OpenMaya as om

module = sys.modules[__name__]
module.window = None

global LAST_PLAYBLASTED_FRAME
COMMENT_REGEX = r"([\.a-zA-Z0-9_-]){1,}"
FILENAME_REGEX = r"([a-zA-Z0-9_-]){1,}"
PLAYBLAST_PREF_FOLDER ="entityPlayblastFolder_{n}"

class MayaPlayblastWindow(QtWidgets.QWidget,windowUI.Ui_PlayblasterWidget):

    def __init__(self, parent=None):
        super(MayaPlayblastWindow, self).__init__(parent=parent)

        self.log = logging.getLogger(__name__)

        self.entityName = "playblast"
        self.setupUi(self)

        self.setObjectName("PlayblastTool")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setParent(parent)
        self.resize(750, 500)

        # File name
        self._fileName = "playblast"

        # Callback for update progress bar
        self._callbackId = None

        # Set regex for the comment bar
        self._setCommentRegex()

        # Set regex for the file name
        self._setFilenameRegex()

        self._setWindowDefaults()

    def _setFilenameRegex(self):
        regex = QtCore.QRegExp(FILENAME_REGEX)
        validator = QtGui.QRegExpValidator(regex, self.videoFileNameLineEdit)
        self.videoFileNameLineEdit.setValidator(validator)


    def _setCommentRegex(self):
        regex = QtCore.QRegExp(COMMENT_REGEX)
        validator = QtGui.QRegExpValidator(regex, self.commentBurnInLineEdit)
        self.commentBurnInLineEdit.setValidator(validator)

    def setCommentToSceneName(self):
        # To set the comment
        fileName = cmds.file(query=1,sceneName = True)

        # If filename
        if fileName:
            _path,_file = os.path.split(fileName)
            _fileName,_ext = os.path.splitext(_file)
            _comment = [ l for l in str(_fileName) if re.search(COMMENT_REGEX,l) ]

            # Went through all the file name characters and checked that they match the regex
            if _comment:
                _comment = ''.join(_comment)
                self.commentBurnInLineEdit.setText(_comment)


    def updateTimesFromAyon(self):
        startFrame, endFrame = self._setAyonFrameDetails()
        self.playblastStartLineEdit.setText(str(startFrame))
        self.playblastEndLineEdit.setText(str(endFrame))

    def updateTimesFromMaya(self):
        startFrame, endFrame = getMayaShotAttributes()
        startFrame = int(startFrame)
        endFrame = int(endFrame)
        self.playblastStartLineEdit.setText(str(startFrame))
        self.playblastEndLineEdit.setText(str(endFrame))

    def _setAyonFrameDetails(self):
        entityName, startFrame, endFrame , resX, resY = getAyonShotAttributes()
        startFrame = int(startFrame)
        endFrame = int(endFrame)

        self.ayonResolutionWidthLineEdit.setText(str(resX))
        self.ayonResolutionHeightLineEdit.setText(str(resY))

        self.ayonStartLineEdit.setText(str(startFrame))
        self.ayonEndLineEdit.setText(str(endFrame))

        self.ayonShotNameLineEdit.setText(str(entityName))

        self.entityName = entityName
        return startFrame, endFrame

    @property
    def fileName(self):
        return self.videoFileNameLineEdit.text()+playblast.EXTENSION

    @fileName.setter
    def fileName(self,v):
        self.videoFileNameLineEdit.setText(v)

    @property
    def filePath(self):
        return os.path.join(self.playblastVideoFolderLineEdit.text(), self.fileName)

    def _setMayaFrameDetails(self):
        startFrame, endFrame = getMayaShotAttributes()

        self.playblastStartLineEdit.setText(str(startFrame))
        self.playblastEndLineEdit.setText(str(endFrame))

    def addCallback(self,playblastStartTime,playblastEndTime):
        self.progressBar.setRange(playblastStartTime,playblastEndTime)
        self._callbackId = om.MDGMessage.addTimeChangeCallback(partial(updateProgressBar,self.progressBar))

    def removeCallback(self):
        if self._callbackId:
            om.MDGMessage.removeCallback(self._callbackId)
            self._callbackId = None
        self.progressBar.reset()

    def setPlayblastCamera(self):
        sel = cmds.ls(sl=True)
        sel.extend(cmds.listRelatives(sel,shapes=True,type="camera") or [])
        cameras = [c for c in sel if cmds.nodeType(c)== "camera"]
        if cameras:
            camera = cameras[0]
            [cmds.setAttr(c+".renderable",False) for c in cmds.ls(cameras=True) if c != camera]
            cmds.setAttr(camera+".renderable",True)
            cmds.modelEditor(self.viewport.editor,e=1,camera=camera)

            self.cameraLineEdit.setText(camera)

    def _setPlayblastSettings(self):
        pass

    def _restorePlayblastSettings(self):
        pass

    def runPlayblast(self):
        #return
        self.addCallback(self.playblastStartTime,self.playblastEndTime)
        importlib.reload(playblast)
        editor = self.viewport.editor
        print('Playblasting to:',self.filePath)


        # TODO: Override the width height in a nicer manner
        if self.playblastWidth == 1920 and self.playblastHeight == 1080:
            playblastWidth = 1024
            playblastHeight = 576
        else:
            playblastWidth = self.playblastWidth
            playblastHeight = self.playblastHeight


        try:
            self._setPlayblastSettings()
            playblast.playblast(
                startTime = self.playblastStartTime,
                endTime = self.playblastEndTime,
                width = playblastWidth,
                height = playblastHeight,
                editor = editor,
                camera = self.renderableCamera,
                comment = self.playblastComment,
                outputFile = self.filePath

            )

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            raise e
        finally:
            self.removeCallback()
            self._restorePlayblastSettings()

    def setPlayblastFolder(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory()
        if directory:
            optVar = PLAYBLAST_PREF_FOLDER.format(n=self.entityName.strip())
            cmds.optionVar(  sv=(optVar, directory  ) )

        self.playblastVideoFolderLineEdit.setText(directory)
        return

    @property
    def playblastWidth(self):
        return int(self.ayonResolutionWidthLineEdit.text())

    @property
    def playblastComment(self):
        return self.commentBurnInLineEdit.text()

    @property
    def playblastHeight(self):
        return int(self.ayonResolutionHeightLineEdit.text())

    @property
    def playblastStartTime(self):
        return int(self.playblastStartLineEdit.text())

    @property
    def playblastEndTime(self):
        return int(self.playblastEndLineEdit.text())

    @property
    def renderableCamera(self):
        return self.cameraLineEdit.text()

    def setRenderableCamera(self):
        camera = getRenderableCamera()
        self.cameraLineEdit.setText(camera)
        cmds.modelEditor(self.viewport.editor,e=1,camera=camera)

    def setAyonVideoFolder(self, entityName ):
        optVar = PLAYBLAST_PREF_FOLDER.format(n=self.entityName.strip())

        # Check if the folder was overriden for this entity
        if cmds.optionVar( exists=optVar ) and os.path.isdir( cmds.optionVar( q=optVar )  ):
            folder = cmds.optionVar( q=optVar )
        else:
            folder = getVideoRoot()

        self.playblastVideoFolderLineEdit.setText(folder)

    def _setWindowDefaults(self):

        # Set ayon details
        self._setAyonFrameDetails()

        # Set maya details as default
        self.updateTimesFromMaya()

        # get renderable camera
        self.setRenderableCamera()

        # set the video folder
        self.setAyonVideoFolder( self.entityName )

        # Set Comment to scene name
        self.setCommentToSceneName()

        # Set File name from entity name
        self.videoFileNameLineEdit.setText( self.entityName )



def updateProgressBar(bar,newTime,status):
    playingBack = om.MConditionMessage.getConditionState( "playingBack" )
    frame = int(newTime.value())
    global LAST_PLAYBLASTED_FRAME

    LAST_PLAYBLASTED_FRAME = frame

    if playingBack:
        bar.setValue( frame )


def show():
    """Display Loader GUI

    Arguments:
        debug (bool, optional): Run loader in debug-mode,
            defaults to False

    """
    print(module.window)
    try:
        module.window.close()
        del module.window
    except (RuntimeError, AttributeError) as e:
        print(e)
        pass

    # Get Maya main window
    mainwindow = get_main_window()

    with qt_app_context():
        window = MayaPlayblastWindow(parent=mainwindow)
        window.show()
        #window.runPlayblast()
        module.window = window
        print(module.window)
    return module.window
