from __future__ import absolute_import

import logging
import os
import re
import webbrowser

from Qt import QtCompat, QtCore, QtWidgets
from ..vfxwindow import VFXWindow

from .everything_else import TemporaryCursor
from .exceptions import UserWarningError, UserExceptionList


logger = logging.getLogger('lego-importer')


def _clean_input(path):
    """Strip the edges of inputs to return just the string."""
    return path.strip('-\'" \n')


class GUI(VFXWindow):
    WindowID = 'bz.lego.importer'
    WindowName = 'LEGO Importer'
    WindowDockable = False

    def __init__(self, parent=None, **kwargs):
        super(GUI, self).__init__(parent=parent, **kwargs)
        self.setWindowPalette('maya')
        QtCompat.loadUi(os.path.join(os.path.dirname(__file__), 'layout.ui'), self)

        self.xmlPath.setPlaceholderText(r'Y:\LEGO\1828s_LegoCitySeries2\Libraries\Model_Library\_importingTestA\legoExample.lxfml')
        self.geoPath.setPlaceholderText(r'Y:\LEGO\1828s_LegoCitySeries2\Libraries\Model_Library\_legoLibrary\High_processed\m')
        self.shdPath.setPlaceholderText(r'Y:\LEGO\1828s_LegoCitySeries2\Libraries\Shader_Library\shaders\master\published\master_shader.ma')
        self.palettePath.setPlaceholderText(r'Y:\LEGO\1828s_LegoCitySeries2\Libraries\Shader_Library\Color_ID_List_BZ.json')
        self.decalPath.setPlaceholderText(r'Y:\LEGO\1828s_LegoCitySeries2\Libraries\Texture_Library\Decorations')

        self.menuClose.triggered.connect(self.close)
        self.menuDocs.triggered.connect(lambda: webbrowser.open('https://sites.google.com/blue-zoo.co.uk/software-tools-workflow/software-tools-workflow-home-page/software/maya/blue-zoo-maya-tools/lego-importer'))

        self.xmlOpen.setIconPath('icons/SP_DirOpenIcon.png')
        self.geoOpen.setIconPath('icons/SP_DirOpenIcon.png')
        self.shdOpen.setIconPath('icons/SP_DirOpenIcon.png')
        self.paletteOpen.setIconPath('icons/SP_DirOpenIcon.png')
        self.decalOpen.setIconPath('icons/SP_DirOpenIcon.png')
        self.shaderSwitchValid.setIconPath('icons/valid.png')
        self.shaderSwitchInvalid.setIconPath('icons/invalid.png')
        self.maskSwitchValid.setIconPath('icons/valid.png')
        self.maskSwitchInvalid.setIconPath('icons/invalid.png')

        self.xmlOpen.clicked.connect(self.chooseXmlFile)
        self.geoOpen.clicked.connect(self.chooseGeoFile)
        self.shdOpen.clicked.connect(self.chooseShaderFile)
        self.paletteOpen.clicked.connect(self.choosePaletteFile)

        self.nsInput.textChanged.connect(self.lsShaderSwitch)
        self.switchInput.textChanged.connect(self.lsShaderSwitch)
        self.decalShadingNetwork.toggled.connect(self.lsShaderSwitch)
        self.lsShaderSwitch()
        self.nsInput.textChanged.connect(self.lsMaskSwitch)
        self.maskInput.textChanged.connect(self.lsMaskSwitch)
        self.decalShadingNetwork.toggled.connect(self.lsMaskSwitch)
        self.lsMaskSwitch()

        self.runImport.clicked.connect(self.importAll)

    def getXmlPath(self):
        """Get the path to the XML file."""
        return _clean_input(self.xmlPath.text() or self.xmlPath.placeholderText())

    def getGeoPath(self):
        """Get the path to the geometry folder."""
        geoPath = _clean_input(self.geoPath.text() or self.geoPath.placeholderText())
        geoExt = _clean_input(self.geoExt.text() or self.geoExt.placeholderText())
        if os.path.isdir(geoPath) and geoPath[-1] != os.path.sep:
            geoPath += os.path.sep
        return geoPath + '*' + geoExt

    def getShaderPath(self):
        """Get the path to the shader file."""
        return _clean_input(self.shdPath.text() or self.shdPath.placeholderText())

    def getBrickGroup(self):
        """Get the name to give to the brick group."""
        return _clean_input(self.geoParent.text() or self.geoParent.placeholderText())

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

    @QtCore.Slot()
    def chooseXmlFile(self):
        """Prompt the user to choose an XML file."""
        filePath = self._openFile('Select LEGO XML File', self.getXmlPath(), 'LEGO XML Files (*.xml *.lxfml)')
        self.xmlPath.setText(filePath)

    @QtCore.Slot()
    def chooseGeoFile(self):
        """Prompt the user to choose a geometry file.

        This will determine the filename format based on the brick ID.
        In case of multiple numbers in the filename, the longest will be chosen.
        """
        filePath = self._openFile('Select (any) LEGO Geometry File', self.getGeoPath(),
                                  'LEGO Geometry Files (*.ma *.mb *.obj)')
        if not filePath:
            return

        # Separate out the brick ID
        fileDir = os.path.dirname(filePath)
        fileName, fileExt = os.path.splitext(os.path.basename(filePath))
        fileNameInts = re.findall(r'\d+', fileName)
        if not fileNameInts:
            logger.warning('Unable to detect brick ID in file path.')
            return
        brickID = max(fileNameInts, key=len)

        # Set the path
        wildcardPath = os.path.join(fileDir, fileName.replace(brickID, '*') + fileExt)
        pathStart, pathEnd = wildcardPath.split('*')
        self.geoPath.setText(pathStart)
        self.geoExt.setText(pathEnd)

    @QtCore.Slot()
    def chooseShaderFile(self):
        """Prompt the user to choose a shader file."""
        filePath = self._openFile('Select LEGO Shader File', self.getShaderPath(), 'LEGO Shader Files (*.ma *.mb)')
        self.shdPath.setText(filePath)

    @QtCore.Slot()
    def choosePaletteFile(self):
        """Prompt the user to choose a shader file."""
        filePath = self._openFile('Select LEGO Palette File', self.getPalettePath(), 'LEGO Palette Files (*.json)')
        self.palettePath.setText(filePath)

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
        if self.geoGrp.isChecked():
            try:
                self.runImportGeo()
            except UserWarningError as e:
                failed.extend(e)
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

    @TemporaryCursor()
    def runImportGeo(self):
        """Import the brick geometry."""
        from .maya.geometry import setupScene, BrickDirectory

        setupScene(
            self.getXmlPath(),
            BrickDirectory(self.getGeoPath(), group=self.getBrickGroup()),
            updateUVs=self.updateUVs.isChecked(),
            deleteColourSets=self.deleteColourSets.isChecked(),
            deleteHistory=self.deleteHistory.isChecked(),
            updateDisplayEdges=self.updateDisplayEdges.isChecked(),
            setTexelDensity=self.setTexelDensity.isChecked(),
            softenEdges=self.softenEdges.isChecked(),
            updateDisplayColourChannel=self.updateDisplayColourChannel.isChecked(),
            shaderNamespace=self.getShaderNamespace(),
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
