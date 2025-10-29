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
            materialIDs = mc.getAttr(brick + '.LEGO_materialIDs')
        except ValueError:
            continue
        materialID = int(materialIDs.split(',')[0])
        colourData = palette.colour(materialID)
        if colourData is None:
            continue

        # Set the RGB values to the custom BZ colour values
        colour = colourData.bzColour
        mc.setAttr(brick + '.LEGO_colourR', colour.r / 255)
        mc.setAttr(brick + '.LEGO_colourG', colour.g / 255)
        mc.setAttr(brick + '.LEGO_colourB', colour.b / 255)

        # Set material class and type
        if mc.getAttr(brick + '.LEGO_designID') in RUBBER_BRICKS:
            mc.setAttr(brick + '.LEGO_materialClass', 2)
            mc.setAttr(brick + '.LEGO_materialType', 0)
        elif colourData.isRefractive:
            mc.setAttr(brick + '.LEGO_materialClass', 3)
            mc.setAttr(brick + '.LEGO_materialType', 0)
        elif colourData.isMetallic:
            mc.setAttr(brick + '.LEGO_materialClass', 4)
            nameParts = colourData.name.split('_')
            if 'Chrome' in nameParts:
                mc.setAttr(brick + '.LEGO_materialType', 1)
            elif 'Ink' in nameParts:
                mc.setAttr(brick + '.LEGO_materialType', 2)
            else:
                mc.setAttr(brick + '.LEGO_materialType', 0)
        else:
            mc.setAttr(brick + '.LEGO_materialClass', 0)
            mc.setAttr(brick + '.LEGO_materialType', 0)


def _setVertexColours(node, colourOverride=None, colourSetName='LEGO_colourSet'):
    """Set vertex colours on a brick."""
    # Skip for locators
    if isBrickALocator(node):
        return

    # Read the colour from the existing attributes
    if colourOverride is None:
        r = mc.getAttr(node + '.LEGO_colourR')
        g = mc.getAttr(node + '.LEGO_colourG')
        b = mc.getAttr(node + '.LEGO_colourB')
    else:
        r, g, b = colourOverride

    # Create or get the set
    for childNode in getDescendants(node, nodeType='transform'):
        colourSets = mc.polyColorSet(childNode, currentPerInstanceSet=True, query=True) or ()
        for colourSet in colourSets:
            if colourSetName in colourSet:
                mc.polyColorSet(childNode, currentColorSet=True, colorSet=colourSet)
                break
        else:
            mc.polyColorSet(childNode, create=True, colorSet=colourSetName, unshared=True, perInstance=True)
            mc.polyColorSet(childNode, currentColorSet=True, colorSet=colourSetName)

        # Set the vertex colours
        mc.polyColorPerVertex(childNode, r=r, g=g, b=b, a=1, colorDisplayOption=True)


def setVertexColours(colourSetName='LEGO_colourSet'):
    """Set vertex colours on all bricks."""
    for brick in getSceneBricks():
        r = mc.getAttr(brick + '.LEGO_colourR')
        g = mc.getAttr(brick + '.LEGO_colourG')
        b = mc.getAttr(brick + '.LEGO_colourB')
        for childBrick in getDescendants(brick, nodeType='transform'):
            _setVertexColours(childBrick, colourOverride=(r, g, b), colourSetName=colourSetName)
