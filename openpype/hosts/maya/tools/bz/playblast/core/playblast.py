import importlib
import datetime
from maya import cmds
from maya import mel
import tempfile
import os
from openpype.hosts.maya.tools.bz.playblast.core import ffmpeg
from openpype.hosts.maya.tools.bz.playblast.core import timecode
from openpype.hosts.maya.tools.bz.playblast.ui import window
from openpype.hosts.maya.tools.bz.playblast.core import utils

importlib.reload(ffmpeg)
importlib.reload(timecode)
importlib.reload(utils)

EXTENSION = ".mov"

def getTimeCodeForFrame(frame):
    fps = mel.eval('float $fps = `currentTimeUnitToFPS`')
    tc = timecode.Timecode(str(int(fps)), '00:00:00:00')
    tc.frames = frame
    return str(tc)

def playblast(

    startTime = None,
    endTime = None,
    width = None,
    height = None,
    editor = None,
    camera = None,
    comment = None,
    outputFile = None
    ):


    tempFile = tempfile.NamedTemporaryFile(delete=False,suffix=EXTENSION)
    tempFileName = tempFile.name
    tempFileSafe = tempFile.name.replace("\\","/")

    # CameraName
    cmds.modelEditor(editor,e=1,camera=camera)
    cmds.setFocus(editor)
    # Datetime string
    date = str(datetime.datetime.now()).split(".")[:1][0].replace(":","\\\:")

    kwargs =  {"filename"      : tempFileSafe,
                "fmt"          : "qt",
                "wh"           : [width,height],
                "st"           : startTime,
                "et"           : endTime,
                "showOrnaments": False,
                "percent"      : 100,
                "quality"      : 100,
                "compression"  : "Lagarith",
                "epn"          :  editor,
                "fo"           :  True,
                "v"            :  False
                    }

    # If there is audio in the timeline
    audio = utils.getCurrentAudioNode()
    if audio:
        kwargs["sound"] = audio
    cmds.playblast( **kwargs
                    )

    # Playblast got interupted, take last visited frame -1
    if endTime != window.LAST_PLAYBLASTED_FRAME:
        endTime = window.LAST_PLAYBLASTED_FRAME -1

    timeCode = getTimeCodeForFrame(startTime)
    focalLength = '{f}mm'.format(f=int(cmds.getAttr(camera+".focalLength")))

    user = os.environ.get( "USERNAME" )

    ffmpeg.convert(
        inputFile = tempFileName,
        outputFile = outputFile,
        timecode = timeCode,
        offset = startTime,
        duration = endTime-startTime+1,
        focalLength = focalLength,
        user= user,
        datetime = date,
        comment = comment
    )
    if os.path.isfile(outputFile):
        return outputFile
