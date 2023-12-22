"""Import decal files into the scene.

Rewrite of Arthur's decal code:
    Y:/LEGO/1686s_LegoCitySeries1/Libraries/Script_Library/lego_decals.py
"""

from __future__ import absolute_import, division

import logging
import os
import re
from collections import defaultdict

import maya.cmds as mc

from .utils import getSceneBricks
from ..exceptions import UserExceptionList


logger = logging.getLogger('lego-importer')


PLACE_2D_TO_FILE_ATTRS = dict(
    coverage='coverage',
	translateFrame='translateFrame',
	rotateFrame='rotateFrame',
	mirrorU='mirrorU',
	mirrorV='mirrorV',
	stagger='stagger',
	wrapU='wrapU',
	wrapV='wrapV',
	repeatUV='repeatUV',
	offset='offset',
	rotateUV='rotateUV',
	noiseUV='noiseUV',
	vertexUvOne='vertexUvOne',
	vertexUvTwo='vertexUvTwo',
	vertexUvThree='vertexUvThree',
	vertexCameraOne='vertexCameraOne',
	outUV='uv',
	outUvFilterSize='uvFilterSize',
)


def getDecalFiles(path):
    """Build a dict mapping the decal name to its path."""
    try:
        filenames = os.listdir(path)
    except OSError:
        filenames = []
    return {filename: os.path.join(path, filename + ext)
            for filename, ext in map(os.path.splitext, filenames) if ext == '.png'}


def getDecalNodes():
    """Build a dict containing each decal and which nodes contain it."""
    decals = defaultdict(list)
    for node in getSceneBricks():
        decal = mc.getAttr(node + '.LEGO_decoration').split(',')[0]
        if decal:
            decals[decal].append(node)
    return decals


def importDecal(filePath, uvSet=None, deleteExistingNodes=True):
    """Import a decal from a file path.

    Paramters:
        filePath (str): Path to directory containing decal images.
        uvSet (str, optional): Name of UV set to give to Redshift.
        deleteExistingNodes (bool): If existing nodes should be replaced.
            Defaults to True.

    Returns:
        Name of created file node.
    """
    decalNodeName = 'LEGO_DECAL_' + os.path.basename(os.path.splitext(filePath)[0])

    # Clean up existing file nodes
    if deleteExistingNodes:
        if mc.objExists(decalNodeName):
            logger.debug('Deleting node %s...', decalNodeName)
            mc.delete(decalNodeName)

    # Import texture file
    fileNode = mc.shadingNode('file', name=decalNodeName, asTexture=True, isColorManaged=True)
    mc.setAttr(fileNode + '.defaultColor', 0, 0, 0, type='double3')
    mc.setAttr(fileNode + '.fileTextureName', filePath, type='string')

    # Clean up existing place2dTexture nodes
    p2dNodeName = fileNode + '_place2dTexture'
    if deleteExistingNodes:
        if mc.objExists(p2dNodeName):
            logger.debug('Deleting node %s...', p2dNodeName)
            mc.delete(p2dNodeName)

    # Create 2D texture
    place2dNode = mc.shadingNode('place2dTexture', asUtility=True, name=p2dNodeName)
    if uvSet is not None:
        mc.setAttr(place2dNode + '.rsUvSet', uvSet, type='string')
        mc.setAttr(place2dNode + '.wrapU', 0)
        mc.setAttr(place2dNode + '.wrapV', 0)

    # Connect to texture file
    for place2dAttr, fileAttr, in PLACE_2D_TO_FILE_ATTRS.iteritems():
        mc.connectAttr(place2dNode + '.' + place2dAttr, fileNode + '.' + fileAttr)

    return fileNode


def importDecals(path, shaderSwitch, maskSwitch):
    """Import decals for the whole scene.

    Parameters:
        path (str): Path to directory containing decal images.
        shaderSwitch (str): Name of shader switch to connect to.
        maskSwitch (str): Name of mask switch to connect to.
    """
    # Convert the inputs into wildcards and ignore the input ranges
    shaderWildcard = replaceNumberRange(shaderSwitch)[0]
    if shaderWildcard.count('*') != 2:
        shaderWildcard = shaderSwitch

    maskWildcard = replaceNumberRange(maskSwitch)[0]
    if maskWildcard.count('*') != 2:
        maskWildcard = maskSwitch

    # Query the scene for any matching switches
    if '*' in shaderWildcard:
        shaderSwitches = getShaderRanges(shaderWildcard)
    else:
        shaderSwitches = {(None, None): shaderWildcard}
    if '*' in maskWildcard:
        maskSwitches = getShaderRanges(maskWildcard)
    else:
        maskSwitches = {(None, None): maskWildcard}

    # Warn if no matching switches found
    with UserExceptionList() as exc:
        if not shaderSwitches:
            exc.append('No shader switches found matching {!r}.'.format(shaderWildcard))
        if not maskSwitches:
            exc.append('No mask switches found matching {!r}.'.format(maskWildcard))

    decalFiles = getDecalFiles(path)
    with UserExceptionList() as exc:
        for i, (decal, nodes) in enumerate(getDecalNodes().items()):

            # Determine which switch to use
            switchStart = 10 * (i // 10)
            switchEnd = switchStart + 9

            try:
                shaderSwitch = shaderSwitches[(switchStart, switchEnd)]
            except KeyError:
                try:
                    shaderSwitch = shaderSwitches[(None, None)]
                except KeyError:
                    exc.append('No shader switch found for index {}.'.format(i))
                    continue

            try:
                maskSwitch = maskSwitches[(switchStart, switchEnd)]
            except KeyError:
                try:
                    maskSwitch = maskSwitches[(None, None)]
                except KeyError:
                    exc.append('No mask switch found for index {}.'.format(i))
                    continue

            try:
                filePath = decalFiles[decal.split(';')[0] + '_COL']
            except KeyError:
                logger.warning('No decal file found for %s', decal.split(';')[0])
            else:
                # Import the decal texture
                logger.info('Importing decal: %s', filePath)
                decalNode = importDecal(filePath, uvSet=decal.split(';')[1].split(':')[-1])
                logger.debug('Created decal node: %s', decalNode)

                # Connect to the Switch nodes
                shaderSlot = i % 10
                logger.info('Connecting decal to shader slot: %s', shaderSlot)
                mc.connectAttr(decalNode+'.outColor', shaderSwitch + '.shader{}'.format(shaderSlot), force=True)
                mc.connectAttr(decalNode+'.outAlpha', maskSwitch + '.shader{}R'.format(shaderSlot), force=True)
                mc.connectAttr(decalNode+'.outAlpha', maskSwitch + '.shader{}G'.format(shaderSlot), force=True)
                mc.connectAttr(decalNode+'.outAlpha', maskSwitch + '.shader{}B'.format(shaderSlot), force=True)

            # Set decal attributes on nodes
            for node in nodes:
                mc.setAttr(node + '.LEGO_decal', 1)
                mc.setAttr(node + '.LEGO_decalNumber', i)
            logger.info('Nodes affected: %s', ', '.join(nodes))


def replaceNumberRange(txt):
    """Given text with a min and max number, return the text without a number and the range."""
    numbers = []
    for match in reversed(list(re.finditer('([0-9]+)', txt))):
        idx = match.start()
        val = match.group(1)
        txt = txt[:idx] + '*' + txt[idx + len(val):]
        numbers.append(int(val))
    numbers.reverse()
    return txt, numbers


def getShaderRanges(search):
    """Get the min/max values of all matching shaders in the scene."""
    result = {}
    for shader in mc.ls(search, exactType='RedshiftShaderSwitch'):
        shaderRange = replaceNumberRange(shader)[1]
        result[tuple(shaderRange)] = shader
    return result
