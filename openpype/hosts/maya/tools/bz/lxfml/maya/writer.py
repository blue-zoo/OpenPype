"""Export the data from a scene."""

import webbrowser
from collections import defaultdict
from itertools import count
from uuid import uuid4
from xml.dom import minidom
from xml.etree import ElementTree as ET

import maya.cmds as mc

from ..everything_else import UndoChunk


def isBasicallyZero(lst, tolerance=0.0001):
    """Find if all values in a list are 0 with some tolerance."""
    return all(-tolerance < item < tolerance for item in lst)


@UndoChunk()
def unfreezeTransform(mesh):
    """Undo the freeze transformation process."""
    pivot = mc.xform(mesh, query=True, rotatePivot=True, objectSpace=True)

    # Skip any local pivots set to 0
    if isBasicallyZero(pivot):
        return False
    if not isBasicallyZero(mc.xform(mesh, query=True, translation=True, worldSpace=True)):
        return False

    # Reverse the move and freeze the transform again
    mc.move(-pivot[0], -pivot[1], -pivot[2], mesh, relative=True)
    mc.makeIdentity(mesh, apply=True, translate=True, rotate=False, scale=False)
    mc.move(pivot[0], pivot[1], pivot[2], mesh, relative=True)
    return True


def getMatrix(node):
    """Get the transformation matrix from translate, rotate, and scale of a node."""
    unfrozen = unfreezeTransform(node)
    matrix = mc.xform(node, query=True, matrix=True, worldSpace=True)
    del matrix[15]
    del matrix[11]
    del matrix[7]
    del matrix[3]
    if unfrozen:
        mc.undo()
    return ','.join(map(str, matrix))


def getGroupBrickParts(group):
    """Find all the brick parts under a particular group."""
    return mc.ls('*|{}|*|*Part*.LEGO_colour'.format(group), objectsOnly=True, long=True)


def exportGroup(group, outputPath):
    """Export a group of bricks from a Maya scene.

    Note that this only supports rigid parts and is limited by what
    data exists in the Maya scene.

    Returns:
        True if successful.
    """
    root = ET.Element('LXFML', versionMajor='6', versionMinor='2', versionPatch='0')
    bricksElement = ET.SubElement(root, 'Bricks')
    ET.SubElement(root, 'RigidSystems')
    ET.SubElement(root, 'GroupSystems')

    # Group parts per brick
    brickParts = defaultdict(list)
    for part in getGroupBrickParts(group):
        brick = part.split('|')[-2]
        # If a part is duplicated, then instead of _PLY, it'll be _PLY1
        # Separate bricks by this number otherwise they won't import
        try:
            dupIdx = int(part[-1].rsplit('_PLY', 1)[-1]) + 1
        except ValueError:
            dupIdx = 1
        brickParts[(brick, dupIdx)].append(part)

    if not brickParts:
        mc.warning('Failed to find valid brick parts inside "{}"'.format(group))
        return False

    # Add an entry for each brick
    brickRefID = count()
    partRefID = count()
    boneRefID = count()
    for parts in brickParts.values():
        brickData = dict(
            designID=str(mc.getAttr(parts[0] + '.LEGO_designID')),
            uuid=str(uuid4()),
        )
        # Fake the brick data
        brickData['refID'] = str(next(brickRefID))
        brickData['itemNos'] = '302001'
        brickData['designID'] += ';A'

        brickElement = ET.SubElement(bricksElement, 'Brick', **brickData)

        for part in parts:
            partData = dict(
                designID=str(mc.getAttr(part + '.LEGO_designID')),
                partType='rigid',
                materials=str(mc.getAttr(part + '.LEGO_materialIDs')),
            )
            boneData = dict(
                transformation=getMatrix(part),
            )
            decoration = mc.getAttr(part + '.LEGO_decoration')
            if decoration:
                partData['decoration'] = decoration

            # Fake the part data
            partData['refID'] = str(next(partRefID))
            partData['designID'] += ';A'
            partData['materials'] += ':0'

            # Fake the bone data
            boneData['refID'] = str(next(boneRefID))

            partElement = ET.SubElement(brickElement, 'Part', **partData)
            ET.SubElement(partElement, 'Bone', **boneData)

    dom = minidom.parseString(ET.tostring(root, encoding='utf-8', method='xml'))
    with open(outputPath, 'w') as file:
        file.write(dom.toprettyxml(indent='  '))
    return True


def exportSelected():
    """Export the selected group to an LXFML file and ask the user where to save."""
    directory = mc.fileDialog2(fileMode=3, dialogStyle=1, caption='Select LXFML Export Directory')

    if not directory:
        mc.warning('Export cancelled by the user.')
        return

    groups = mc.ls(selection=True)
    if not groups:
        mc.warning('No groups selected. Please select one or more groups to export.')
        return
    successes = 0
    for node in groups:
        successes += exportGroup(node, directory[0] + '/{}.lxfml'.format(node.split('|')[-1]))

    if successes:
        print('Opening output folder...')
        webbrowser.open(directory[0])


if __name__ == '__main__':
    exportSelected()
