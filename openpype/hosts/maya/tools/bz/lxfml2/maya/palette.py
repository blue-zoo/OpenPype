import logging

import maya.cmds as mc

from .utils import getSceneBricks, isBrickALocator
from ..everything_else import getDescendants
from ..colour import ColourPalette


logger = logging.getLogger('lego-importer')

RUBBER_BRICKS = [59895, 87414, 50951, 30028, 92409, 87697, 61254, 56890, 11209, 18977, 30648, 58090,
                 92402, 35578, 30699, 56898, 56891, 55978, 70490, 44309, 15413, 70695, 55976, 50861]


def applyPalette(path=None):
    """Read the palette file and set attributes."""
    palette = ColourPalette(path)
    for brick in getSceneBricks():
        # Get the palette colour from the material ID
        # Use only the first material ID value
        try:
            materialID = mc.getAttr(brick + '.LEGO_materialID')
        except ValueError:
            continue
        colourData = palette.colour(materialID)
        if colourData is None:
            continue

        # Set the RGB values to the custom BZ colour values
        colour = colourData.bzColour
        mc.setAttr(brick + '.LEGO_colourR', colour.r / 255)
        mc.setAttr(brick + '.LEGO_colourG', colour.g / 255)
        mc.setAttr(brick + '.LEGO_colourB', colour.b / 255)

        # Set material class and type
        materialType = 0
        materialClass = 0
        if mc.getAttr(brick + '.LEGO_designID') in RUBBER_BRICKS:
            materialType = 5
        elif colourData.isTransparent:
            materialType = 1
        elif colourData.isMetallic:
            materialType = 2
            nameParts = colourData.name.split('_')
            if 'Chrome' in nameParts:
                materialClass = 2
            else:
                materialClass = 0
            if materialID in (335, 336, 337, 344):
                materialClass = 1
        elif colourData.isGlitter:
            materialType = 3
        elif colourData.isOpalescent:
            materialType = 4
        mc.setAttr(brick + '.LEGO_materialClass', materialClass)
        mc.setAttr(brick + '.LEGO_materialType', materialType)


def _setVertexColours(node, colourOverride=None, colourSetName='LEGO_colourSet'):
    """Set vertex colours on a brick."""
    # Skip for locators
    try:
        if isBrickALocator(node):
            return
    except TypeError:
        return

    # Read the colour from the existing attributes
    if colourOverride is None:
        r = mc.getAttr(node + '.LEGO_colourR')
        g = mc.getAttr(node + '.LEGO_colourG')
        b = mc.getAttr(node + '.LEGO_colourB')
    else:
        r, g, b = colourOverride

    allMeshes = getDescendants(node, nodeType='mesh')
    allMeshTransforms = mc.listRelatives(allMeshes, parent=True, fullPath=True) or []

    # Create or get the set
    for childNode in allMeshTransforms:
        colourSets = mc.polyColorSet(childNode, currentPerInstanceSet=True, query=True) or []
        for colourSet in colourSets:
            if colourSetName in colourSet:
                mc.polyColorSet(childNode, currentColorSet=True, colorSet=colourSet)
                break
        else:
            mc.polyColorSet(childNode, create=True, colorSet=colourSetName, unshared=True, perInstance=True)
            mc.polyColorSet(childNode, currentColorSet=True, colorSet=colourSetName)

        try:
            mc.polyColorPerVertex(childNode, r=r, g=g, b=b, a=1, colorDisplayOption=True)
        except RuntimeError as e:
            raise RuntimeError('{}: {}'.format(childNode, e))


def setVertexColours(colourSetName='LEGO_colourSet'):
    """Set vertex colours on all bricks."""
    for brick in getSceneBricks():
        r = mc.getAttr(brick + '.LEGO_colourR')
        g = mc.getAttr(brick + '.LEGO_colourG')
        b = mc.getAttr(brick + '.LEGO_colourB')
        for childBrick in getDescendants(brick, nodeType='transform'):
            _setVertexColours(childBrick, colourOverride=(r, g, b), colourSetName=colourSetName)
