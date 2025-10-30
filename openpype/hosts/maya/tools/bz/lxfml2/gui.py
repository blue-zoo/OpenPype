from __future__ import absolute_import

import logging
import os
import re
import webbrowser

from qtpy import QtCore, QtWidgets
from qtpy.uic import loadUi

from ..vfxwindow import VFXWindow

from .everything_else import TemporaryCursor
from .exceptions import UserWarningError, UserExceptionList
from .reader import formatGroupName
from .constants import STYLE_PRESETS


logger = logging.getLogger('lego-importer')


os.environ.setdefault('BZ_LXFML_PRIMITIVES', r'Y:\LEGO\2013s_LegoCitySeries4\Libraries\brickDatabase\Primitives')
os.environ.setdefault('BZ_LXFML_DECORATIONS', r'F:\HighlyUnlikely\1903s_SFLEGOMaster\Libraries\Texture_Library\Decorations')
os.environ.setdefault('BZ_LXFML_COMMONPARTS', r'Y:\LEGO\2013s_LegoCitySeries4\Libraries\brickDatabase\CommonParts')
os.environ.setdefault('BZ_LXFML_SHADER_PATH', r'F:\HighlyUnlikely\1903s_SFLEGOMaster\Libraries\Shader_Library\shaders\master\published\master_shader.ma')
os.environ.setdefault('BZ_LXFML_SHADER_NS', 'shaders')
os.environ.setdefault('BZ_LXFML_SHADER_GROUP', 'PLASTIC_MASTER_SG')
os.environ.setdefault('BZ_LXFML_PALETTE', r'Y:\LEGO\1882s_LegoCityBricksburg\Libraries\Script_Library\LEGOColorPalette\LegoBrickCol_BZ_ACES_CUSTOM.csv')
os.environ.setdefault('BZ_LXFML_SCALE', '20.0')
os.environ.setdefault('BZ_LXFML_STYLE', 'Render')


def _clean_input(path):
    """Strip the edges of inputs to return just the string."""
    return path.strip('-\'" \n')


def _getIcon(name):
    print(os.path.join(os.path.dirname(__file__), 'icons', name))
    return os.path.join(os.path.dirname(__file__), 'icons', name)


class GUI(VFXWindow):
    WindowID = 'bz.lego.importer'
    WindowName = 'LEGO Importer'
    WindowDockable = False

    def __init__(self, parent=None, **kwargs):
        super(GUI, self).__init__(parent=parent, **kwargs)
        self.setWindowPalette('maya')
        loadUi(os.path.join(os.path.dirname(__file__), 'layout.ui'), self)

        self.atomPath.setPlaceholderText(os.environ['BZ_LXFML_PRIMITIVES'])
        self.commonPartsPath.setPlaceholderText(os.environ['BZ_LXFML_COMMONPARTS'])
        self.shdPath.setPlaceholderText(os.environ['BZ_LXFML_SHADER_PATH'])
        self.nsInput.setPlaceholderText(os.environ['BZ_LXFML_SHADER_NS'])
        self.sgInput.setPlaceholderText(os.environ['BZ_LXFML_SHADER_GROUP'])
        self.palettePath.setPlaceholderText(os.environ['BZ_LXFML_PALETTE'])
        self.scaleValue.setValue(float(os.environ['BZ_LXFML_SCALE']))
        self.scaleGrp.setChecked(float(os.environ['BZ_LXFML_SCALE']) != 1)
        self.decalPath.setPlaceholderText(os.environ['BZ_LXFML_DECORATIONS'])

        self.menuClose.triggered.connect(self.close)
        self.menuDocs.triggered.connect(lambda: webbrowser.open('https://sites.google.com/blue-zoo.co.uk/software-tools-workflow/software-tools-workflow-home-page/software/maya/blue-zoo-maya-tools/lego-importer'))

        self.xmlOpen.setIconPath(_getIcon('SP_DirOpenIcon.png'))
        self.atomOpen.setIconPath(_getIcon('SP_DirOpenIcon.png'))
        self.shdOpen.setIconPath(_getIcon('SP_DirOpenIcon.png'))
        self.paletteOpen.setIconPath(_getIcon('SP_DirOpenIcon.png'))
        self.decalOpen.setIconPath(_getIcon('SP_DirOpenIcon.png'))
        self.shaderSwitchValid.setIconPath(_getIcon('valid.png'))
        self.shaderSwitchInvalid.setIconPath(_getIcon('invalid.png'))
        self.maskSwitchValid.setIconPath(_getIcon('valid.png'))
        self.maskSwitchInvalid.setIconPath(_getIcon('invalid.png'))

        self.xmlOpen.clicked.connect(self.chooseXmlFile)
        self.atomOpen.clicked.connect(self.chooseAtomFile)
        self.shdOpen.clicked.connect(self.chooseShaderFile)
        self.shdOpen.clicked.connect(self.choosePaletteFile)
        self.commonPartOpen.clicked.connect(self.chooseCommonPartsFile)

        self.nsInput.textChanged.connect(self.lsShaderSwitch)
        self.switchInput.textChanged.connect(self.lsShaderSwitch)
        self.decalShadingNetwork.toggled.connect(self.lsShaderSwitch)
        self.lsShaderSwitch()
        self.nsInput.textChanged.connect(self.lsMaskSwitch)
        self.maskInput.textChanged.connect(self.lsMaskSwitch)
        self.decalShadingNetwork.toggled.connect(self.lsMaskSwitch)
        self.lsMaskSwitch()

        self.runImport.clicked.connect(self.importAll)

        self.stylePresets.clear()
        self.stylePresets.addItems(sorted(STYLE_PRESETS))
        self.stylePresets.setCurrentText(os.environ['BZ_LXFML_STYLE'])

    def getXmlPath(self):
        """Get the path to the XML file."""
        return _clean_input(self.xmlPath.text() or self.xmlPath.placeholderText())

    def getXmlPaths(self):
        """Get the path to the XML file and its group."""
        return [path.strip() for path in self.getXmlPath().split(',')]

    def getAtomPath(self):
        """Get the path to the geometry folder."""
        return _clean_input(self.atomPath.text() or self.atomPath.placeholderText())

    def getShaderPath(self):
        """Get the path to the shader file."""
        return _clean_input(self.shdPath.text() or self.shdPath.placeholderText())

    def getBrickGroups(self):
        """Get the name to give to the brick group."""
        return [self.formatGroupName(xmlPath) for xmlPath in self.getXmlPaths()]

    def getShaderNamespace(self):
        """Get the namespace to give to the shader."""
        return _clean_input(self.nsInput.text() or self.nsInput.placeholderText())

    def getShadingGroup(self):
        return _clean_input(self.sgInput.text() or self.sgInput.placeholderText())

    def getPalettePath(self):
        """Get the path to the palette file."""
        return _clean_input(self.palettePath.text() or self.palettePath.placeholderText())

    def getDecalPath(self):
        """Get the path to the decal file."""
        return _clean_input(self.decalPath.text() or self.decalPath.placeholderText())

    def getCommonPartsPath(self):
        return _clean_input(self.commonPartsPath.text() or self.commonPartsPath.placeholderText())

    def getShaderSwitch(self):
        """Get the decal shader switch."""
        switch = _clean_input(self.switchInput.text() or self.switchInput.placeholderText())
        if ':' not in switch and not self.decalShadingNetwork.isChecked():
            return self.getShaderNamespace() + ':' + switch
        return switch

    def getMaskSwitch(self):
        """Get the decal mask switch."""
        switch = _clean_input(self.maskInput.text() or self.maskInput.placeholderText())
        if ':' not in switch and not self.decalShadingNetwork.isChecked():
            return self.getShaderNamespace() + ':' + switch
        return switch

    def _openFile(self, title, fileDir, extensions):
        """Prompt the user to choose a file."""
        path, filter = QtWidgets.QFileDialog.getOpenFileName(self, title, fileDir, extensions)
        if not path:
            return ''
        return os.path.normpath(path)

    def _openFiles(self, title, fileDir, extensions):
        """Prompt the user to choose one or more files."""
        paths, filter = QtWidgets.QFileDialog.getOpenFileNames(self, title, fileDir, extensions)
        if not paths:
            return []
        return [os.path.normpath(path) for path in paths]

    def _openDirectory(self, title, fileDir):
        """Prompt the user to choose a directory."""
        path = QtWidgets.QFileDialog.getExistingDirectory(self, title, fileDir)
        if not path:
            return ''
        return os.path.normpath(path)

    @QtCore.Slot()
    def chooseXmlFile(self):
        """Prompt the user to choose an XML file."""
        filePaths = self._openFiles('Select LEGO XML File', self.getXmlPaths()[0], 'LEGO XML Files (*.xml *.lxfml)')
        self.xmlPath.setText(', '.join(filePaths))

    @QtCore.Slot()
    def chooseAtomFile(self):
        folderPath = self._openDirectory('Select Atom Database Root Folder', self.getAtomPath())
        if folderPath:
            self.atomPath.setText(folderPath)

    @QtCore.Slot()
    def chooseShaderFile(self):
        """Prompt the user to choose a shader file."""
        filePath = self._openFile('Select LEGO Shader File', self.getShaderPath(), 'LEGO Shader Files (*.ma *.mb)')
        self.shdPath.setText(filePath)

    @QtCore.Slot()
    def choosePaletteFile(self):
        """Prompt the user to choose a shader file."""
        filePath = self._openFile('Select LEGO Palette File', self.getPalettePath(), 'LEGO Palette Files (*.csv)')
        self.palettePath.setText(filePath)

    @QtCore.Slot()
    def chooseCommonPartsFile(self):
        filePath = self._openDirectory('Select Common Parts Path', self.getCommonPartsPath())
        self.commonPartsPath.setText(filePath)

    @QtCore.Slot()
    def lsShaderSwitch(self):
        """Check if the current shader switch exists in the scene."""
        shaderSwitch = self.getShaderSwitch()
        try:
            import maya.cmds as mc
        except ImportError:
            exists = len(shaderSwitch.split(':')[-1]) > 1  # For testing
        else:
            from .maya.decals import replaceNumberRange
            wildcard = replaceNumberRange(shaderSwitch)[0]
            try:
                exists = bool(mc.ls(wildcard, exactType='RedshiftShaderSwitch'))
            except RuntimeError:
                exists = False

        self.shaderSwitchValid.setVisible(exists)
        self.shaderSwitchInvalid.setVisible(not exists)

    @QtCore.Slot()
    def lsMaskSwitch(self):
        """Check if the current mask switch exists in the scene."""
        maskSwitch = self.getMaskSwitch()
        try:
            import maya.cmds as mc
        except ImportError:
            exists = len(maskSwitch.split(':')[-1]) > 1  # For testing
        else:
            from .maya.decals import replaceNumberRange
            wildcard = replaceNumberRange(maskSwitch)[0]
            try:
                exists = bool(mc.ls(wildcard, exactType='RedshiftShaderSwitch'))
            except RuntimeError:
                exists = False

        self.maskSwitchValid.setVisible(exists)
        self.maskSwitchInvalid.setVisible(not exists)

    @QtCore.Slot()
    def importAll(self):
        """Import everything and notify the user of any errors."""
        failed = []
        if self.atomGrp.isChecked():
            try:
                self.runImportAtom()
            except UserWarningError as e:
                failed.extend(e)
            except Exception as e:  # pylint: disable=broad-except
                logger.exception(e)
                failed.append(e)

        if self.scaleGrp.isChecked() and self.scaleValue.value() != 1:
            try:
                self.runScaleBricks(self.scaleValue.value())
            except Exception as e:  # pylint: disable=broad-except
                logger.exception(e)
                failed.append(e)

        if self.shdGrp.isChecked():
            try:
                self.runAssignShaders()
            except UserWarningError as e:
                failed.extend(e)
            except Exception as e:  # pylint: disable=broad-except
                logger.exception(e)
                failed.append(e)

        if self.paletteGrp.isChecked():
            try:
                self.runApplyPalette()
            except UserWarningError as e:
                failed.extend(e)
            except Exception as e:  # pylint: disable=broad-except
                logger.exception(e)
                failed.append(e)

        if self.decalGrp.isChecked():
            try:
                self.runDecals()
            except UserWarningError as e:
                failed.extend(e)
            except Exception as e:  # pylint: disable=broad-except
                logger.exception(e)
                failed.append(e)

        if failed:
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle('Warning')
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            lines = ['Warning: The following problems occured:', '']
            lines.extend(sorted(set(map(str, failed))))
            msg.setText('\n'.join(lines))
            msg.exec_()

    def formatGroupName(self, xmlPath):
        return formatGroupName(os.path.splitext(os.path.basename(xmlPath))[0])

    @TemporaryCursor()
    def runImportAtom(self):
        """Import the brick geometry."""
        from .maya.geometry import setupScene, BrickDirectory

        for xmlPath in self.getXmlPaths():
            setupScene(
                xmlPath,
                BrickDirectory(self.getAtomPath(), self.stylePresets.currentText(),
                               self.getPalettePath(), group=self.formatGroupName(xmlPath)),
                groups=self.createGroups.isChecked(),
                selectionSets=self.createSelectionSets.isChecked(),
                sockets=self.sockets.isChecked(),
                pivots=self.pivots.isChecked(),
                collapseGeo=self.collapseGeo.isChecked(),
                rename=self.rename.isChecked(),
                commonPartsPath=self.getCommonPartsPath() if self.replaceCommonParts.isChecked() else None,
            )

    @TemporaryCursor()
    def runAssignShaders(self):
        """Assign shaders to the geometry."""
        from .maya.shaders import assignShaders

        namespace = assignShaders(self.getShaderPath(), namespace=self.getShaderNamespace(),
                                  shadingGroup=self.getShadingGroup())

        # Handle cases if namespace already exists
        if namespace != self.getShaderNamespace():
            self.nsInput.setText(namespace)

        # Update switch validation
        self.lsShaderSwitch()
        self.lsMaskSwitch()

    @TemporaryCursor()
    def runScaleBricks(self, scale):
        from .maya.utils import scaleObject
        for group in self.getBrickGroups():
            scaleObject(group, scale, xform=self.scaleXform.isChecked())

    @TemporaryCursor()
    def runApplyPalette(self):
        """Apply the palette colours to bricks."""
        from .maya.palette import applyPalette, setVertexColours

        applyPalette(self.getPalettePath())
        if self.vertexColours.isChecked():
            setVertexColours()

    @TemporaryCursor()
    def runDecals(self):
        """Load decals into the scene."""
        from .maya.decals import importDecals
        from .maya.decals2 import setupNodeNetwork, assignDecalShaders

        with TemporaryCursor(), UserExceptionList() as exc:
            nodeNetworkCreated = False
            if self.decalShadingNetwork.isChecked():
                try:
                    setupNodeNetwork(
                        doubleSided=self.decalDoubleSided.isChecked(),
                        stickers=self.decalStickers.isChecked(),
                        namespace=self.getShaderNamespace(),
                    )
                except UserWarningError as e:
                    exc.extend(e)
                else:
                    nodeNetworkCreated = True

            try:
                importDecals(self.getDecalPath(), shaderSwitch=self.getShaderSwitch(), maskSwitch=self.getMaskSwitch())
            except UserWarningError as e:
                exc.extend(e)

            if nodeNetworkCreated:
                try:
                    assignDecalShaders()
                except UserWarningError as e:
                    exc.extend(e)


if __name__ == '__main__':
    GUI.show()
