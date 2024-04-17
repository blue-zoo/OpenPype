from maya import cmds, mel

RUN_PLAYBLAST_CMD='''
from openpype.hosts.maya.tools.bz.playblast.ui import window;
from PySide2.QtWidgets import QApplication;
tool = window.show();
QApplication.processEvents();
tool.runPlayblast();
'''

RUN_PLAYBLAST_WINDOW_CMD='''
from openpype.hosts.maya.tools.bz.playblast.ui import window;
tool = window.show();
'''



# Add the playblaster to the timeslider menu
def putPlayblastToTimeSliderDeferred():
    """ Added the playblast command
        to the Timeline popup menu.
    """
    mel.eval('''updateTimeSliderMenu TimeSliderMenu''')
    if cmds.menuItem("bzPlayblastMenuitem",exists = 1):
        cmds.deleteUI("bzPlayblastMenuitem")

    if cmds.menuItem("bzPlayblastMenuitem_option",exists = 1):
        cmds.deleteUI("bzPlayblastMenuitem_option")

    # original
    cmds.menuItem("bzPlayblastMenuitem",
                label = "Blue-zoo Playblast...",
                command = RUN_PLAYBLAST_CMD,
                ia="timeSliderPlayblastOptionItem",
                p="TimeSliderMenu" )

    cmds.menuItem( "bzPlayblastMenuitem_option",
                optionBox = True,
                command = RUN_PLAYBLAST_WINDOW_CMD,
                ia= "bzPlayblastMenuitem" )


def addPlayblastMenu():
    """ Run the command for the playblast menu.
    """
    cmds.evalDeferred(putPlayblastToTimeSliderDeferred)
