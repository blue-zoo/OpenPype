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


def getCurrentAudioNode():
    aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
    node = cmds.timeControl( aPlayBackSliderPython, q=True, sound=True, displaySound=True )
    if node in [None,[],""]:
        return None
    else:
        return node

def getAyonShotAttributes():
    projectName = get_current_project_name()
    folderPath = get_current_asset_name()

    if "/" in folderPath:
        print(folderPath)
        currentFolder = get_folder_by_path(projectName, folderPath)
    else:
        currentFolder = get_folder_by_name(
            projectName, folder_name=folderPath
        )
    startFrame = currentFolder['attrib']['frameStart']
    endFrame = currentFolder['attrib']['frameEnd']
    entityName = currentFolder['name']
    resolutionX = currentFolder['attrib']['resolutionWidth']
    resolutionY = currentFolder['attrib']['resolutionHeight']

    import pprint
    pprint.pprint(currentFolder)
    return entityName, startFrame, endFrame, resolutionX, resolutionY


def getMayaShotAttributes():
    startFrame = cmds.playbackOptions(q=1,minTime=1)
    endFrame  = cmds.playbackOptions(q=1,maxTime=1)
    return startFrame, endFrame

def getRenderableCamera():
    cameras = cmds.ls(cameras=True)
    renderableCameras = [c for c in cameras if cmds.getAttr(c+".renderable")]
    if renderableCameras:
        return renderableCameras[0]
    else:
        return cameras[0]

def getVideoRoot():
    # set name of comment
    anatomy = Anatomy()
    videoRoot = anatomy.roots['videoRoot'].value
    print(videoRoot)

    folderPath = get_current_asset_name()
    folders = folderPath.split("/")
    print(folders)
    _path = os.path.join(str(videoRoot),folders[1],folders[2],"Playblasts","WIP")
    return os.path.normpath(_path)
