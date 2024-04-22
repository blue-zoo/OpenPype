import re

from openpype.hosts.maya.tools.bz import shotgrid
import importlib
importlib.reload(shotgrid)



import os

from maya import cmds
from maya import mel

from openpype.pipeline import (
    get_current_asset_name,
    get_current_project_name,
    Anatomy
)
from ayon_api import (
    get_folder_by_name,
    get_folder_by_path,
)

SHOT_AUDIO_NODE_NAME = "SHOT_AUDIO"
EPISODE_AUDIO_NODE_NAME = "EPISODE_AUDIO"

def getShotId():
    projectName = get_current_project_name()
    folderPath = get_current_asset_name()

    if "/" in folderPath:
        currentFolder = get_folder_by_path(projectName, folderPath)
    else:
        currentFolder = get_folder_by_name(
            projectName, folder_name=folderPath
        )
    shotId = currentFolder["id"]

    return shotId

def notify(message):
    cmds.confirmDialog( title='Audio Updated', message=message.replace("\\","/"), button=['Yes'], defaultButton='Yes', cancelButton='No', dismissString='No' )

def displayMessage(message):
    cmds.warning(message)
    cmds.headsUpMessage( message )


def loadShotAudio():
    message = ""
    connection = shotgrid.getConnection()
    shotId = getShotId()
    shots = connection.find("Shot",[["sg_ayon_id","is",shotId]],["sg_sequence_in","sg_shot_audio_path","sg_cut_in","sg_sequence.Sequence.sg_episode_audio_file"])

    if not shots:
        displayMessage("Could not find Shot On Shotgrid for Id {id}".format(id=shotId))
        return
    if len(shots) != 1:
        displayMessage("Multiple shots on  Shotgrid for Id {id}".format(id=shotId))
        return

    shot = shots[0]

    # Start frame
    sequenceIn = shot.get("sg_sequence_in",False)

    # shot start frame
    cutIn = shot.get("sg_cut_in",100)

    # Episode Audio Path
    shotgridEpisodeAudioPath = False
    if shot.get("sg_sequence.Sequence.sg_episode_audio_file",False):
        shotgridEpisodeAudioPath=shot.get("sg_sequence.Sequence.sg_episode_audio_file",False)
        shotgridEpisodeAudioPath = shotgridEpisodeAudioPath["local_path_windows"]

    if not shotgridEpisodeAudioPath:
        displayMessage("Could not Find Episode Audio on shotgrid for Id {id}".format(id=shotId))
        return

    episodeAudioPath = os.path.normpath(shotgridEpisodeAudioPath)
    if not os.path.isfile(episodeAudioPath):
        displayMessage("Could not Find Episode Audio {id}".format(id=episodeAudioPath))
        return

    # Shot Audio Path
    shotgridAudioPath = shot.get("sg_shot_audio_path",False)
    if not shotgridAudioPath:

        displayMessage("Could not Find Shot Audio on shotgrid for Id {id}".format(id=shotId))
        return


    shotAudioPath = os.path.normpath(shotgridAudioPath)
    if not os.path.isfile(shotAudioPath):
        displayMessage("Could not Find Shot Audio {id}".format(id=shotAudioPath))
        return

    # Get Frame
    _path, _file = os.path.split(shotAudioPath)
    startRegex = re.search(r"(?<=fStart_)[0-9]{1,}",_file)
    endRegex = re.search(r"(?<=fEnd_)[0-9]{1,}",_file)
    startFrame = None
    endFrame = None
    if startRegex:
        startFrame = int(startRegex.group())

    if endRegex:
        endFrame = int(endRegex.group())

    if not endFrame or not startFrame:
        displayMessage("Unable to determine start of end frame in file {id}".format(id=shotAudioPath))
        return

    # find  / makde shot nodes
    soundNodes = cmds.ls(et="audio")
    if startFrame == None:
        startFrame = cmds.playbackOptions(query=True, min=True)

    if not SHOT_AUDIO_NODE_NAME in soundNodes:
        cmds.createNode("audio",ss=True,name=SHOT_AUDIO_NODE_NAME)
        cmds.setAttr("{}.filename".format(SHOT_AUDIO_NODE_NAME),shotAudioPath,type="string")

    else:
        old = cmds.getAttr("{}.filename".format(SHOT_AUDIO_NODE_NAME))

        cmds.setAttr("{}.filename".format(SHOT_AUDIO_NODE_NAME),shotAudioPath,type="string")
        if os.path.normpath(old) != shotAudioPath:
            message+= "Shot Audio updated to \n{a}\n".format(a=shotAudioPath)

    # Update the offset
    cmds.setAttr("{}.offset".format(SHOT_AUDIO_NODE_NAME), startFrame )

    # Update info
    audioFrameCount = cmds.getAttr("{}.frameCount".format(SHOT_AUDIO_NODE_NAME))
    audioSampleRate = cmds.getAttr("{}.sampleRate".format(SHOT_AUDIO_NODE_NAME))
    durationSeconds = audioFrameCount / audioSampleRate
    fps = mel.eval('currentTimeUnitToFPS()')  # workfile FPS
    sourceStart = 0
    sourceEnd = (durationSeconds * fps)
    cmds.setAttr("{}.sourceStart".format(SHOT_AUDIO_NODE_NAME), sourceStart)
    cmds.setAttr("{}.sourceEnd".format(SHOT_AUDIO_NODE_NAME), sourceEnd)

    cmds.timeControl(
        mel.eval("$gPlayBackSlider=$gPlayBackSlider"),
        edit=True,
        sound=SHOT_AUDIO_NODE_NAME,
        displaySound=True
    )

    if episodeAudioPath:
        soundNodes = cmds.ls(et="audio")

        if not EPISODE_AUDIO_NODE_NAME in soundNodes:
            cmds.createNode("audio",ss=True,name=EPISODE_AUDIO_NODE_NAME)
            cmds.setAttr("{}.filename".format(EPISODE_AUDIO_NODE_NAME),episodeAudioPath,type="string")

        else:
            old = cmds.getAttr("{}.filename".format(EPISODE_AUDIO_NODE_NAME))
            cmds.setAttr("{}.filename".format(EPISODE_AUDIO_NODE_NAME),episodeAudioPath,type="string")

            if os.path.normpath(old) != episodeAudioPath:
                message+= "\nEpisode Audio updated to \n{a}\n".format(a=episodeAudioPath)


        episodeOffset = sequenceIn+cutIn
        if sequenceIn:
            cmds.setAttr("{}.offset".format(EPISODE_AUDIO_NODE_NAME),episodeOffset  )

        audioFrameCount = cmds.getAttr("{}.frameCount".format(EPISODE_AUDIO_NODE_NAME))
        audioSampleRate = cmds.getAttr("{}.sampleRate".format(EPISODE_AUDIO_NODE_NAME))
        durationSeconds = audioFrameCount / audioSampleRate
        sourceStart = 0
        sourceEnd = (durationSeconds * fps)
        cmds.setAttr("{}.sourceStart".format(EPISODE_AUDIO_NODE_NAME), sourceStart)
        cmds.setAttr("{}.sourceEnd".format(EPISODE_AUDIO_NODE_NAME), sourceEnd)

    if message != "":
        notify(message)
