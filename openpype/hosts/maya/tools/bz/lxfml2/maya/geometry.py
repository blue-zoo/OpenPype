import logging
import os
import random
from collections import defaultdict
from uuid import uuid4, UUID

import maya.cmds as mc
import maya.mel as mel

from .common_parts import run_style_update
from .utils import isBrickALocator
from .rename import renameSceneObjects
from ..constants import STYLE_PRESETS
from ..exceptions import UserExceptionList, UserWarningError, NoMeshError
from ..reader import LXFML, PartRigid
from ..colour import ColourPalette


logger = logging.getLogger('lego-importer')

_ATOM_FILE_LIST = {}


def fbxImportFix(func):
    """Temporarily set specific FBX import settings."""
    fbxGlobals = {
        'FBXImportMode': 'add',
        'FBXImportMergeAnimationLayers': False,
        'FBXImportProtectDrivenKeys': False,
        'FBXImportConvertDeformingNullsToJoint': False,
        'FBXImportLights': False,
        'FBXImportCameras': False,
    }
    def wrapper(*args, **kwargs):
        loaded = mc.pluginInfo('fbxmaya', query=True, loaded=True)
        if not loaded:
            mc.loadPlugin('fbxmaya')

        originalSettings = {setting[0]: mel.eval('{} -q'.format(setting[0])) for setting in fbxGlobals.items()}

        for melGlobal, tempValue in fbxGlobals.items():
            if isinstance(tempValue, bool):
                mel.eval('{} -v {}'.format(melGlobal, str(tempValue).lower()))
            else:
                mel.eval('{} -v "{}"'.format(melGlobal, tempValue))

        try:
            return func(*args, **kwargs)

        finally:
            for melGlobal, tempValue in fbxGlobals.items():
                originalValue = originalSettings[melGlobal]
                if isinstance(tempValue, bool):
                    mel.eval('{} -v {}'.format(melGlobal, str(bool(originalValue)).lower()))
                else:
                    mel.eval('{} -v "{}"'.format(melGlobal, originalValue))
            if not loaded:
                mc.unloadPlugin('fbxmaya')

    return wrapper


class BrickDirectory(object):
    """Handle the brick directory when working on individual brick design IDs."""

    NODE_TYPES = dict(ma='mayaAscii', mb='mayaBinary', obj='OBJ', fbx='FBX')

    def __init__(self, atomPath, stylePreset, palettePath, group=None):
        self.atomPath = atomPath
        self.stylePreset = stylePreset
        self.palette = ColourPalette(palettePath)
        self.group = group or ''
        self.cache = {}

    def __repr__(self):
        return '{}({!r}, {!r}, {!r})'.format(type(self).__name__, self.atomPath, self.stylePreset, self.group)

    def generatePartName(self, part, wildcard=False):
        """Generate the name of a part.
        If `wildcard` is set, the scene will be searched for any matching parts.
        """
        # Efficient shortcut
        if wildcard:
            return '{}|*|*Part_{}_*'.format(self.group, part.designID.split(';')[0])
        return '{}|Brick_{}_{}|Part_{}_{}'.format(
            self.group,
            '*' if wildcard else part.brick.designID.split(';')[0],
            '*' if wildcard else part.brick.mayaIdentifier,
            part.designID.split(';')[0],
            '*' if wildcard else part.mayaIdentifier,
        )

    @fbxImportFix
    def importBrickPart(self, part, useInstances=True):
        """Import a brick from an ID.

        Parameters:
            part (Part): Brick part read from the XML.
            useInstances (bool): If the current brick should be instanced if possible.
                Instancing should be used on all bricks but the "flex" type.
            shaderNamespace (str, optional): Flag an error if this namespace is imported.

        Returns:
            dict containing the keys "success", "node" and "message".
        """
        brickName = self.generatePartName(part)

        returnVal = dict(success=True, message='', node=brickName)

        # Skip if already imported
        if mc.objExists(brickName):
            # If brick is a locator, then delete it and force a fresh import
            if isBrickALocator(brickName):
                logger.info('Deleting %r locator...', brickName)
                mc.delete(brickName)
                useInstances = False
            else:
                return returnVal

        # Duplicate if matching part exists
        brickMatch = False
        if useInstances:
            brickMatch = mc.ls(self.generatePartName(part, wildcard=True), exactType='transform')

        if brickMatch:
            logger.info('Instancing %r to create %r...', brickMatch[0], brickName)
            newNode = mc.duplicate(brickMatch[0], returnRootsOnly=True, instanceLeaf=True)[0]
            addToDisplayLayer('LEGO_Placeholders' if isBrickALocator(brickMatch[0]) else 'LEGO_Bricks', newNode)
            isInstance = True

        else:
            # Find file on disk
            found = False
            number, suffix = part.designID.split(';')
            filename = 'VX{:07d}.{}.fbx'.format(int(number), suffix)

            try:
                colourData = self.palette.colour(int(part.materials.split(',')[0].split(':')[0]))
            except Exception as e:
                logger.exception(e)
                colourData = None
            stylePresets = STYLE_PRESETS[self.stylePreset]

            if colourData is not None and (colourData.isTransparent or colourData.isGlitter or colourData.isOpalescent):
                styleOptions = stylePresets.get('Transparent')
            else:
                styleOptions = stylePresets.get('Standard')

            if styleOptions is not None:
                logger.debug('Searching for "%s" in %s...', filename, ', then '.join(styleOptions))
                for style in styleOptions:
                    if style not in _ATOM_FILE_LIST:
                        _ATOM_FILE_LIST[style] = set(os.listdir(os.path.join(self.atomPath, style)))

                    if filename in _ATOM_FILE_LIST[style]:
                        path = os.path.join(self.atomPath, style, filename)
                        found = True
                    else:
                        prefix = filename.split('.')[0]
                        for otherfile in _ATOM_FILE_LIST[style]:
                            if otherfile.startswith(prefix):
                                path = os.path.join(self.atomPath, style, otherfile)
                                found = True
                                break

                    if found:
                        break

            # Make a locator if brick doesn't exist
            if not found:
                logger.info('File not found for %r, creating locator...', brickName)
                newNode = mc.spaceLocator()[0]
                addToDisplayLayer('LEGO_Placeholders', newNode)
                isInstance = False

            # Import brick if the first time
            else:
                logger.info('Importing %r from "%s"...', brickName, path)
                newNode = None
                try:
                    nodes = mc.file(path, i=True, returnNewNodes=True,
                                    type=self.NODE_TYPES[os.path.splitext(path)[1][1:]])

                    transformNodes = mc.ls(nodes, exactType='transform')
                    mc.sets(transformNodes, edit=True, forceElement='initialShadingGroup')

                    newNode = transformNodes[0]
                    if not mc.listRelatives(newNode, children=True):
                        raise NoMeshError

                    # Delete non transform / mesh nodes
                    toDelete = set(mc.ls(nodes)) - set(mc.ls(nodes, type=['transform', 'mesh', 'locator']))
                    if toDelete:
                        mc.delete(toDelete)

                    # Add objects to display layers
                    addToDisplayLayer('LEGO_Bricks', newNode)
                    for childItem in ('Knob', 'Tube', 'Pin'):
                        childNodes = [node for node in transformNodes if node.split(':')[-1].startswith(childItem + '_')]
                        if childNodes:
                            addToDisplayLayer('LEGO_{}s'.format(childItem), childNodes)

                    # Add attributes on all nodes
                    for transformNode in transformNodes:
                        mc.addAttr(transformNode, longName='LEGO_logo', attributeType='long', minValue=0, maxValue=1)
                        mc.setAttr(transformNode + '.LEGO_logo', transformNode.split(':')[-1].startswith('Knob_'))

                    # Add custom attributes
                    mc.addAttr(newNode, longName='LEGO_colour', attributeType='float3', usedAsColor=True)
                    mc.addAttr(newNode, longName='LEGO_colourR', attributeType='float', parent='LEGO_colour')
                    mc.addAttr(newNode, longName='LEGO_colourG', attributeType='float', parent='LEGO_colour')
                    mc.addAttr(newNode, longName='LEGO_colourB', attributeType='float', parent='LEGO_colour')
                    mc.addAttr(newNode, longName='LEGO_materialType', attributeType='long')
                    mc.addAttr(newNode, longName='LEGO_materialClass', attributeType='long')
                    mc.addAttr(newNode, longName='LEGO_wear', attributeType='long')
                    mc.addAttr(newNode, longName='LEGO_offsetTexture', attributeType='double3')
                    mc.addAttr(newNode, longName='LEGO_offsetTextureX', attributeType='double', parent='LEGO_offsetTexture')
                    mc.addAttr(newNode, longName='LEGO_offsetTextureY', attributeType='double', parent='LEGO_offsetTexture')
                    mc.addAttr(newNode, longName='LEGO_offsetTextureZ', attributeType='double', parent='LEGO_offsetTexture')
                    mc.addAttr(newNode, longName='LEGO_decal', attributeType='long', minValue=0)
                    mc.addAttr(newNode, longName='LEGO_decalNumber', attributeType='long')

                    # Promote attributes to channel box
                    mc.setAttr(newNode + '.LEGO_materialType', edit=True, channelBox=True)
                    mc.setAttr(newNode + '.LEGO_materialClass', edit=True, channelBox=True)
                    mc.setAttr(newNode + '.LEGO_wear', edit=True, channelBox=True)

                    isInstance = False

                except ZeroDivisionError:
                    raise

                except NoMeshError:
                    if newNode is not None:
                        mc.delete(newNode)
                    isInstance = False
                    newNode = mc.spaceLocator()[0]
                    addToDisplayLayer('LEGO_Placeholders', newNode)

                # If an error, then delete the node and fallback to the locator
                except Exception as e:  # pylint: disable=broad-except
                    logger.exception(e)
                    if newNode is not None:
                        mc.delete(newNode)

                    isInstance = False
                    newNode = mc.spaceLocator()[0]
                    addToDisplayLayer('LEGO_Placeholders', newNode)
                    returnVal['success'] = False
                    returnVal['message'] = str(e)

        # Apply groups and rename node
        grpName, grpItem, grpCreated = ensureGroups(brickName)
        try:
            logger.info('Setting parent: %s -> %s', newNode, grpName)
            mc.parent(newNode, grpName)

        # Item already likely under the correct group
        # Checking via strings is clunky so ask for forgiveness instead
        except RuntimeError:
            if not isInstance:
                raise
            logger.info('Failed to set parent due as instanced')

        # Add/set brick attributes
        if grpCreated:
            mc.addAttr(grpName, longName='LEGO_UUID', dataType='string')
            mc.addAttr(grpName, longName='LEGO_designID', attributeType='long')
            mc.setAttr(grpName + '.LEGO_designID', int(part.brick.designID.split(';')[0]))
            mc.setAttr(grpName + '.LEGO_UUID', part.brick.uuid, type='string')

            if part.version < 8:
                mc.addAttr(grpName, longName='LEGO_refID', attributeType='long')
                mc.setAttr(grpName + '.LEGO_refID', int(part.brick.refID))

        # Set correct node name
        logger.info('Renaming: %s | %s -> %s', grpName, newNode, grpItem)
        mc.rename(grpName + '|' + newNode, grpItem)

        if not isInstance:
            # Add custom attributes to store data
            mc.addAttr(brickName, longName='LEGO_designID', attributeType='long')
            mc.addAttr(brickName, longName='LEGO_materialID', attributeType='long')
            mc.addAttr(brickName, longName='LEGO_decoration', dataType='string')
            # mc.addAttr(brickName, longName='LEGO_transformation', attributeType='fltMatrix')

            if part.version >= 8:
                mc.addAttr(brickName, longName='LEGO_UUID', dataType='string')
            else:
                mc.addAttr(brickName, longName='LEGO_refID', attributeType='long')

        # Set custom attributes
        mc.setAttr(brickName + '.LEGO_designID', int(part.designID.split(';')[0]))
        mc.setAttr(brickName + '.LEGO_materialID', int(part.materials.split(',')[0].split(':')[0]))
        mc.setAttr(brickName + '.LEGO_decoration', part.decoration or '', type='string')
        if part.version >= 8:
            mc.setAttr(brickName + '.LEGO_UUID', part.uuid, type='string')
        else:
            mc.setAttr(brickName + '.LEGO_refID', int(part.refID))

        # Apply transformation matrix
        setMatrix(brickName, part.matrix)

        # Randomise values
        if not isBrickALocator(brickName):
            mc.setAttr(brickName + '.LEGO_offsetTextureX', random.uniform(-1, 1))
            mc.setAttr(brickName + '.LEGO_offsetTextureY', random.uniform(-1, 1))
            mc.setAttr(brickName + '.LEGO_offsetTextureZ', random.uniform(-1, 1))

        return returnVal


def ensureGroups(dagPath):
    """Take a dag path and create any required groups.

    If ensuring "a|b|c", then "a|b" will be created, and
    a tuple of ("a|b", "c", True) will be returned.
    """
    groups = dagPath.lstrip('|').split('|')
    name = groups.pop(-1)
    createdGroup = False
    for i, group in enumerate(groups):
        previousGroup = '|' + '|'.join(groups[:i])
        if createdGroup:
            groupExists = False
        else:
            groupExists = mc.ls(previousGroup.rstrip('|') + '|' + group)

        if not groupExists:
            tmpName = 'tmp_' + uuid4().hex
            mc.group(name=tmpName, empty=True)
            if i:
                mc.parent(tmpName, previousGroup)
            mc.rename(previousGroup + '|' + tmpName, group)
            createdGroup = True

    return '|'.join([''] + groups), name, createdGroup


def setMatrix(node, matrix):
    """Set a transformation matrix on a node."""
    decomposeMatrix = mc.createNode('decomposeMatrix')
    mc.connectAttr(decomposeMatrix + '.outputTranslate', node + '.translate', force=True)
    mc.connectAttr(decomposeMatrix + '.outputRotate', node + '.rotate', force=True)
    mc.connectAttr(decomposeMatrix + '.outputScale', node + '.scale', force=True)
    mc.setAttr(decomposeMatrix + '.inputMatrix', matrix, type='matrix')
    mc.delete(decomposeMatrix)


def addToDisplayLayer(layer, nodes):
    """Add nodes to a display layer."""
    try:
        displayLayer = mc.ls(layer + '*', exactType='displayLayer')[0]
    except IndexError:
        displayLayer = mc.createDisplayLayer(name=layer, empty=True)
    mc.editDisplayLayerMembers(displayLayer, nodes, noRecurse=True)


def setupScene(xmlPath, brickDirectory, groups=True, selectionSets=True, sockets=True,
               pivots=True, collapseGeo=True, rename=True, commonPartsPath=None, commonPartsStyle=None,
               **kwargs):
    """Load the brick files into the scene.

    Returns:
        List of failed node imports and the exception raised.
    """
    with UserExceptionList() as exc:
        unknownPlugins = set(mc.unknownPlugin(query=True, list=True) or ())
        lxfml = LXFML(xmlPath)

        nodes = defaultdict(lambda: defaultdict(list))
        for brick in lxfml.bricks:
            logger.info('Processing brick: %s', brick)
            for part in brick.parts:
                logger.info('Processing part: %s', part)
                if not isinstance(part, PartRigid):
                    logger.info('Skipping part as not rigid')
                    continue

                result = brickDirectory.importBrickPart(part, **kwargs)
                if result['success']:
                    nodes[brick.mayaIdentifier][part.mayaIdentifier] = '|' + result['node']
                else:
                    exc.append('Brick {}: {}'.format(part.designID.split(';')[0], result['message']))

        # Set XML path on group
        if brickDirectory.group and 'LEGO_XML' not in mc.listAttr(brickDirectory.group):
            mc.addAttr(brickDirectory.group, longName='LEGO_XML', dataType='string')
            mc.setAttr(brickDirectory.group + '.LEGO_XML', xmlPath, type='string')

        # Create selection sets
        if selectionSets:
            for selectionSet in lxfml.selectionSets:
                selectionSetName = selectionSet.name
                if not mc.objExists(selectionSetName):
                    selectionSetName = mc.sets([], name=selectionSetName)
                bricks = [next(iter(nodes[brick.mayaIdentifier].values())).rsplit('|', 1)[0] for brick in selectionSet.bricks
                          if brick.mayaIdentifier in nodes]
                mc.sets(bricks, add=selectionSetName)

        # Create groups
        if groups:
            for group in lxfml.groups:
                groupPath = '|{}|{}'.format(brickDirectory.group, group.name)
                bricks = [next(iter(nodes[brick.mayaIdentifier].values())).rsplit('|', 1)[0] for brick in group.bricks
                          if brick.mayaIdentifier in nodes]

                # Ensure group exists
                parent, groupName = groupPath.rsplit('|', 1)
                if not mc.objExists(groupPath):
                    groupPath = mc.rename(mc.parent(mc.createNode('transform'), parent), groupName)

                for brick in bricks:
                    brickParentOld = mc.listRelatives(brick, parent=True, fullPath=True)[0]
                    brick = mc.parent(brick, groupPath)[0]
                    brickID = UUID(mc.getAttr(brick + '.LEGO_UUID')).hex
                    brickParentNew = mc.listRelatives(brick, parent=True, fullPath=True)[0]
                    for part, node in nodes[brickID].items():
                        nodes[brickID][part] = node.replace(brickParentOld, brickParentNew)

        allChildren = set(mc.listRelatives('|' + brickDirectory.group, allDescendents=True, fullPath=True))

        # Create sockets
        if sockets:
            for socketGroup in allChildren & set(mc.ls('_sockets', long=True)):
                for child in mc.listRelatives(socketGroup, children=True, fullPath=True):

                    # Remove from data dict
                    for brick in mc.listRelatives(child, children=True, fullPath=True):
                        brickID = UUID(mc.getAttr(brick + '.LEGO_UUID')).hex
                        del nodes[brickID]

                    # Find the world position
                    allMeshes = mc.listRelatives(child, allDescendents=True, type='mesh', fullPath=True)
                    if not allMeshes:
                        continue
                    meshTransforms = mc.listRelatives(allMeshes[0], parent=True, fullPath=True)
                    worldPos = mc.xform(meshTransforms, query=True, translation=True, worldSpace=True)

                    # Create socket
                    logger.info('Creating socket at %s', worldPos)
                    locator = mc.spaceLocator(name=child.split('|')[-1][:-4], position=worldPos)[0]

                    # Parent to top level group
                    locator = mc.parent(locator, mc.listRelatives(socketGroup, parent=True, fullPath=True)[0])[0]

                    renameSceneObjects(locator)

                mc.delete(socketGroup)

        # Create pivots
        if pivots:
            pivotGroups = set(mc.ls('_pivot', long=True))
            for pivotGroup in allChildren & pivotGroups:
                for child in mc.listRelatives(pivotGroup, children=True, fullPath=True):
                    # Remove from data dict
                    brickID = UUID(mc.getAttr(child + '.LEGO_UUID')).hex
                    del nodes[brickID]

                    # Find the world position
                    allMeshes = mc.listRelatives(child, allDescendents=True, type='mesh', fullPath=True)
                    if not allMeshes:
                        continue
                    meshTransforms = mc.listRelatives(allMeshes[0], parent=True, fullPath=True)
                    worldPos =  mc.xform(meshTransforms, query=True, translation=True, worldSpace=True)

                    # Create pivot
                    parentGroup = mc.listRelatives(pivotGroup, parent=True, fullPath=True)[0]
                    mc.xform(parentGroup, worldSpace=True, scalePivot=worldPos)
                    mc.xform(parentGroup, worldSpace=True, rotatePivot=worldPos)
                    logger.info('Setting pivot on %s to %s', parentGroup, worldPos)

                mc.delete(pivotGroup)

        # Collapse bricks
        if collapseGeo:
            for brick, parts in nodes.items():
                logger.info('Flattening brick: %s', brick)
                for part, node in parts.items():
                    logger.info('Flattening part: %s (%s)', part, node)
                    children = mc.listRelatives(node, children=True, type='transform', fullPath=True)
                    if not children:
                        if not mc.listRelatives(node, children=True, type='locator', fullPath=True):
                            raise RuntimeError('unknown children for {}'.formst(node))
                        continue
                    relatives = mc.listRelatives(children, allDescendents=True, type=('mesh', 'locator'), fullPath=True)
                    parents = mc.listRelatives(relatives, parent=True, fullPath=True)
                    for child in sorted(parents, key=len, reverse=True):
                        parts[part] = mc.listRelatives(mc.parent(child, node)[0], parent=True, fullPath=True)[0]
                    mc.delete(children)

        # Clear any new unknown plugins
        newUnknownPlugins = set(mc.unknownPlugin(query=True, list=True) or ()) - unknownPlugins
        for plugin in newUnknownPlugins:
            logger.info('Removing unknown plugin: %s', plugin)
            try:
                mc.unknownPlugin(plugin, remove=True)
            except Exception as e:
                exc.append('{}: {}'.format(plugin, e))

        # Rename brick nodes
        if rename:
            nodesToRename = set()
            for brickID, parts in nodes.items():
                for node in parts.values():
                    brick = mc.listRelatives(node, parent=True)[0]
                    nodesToRename.add(brick)
                    nodesToRename.update(mc.listRelatives(brick, allDescendents=True, type='transform'))
                    break
            renameSceneObjects(nodesToRename)

        if commonPartsPath is not None and commonPartsStyle is not None:
            run_style_update(brickDirectory.stylePreset, commonPartsPath)
