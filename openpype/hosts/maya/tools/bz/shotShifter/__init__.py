
import maya.cmds as mc

from qtpy import QtWidgets, QtCore
from ..vfxwindow import VFXWindow



import maya.cmds as mc

class MayaFrameRange():
    @property
    def max(self):
        return mc.playbackOptions(q=True, max = True)
    @property
    def min(self):
        return mc.playbackOptions(q=True, min = True)
    @property
    def start(self):
        return mc.playbackOptions(q=True, animationStartTime = True)
    @property
    def end(self):
        return mc.playbackOptions(q=True, animationEndTime = True)
    @property
    def current(self):
        return mc.currentTime(q=True)

    def checkStartEqual(self, val=None):
        if val is None:
            return self.start == self.min
        else:
            return self.start == self.min == val

    def checkEndEqual(self, val=None):
        if val is None:
            return self.end == self.max
        else:
            return self.end == self.max == val

    def setCurrentFrame(self, val):
        mc.currentTime(val, edit=True)

    def setMax(self, val):
        return mc.playbackOptions(max = val)

    def setMin(self, val):
        return mc.playbackOptions(min = val)

    def setStart(self, val):
        return mc.playbackOptions(animationStartTime = val)

    def setEnd(self, val):
        return mc.playbackOptions(animationEndTime = val)

    def trimStart(self):
        self.setStart(self.min)

    def trimEnd(self):
        self.setEnd(self.max)

    def extendMin(self):
        self.setMin(self.start)

    def extendMax(self):
        self.setMax(self.end)


    @property
    def innerRange(self):
        return self.max - self.min

    @property
    def outerRange(self):
        return self.end - self.start


def offsetAudio(audioNode, offset, sourceEnd):
    offsetUpdated = False
    currentOffset = mc.getAttr(audioNode + '.offset')
    if currentOffset != offset:
        offsetUpdated = True
        mc.setAttr(audioNode + '.offset', offset)
    # Update the sequencer source end
    if sourceEnd is not None:
        mc.setAttr(audioNode + '.sourceEnd', sourceEnd- offset +1)
    return offsetUpdated

class FrameNumSpinBox(QtWidgets.QDoubleSpinBox):
    """Modified spinbox to hold frame numbers. Allow subframes via right click menu or by force setValue.
    """
    def __init__(self, *args, **kwargs):
        super(FrameNumSpinBox, self).__init__(*args, **kwargs)
        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.setDecimals(0)
        self.setPrefix("Frame ")
        self.setRange(0, 100000)

    def setSubframes(self, val):
        if isinstance(val, bool):
            if val == True:
                self.setDecimals(4)
                return
            elif val == False:
                self.setDecimals(0)
                return

        mod = val%10
        if mod == 0:
            self.setDecimals(0)
        else:
            self.setDecimals(len(str(mod))-2)

    def contextMenuEvent(self, event):
        QtCore.QTimer.singleShot(0, self.addAction)
        super(FrameNumSpinBox, self).contextMenuEvent(event)

    def setValue(self, val):
        self.setSubframes(val)
        if val < self.minimum():
            self.setMinimum(val)
        super(FrameNumSpinBox, self).setValue(val)


    @QtCore.Slot()
    def addAction(self):
        editMenu = self.findChild(QtWidgets.QMenu, 'qt_edit_menu')
        editMenu.addSeparator()
        menuItem = QtWidgets.QAction('Allow subframes', editMenu, checkable=True)
        editMenu.addAction(menuItem)
        if self.decimals() != 0:
            menuItem.setChecked(True)
        menuItem.toggled.connect(self.setSubframes)



def offsetCurves(offset):
    error = False
    for curve in mc.ls(type='animCurve'):
        try:
            mc.keyframe(curve, edit=True,r=True,timeChange=offset)
        except RuntimeError as e:
            print("Could not move curve {}  {}".format(curve, e))
            error = True
            pass
    if error:
        mc.confirmDialog(title='Error',
                button=['Ok'],
                icon='critical',
                message='Errors encountered Shifting, see script editor for details...')


def shiftShot(shiftCurves, shiftAudio, newStart, newEnd, offset):
        if shiftCurves:
            offsetCurves(offset)
        if shiftAudio:
            for audioNode in mc.ls(exactType='audio'):
                currentOffset = mc.getAttr(audioNode + '.offset')
                offsetAudio(audioNode, currentOffset+offset, sourceEnd=newEnd)

        framerange = MayaFrameRange()
        framerange.setMin(newStart)
        framerange.setStart(newStart)
        framerange.setMax(newEnd)
        framerange.setEnd(newEnd)
        framerange.setCurrentFrame(framerange.current + offset)


class ShotShifterUI(VFXWindow):
    """UI for Shot Shifter
    """
    WindowID = '"BZShotShifter'
    WindowName = 'BZShotShifter'
    WindowDockable= True

    def __init__(self, **kwargs):
        super(ShotShifterUI, self).__init__(**kwargs)
        self.framerange = MayaFrameRange()

        self.docsbutton = QtWidgets.QPushButton('Documentation')
        self.refreshButton = QtWidgets.QPushButton('Refresh FrameNumbers')
        self.runButton = QtWidgets.QPushButton('')
        self.warninglabel = QtWidgets.QLabel('WARNING:\nDo Not shift the animation if the shot has already been sent to edit.')

        self.originalStartBox = FrameNumSpinBox()
        self.originalEndBox =  FrameNumSpinBox()
        self.originalEndBox.setEnabled(False)
        self.newStartBox = FrameNumSpinBox()
        self.newStartBox.setValue(100)
        self.newEndBox = FrameNumSpinBox()
        self.newEndBox.setEnabled(False)

        self.shiftAudio = QtWidgets.QCheckBox('Shift Audio')
        self.shiftAudio.setChecked(True)
        self.shiftCurves = QtWidgets.QCheckBox('Shift Animation Keyframes')
        self.shiftCurves.setChecked(True)

        gridLayout = QtWidgets.QGridLayout()

        main = QtWidgets.QWidget()
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(QtWidgets.QLabel("Original Start"),0,0)
        gridLayout.addWidget(self.originalStartBox,1,0)
        gridLayout.addWidget(QtWidgets.QLabel("Original End"),0,1)
        gridLayout.addWidget(self.originalEndBox,1,1)

        gridLayout.addWidget(QtWidgets.QLabel("New Start"),2,0)
        gridLayout.addWidget(self.newStartBox,3,0)
        gridLayout.addWidget(QtWidgets.QLabel("New End"),2,1)
        gridLayout.addWidget(self.newEndBox,3,1)

        self.newStartBox.valueChanged.connect(self.updateRunText)
        self.originalStartBox.valueChanged.connect(self.updateRunText)
        self.refreshButton.clicked.connect(self.refreshFrameNumbers)
        self.docsbutton.clicked.connect(self.docs)
        self.runButton.clicked.connect(self.run)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.docsbutton)
        layout.addWidget(self.refreshButton)
        layout.addLayout(gridLayout)
        layout.addWidget(self.shiftAudio)
        layout.addWidget(self.shiftCurves)
        layout.addWidget(self.warninglabel)
        layout.addWidget(self.runButton)

        main.setLayout(layout)
        self.setCentralWidget(main)

        self.refreshFrameNumbers()
        self.updateRunText()

        self.show()

    def docs(self):
        mc.confirmDialog(title='Shot Shifter',
                button=['Ok'],
                message="This tool offsets Keyframes and/or audio along the timeline. \n\nSet a new start frame, and click the 'Shift' button.\n\nTo use sub frames, right-click the frame number box and select 'Allow subframes'\n\n The Original start/end will be taken from the timeline.\nIf the timeline is updated, click the Refresh button.\n\nThis tool will not stretch the animation, so the end times are used as an indication only and cannot be modified.")

    def refreshFrameNumbers(self):
        self.originalStartBox.setValue(self.framerange.min)
        self.originalEndBox.setValue(self.framerange.max)
        self.setNewEnd()

    def setNewEnd(self):
        offset = self.getOffset()
        self.newEndBox.setValue(self.originalEndBox.value()+offset)


    def getOffset(self):
        return self.newStartBox.value() - self.originalStartBox.value()

    def updateRunText(self):
        offset = self.getOffset()
        self.runButton.setText('Shift {:+.6g} frames'.format(offset))
        self.setNewEnd()


    def run(self):
        offset = self.getOffset()
        shiftCurves =  self.shiftCurves.isChecked()
        shiftAudio = self.shiftAudio.isChecked()
        newStart = self.newStartBox.value()
        newEnd = self.newEndBox.value()
        shiftShot(shiftCurves, shiftAudio, newStart, newEnd, offset)
        self.refreshFrameNumbers()

if __name__ == '__main__':
    ShotShifterUI()
