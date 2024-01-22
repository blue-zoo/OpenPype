import logging
import os
import random
from collections import defaultdict
from uuid import uuid4

import maya.cmds as mc
import maya.mel as mel

from .utils import isBrickALocator
from ..exceptions import UserExceptionList, UserWarningError
from ..reader import LXFML, PartRigid


logger = logging.getLogger('lego-importer')


class BlockTweaks(object):
    SetAttributes               = 0b00000001
    UpdateUVs                   = 0b00000010
    DeleteColourSets            = 0b00000100
    DeleteHistory               = 0b00001000
    UpdateDisplayEdges          = 0b00010000
    SetTexelDensity             = 0b00100000
    SoftenEdges                 = 0b01000000
    UpdateDisplayColourChannel  = 0b10000000



class BrickDirectory(object):
    """Handle the brick directory when working on individual brick design IDs."""

    NODE_TYPES = dict(ma='mayaAscii', mb='mayaBinary', obj='OBJ')

    def __init__(self, dirPattern, group=None):
        self.dirPattern = dirPattern
        self.group = group or ''
        self.cache = {}

    def __repr__(self):
        return '{}({!r}, group={!r})'.format(type(self).__name__, self.dirPattern, self.group)

    def _getEnum(self, node):
        """Get the node enum value.
        The attribute is created if it doesn't exist.
        """
        try:
            return mc.getAttr(node + '.LEGO_importData')
        except ValueError:
            mc.addAttr(node, longName='LEGO_importData', attributeType='long', minValue=0)
            return 0

    def _checkEnum(self, node, enum):
        """Check if an operation has been done on the brick."""
        return bool(self._getEnum(node) & enum)

    def _setEnum(self, node, enum):
        """Mark when an operation has been done."""
        original = self._getEnum(node)
        new = original | enum
        if original == new:
            return False
        mc.setAttr(node + '.LEGO_importData', self._getEnum(node) | enum)
        return True

    def _updateUVs(self, node):
        """Add "map1" and "bumpSet" UV sets.

        If "map1" or "bumpSet" already exists, it will be deleted.
        If any UV set contains the text "3DP", then the first instance
        will be renamed to "bumpSet".
        The very first UV set will be set to "map1". If this clashes with
        "bumpSet", then "bumpSet" will be duplicated.
        """
        uvSets = mc.polyUVSet(node, query=True, allUVSets=True)
        if 'map1' in uvSets[1:]:
            mc.polyUVSet(node, delete=True, uvSet='map1')

        # Rename or delete the existing bumpSet
        if 'bumpSet' in uvSets:
            if uvSets[0] == 'bumpSet':
                mc.polyUVSet(node, rename=True, uvSet='bumpSet', newUVSet='map1')
                uvSets[0] = 'map1'
            else:
                mc.polyUVSet(node, delete=True, uvSet='bumpSet')

        # Rename the 3DP set to bumpSet
        for i, uvSet in enumerate(uvSets):
            if '3DP' in uvSet:
                mc.polyUVSet(node, rename=True, uvSet=uvSet, newUVSet='bumpSet')
                uvSets[i] = 'bumpSet'
                break

        # Ensure first set is map1, copy bumpSet if required
        if uvSets[0] != 'map1':
            mc.polyUVSet(node, rename=True, uvSet=uvSets[0], newUVSet='map1')
            if uvSets[0] == 'bumpSet':
                mc.polyUVSet(node, copy=True, uvSet='map1', newUVSet='bumpSet')

        # Set current UV set to bumpSet
        mc.polyUVSet(node, currentUVSet=True, uvSet='bumpSet')

    def _deleteColourSets(self, nodes):
        """Delete all colour sets."""
        if mc.polyColorSet(nodes, query=True, allColorSets=True):
            mc.polyColorSet(nodes, delete=True)

    def _deleteHistory(self, node):
        """Delete the node construction history."""
        mc.delete(node, constructionHistory=True)

    def _updateDisplayEdges(self, node):
        """Ensure "Mesh Component Display Edges" is set to "Standard"."""
        brickShape = mc.ls(mc.listRelatives(node, children=True, path=True)[0], exactType='mesh')[0]
        mc.setAttr(brickShape + '.displayEdges', 0)

    def _setTexelDensity(self, node):
        """Set the texel density to 25 | 512.

        This is a heavy operation and will add considerable processing time to the import.
        """
        mc.select(node)
        try:
            mel.eval('texSetTexelDensity(25, 512)')
        except RuntimeError as e:
            logger.warning(e)
            raise UserWarningError('error setting texel density')

    def _softenEdge(self, node):
        """Apply the soften edge modifier.

        This is a heavy operation and will add considerable processing time to the import.
        """
        mc.polySoftEdge(node, angle=180, constructionHistory=False)

    def _setDisplayColourChannel(self, node):
        """Set the display colour channel to diffuse."""
        mc.setAttr(node + '.displayColorChannel', 'Diffuse', type='string')

    def generatePartName(self, part, wildcard=False):
        """Generate the name of a part.
        If `wildcard` is set, the scene will be searched for any matching parts.
        """
        # Efficient shortcut
        if wildcard:
            return '*Part_{}_*'.format(part.designID.split(';')[0])
        return '{}|Brick_{}_{}|Part_{}_{}'.format(
            self.group,
            '*' if wildcard else part.brick.designID.split(';')[0],
            '*' if wildcard else part.brick.mayaIdentifier,
            part.designID.split(';')[0],
            '*' if wildcard else part.mayaIdentifier,
        )

    def importBrickPart(self, part, useInstances=True, updateUVs=True, deleteColourSets=True,
                        deleteHistory=True, updateDisplayEdges=True, setTexelDensity=True,
                        softenEdges=True, updateDisplayColourChannel=True, shaderNamespace=None):
        """Import a brick from an ID.

        Parameters:
            part (Part): Brick part read from the XML.
            useInstances (bool): If the current brick should be instanced if possible.
                Instancing should be used on all bricks but the "flex" type.
            updateUVs (bool): Add "map1" and "bumpSet" UV sets.
            deleteColourSets (bool): Delete all colour sets.
            deleteHistory (bool): Delete the node construction history.
            updateDisplayEdges (bool): Ensure Display Edges is set to the default value.
            setTexelDensity (bool): Set a uniform texel density on all nodes.
            softenEdges (bool): Apply the soften edge modifier.
            updateDisplayColourChannel (bool): Set the display colour channel to diffuse.
            shaderNamespace (str, optional): Flag an error if this namespace is imported.

        Returns:
            dict containing the keys "success", "node" and "message".
        """
        path = self.dirPattern.replace('*', part.designID.split(';')[0])
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

        # Make a locator if brick doesn't exist
        elif not os.path.exists(path):
            logger.info('File not found for %r, creating locator...', brickName)
            newNode = mc.spaceLocator()[0]
            addToDisplayLayer('LEGO_Placeholders', newNode)
            isInstance = False

        # Import brick if the first time
        else:
            logger.info('Importing %r (%s)...', brickName, path)
            newNode = None
            try:
                # Bring in the file
                namespace = '_ns_tmp_' + uuid4().hex
                nodes = mc.file(path, i=True, returnNewNodes=True, namespace=namespace,
                                type=self.NODE_TYPES[os.path.splitext(path)[1][1:]])
                transformNodes = mc.ls(nodes, exactType='transform')
                newNode = transformNodes[0]

                if shaderNamespace is not None and any(node.startswith('{}:{}:'.format(namespace, shaderNamespace))
                                                       for node in nodes):
                    raise UserWarningError('brick contains "{}" namespace'.format(shaderNamespace))

                # Remove colour sets
                if deleteColourSets and not self._checkEnum(newNode, BlockTweaks.DeleteColourSets):
                    self._deleteColourSets(transformNodes)
                    self._setEnum(newNode, BlockTweaks.DeleteColourSets)

                # Handle UV sets
                if updateUVs and not self._checkEnum(newNode, BlockTweaks.UpdateUVs):
                    for transformNode in transformNodes:
                        self._updateUVs(transformNode)
                    self._setEnum(newNode, BlockTweaks.UpdateUVs)

                # Remove the construction history
                if deleteHistory and not self._checkEnum(newNode, BlockTweaks.DeleteHistory):
                    self._deleteHistory(nodes)
                    self._setEnum(newNode, BlockTweaks.DeleteHistory)

                # Soften the edges
                if softenEdges and not self._checkEnum(newNode, BlockTweaks.SoftenEdges):
                    for node in transformNodes + mc.ls(nodes, exactType=['mesh']):
                        self._softenEdge(node)
                    self._setEnum(newNode, BlockTweaks.SoftenEdges)

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

                # Sort out the namespace
                newNode = mc.rename(transformNodes[0], namespace + ':' + '_brick_tmp_' + uuid4().hex)
                mc.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
                newNode = newNode.split(':')[-1]

                # Set shape display edges to standard
                if updateDisplayEdges and not self._checkEnum(newNode, BlockTweaks.UpdateDisplayEdges):
                    self._updateDisplayEdges(newNode)
                    self._setEnum(newNode, BlockTweaks.UpdateDisplayEdges)

                # Set texel density
                if setTexelDensity and not self._checkEnum(newNode, BlockTweaks.SetTexelDensity):
                    self._setTexelDensity(newNode)
                    self._setEnum(newNode, BlockTweaks.SetTexelDensity)

                # Update the display colour channel
                if updateDisplayColourChannel and not self._checkEnum(newNode, BlockTweaks.UpdateDisplayColourChannel):
                    self._setDisplayColourChannel(newNode)
                    self._setEnum(newNode, BlockTweaks.UpdateDisplayColourChannel)

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
            mc.parent(newNode, grpName)

        # Item already likely under the correct group
        # Checking via strings is clunky so ask for forgiveness instead
        except RuntimeError:
            if not isInstance:
                raise

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
        mc.rename(grpName + '|' + newNode, grpItem)

        if not isInstance:
            # Add custom attributes to store data
            mc.addAttr(brickName, longName='LEGO_designID', attributeType='long')
            mc.addAttr(brickName, longName='LEGO_materialIDs', dataType='string')
            mc.addAttr(brickName, longName='LEGO_decoration', dataType='string')
            # mc.addAttr(brickName, longName='LEGO_transformation', attributeType='fltMatrix')

            if part.version >= 8:
                mc.addAttr(brickName, longName='LEGO_UUID', dataType='string')
            else:
                mc.addAttr(brickName, longName='LEGO_refID', attributeType='long')

        # Set custom attributes
        mc.setAttr(brickName + '.LEGO_designID', int(part.designID.split(';')[0]))
        mc.setAttr(brickName + '.LEGO_materialIDs', ','.join(mat.split(':')[0] for mat in part.materials.split(',')), type='string')
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

    def processBricksInFile(self, updateUVs=True, deleteColourSets=True,
                            deleteHistory=True, updateDisplayEdges=True, setTexelDensity=True,
                            softenEdges=True, updateDisplayColourChannel=True):
        """Process a brick file.

        Parameters:
            updateUVs (bool): Add "map1" and "bumpSet" UV sets.
            deleteColourSets (bool): Delete all colour sets.
            deleteHistory (bool): Delete the node construction history.
            updateDisplayEdges (bool): Ensure Display Edges is set to the default value.
            setTexelDensity (bool): Set a uniform texel density on all nodes.
            softenEdges (bool): Apply the soften edge modifier.
            updateDisplayColourChannel (bool): Set the display colour channel to diffuse.

        Returns:
            list of dicts containing the keys "success", "node" and "message".
        """
        returnVals = []
        for node in mc.ls(assemblies=True):
            if not mc.listRelatives(node, children=True, type='mesh'):
                continue

            updates = 0
            logger.info('Processing %r...', node)
            returnVal = dict(success=True, message='', node=node)
            transformNodes = [node] + mc.ls(node + '|*', exactType='transform')

            try:
                # Remove colour sets
                if deleteColourSets and not self._checkEnum(node, BlockTweaks.DeleteColourSets):
                    self._deleteColourSets(transformNodes)
                    updates += self._setEnum(node, BlockTweaks.DeleteColourSets)

                # Handle UV sets
                if updateUVs and not self._checkEnum(node, BlockTweaks.UpdateUVs):
                    for transformNode in transformNodes:
                        self._updateUVs(transformNode)
                    updates += self._setEnum(node, BlockTweaks.UpdateUVs)

                # Remove the construction history
                if deleteHistory and not self._checkEnum(node, BlockTweaks.DeleteHistory):
                    self._deleteHistory(node)
                    updates += self._setEnum(node, BlockTweaks.DeleteHistory)

                # Soften the edges
                if softenEdges and not self._checkEnum(node, BlockTweaks.SoftenEdges):
                    for childNode in transformNodes + mc.ls(node, exactType=['mesh']):
                        self._softenEdge(childNode)
                    updates += self._setEnum(node, BlockTweaks.SoftenEdges)

                # Set shape display edges to standard
                if updateDisplayEdges and not self._checkEnum(node, BlockTweaks.UpdateDisplayEdges):
                    self._updateDisplayEdges(node)
                    updates += self._setEnum(node, BlockTweaks.UpdateDisplayEdges)

                # Set texel density
                if setTexelDensity and not self._checkEnum(node, BlockTweaks.SetTexelDensity):
                    self._setTexelDensity(node)
                    updates += self._setEnum(node, BlockTweaks.SetTexelDensity)

                # Update the display colour channel
                if updateDisplayColourChannel and not self._checkEnum(node, BlockTweaks.UpdateDisplayColourChannel):
                    self._setDisplayColourChannel(node)
                    updates += self._setEnum(node, BlockTweaks.UpdateDisplayColourChannel)

            except Exception as e:  # pylint: disable=broad-except
                logger.exception(e)
                returnVal['success'] = False
                returnVal['message'] = str(e)

            if updates:
                returnVals.append(returnVal)

        return returnVals


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


def setupScene(xmlPath, brickDirectory, **kwargs):
    """Load the brick files into the scene.

    Returns:
        List of failed node imports and the exception raised.
    """
    with UserExceptionList() as exc:
        unknownPlugins = set(mc.unknownPlugin(query=True, list=True) or ())
        lxfml = LXFML(xmlPath)

        nodes = defaultdict(lambda: defaultdict(list))
        for brick in lxfml.bricks:
            for part in brick.parts:
                if not isinstance(part, PartRigid):
                    continue

                result = brickDirectory.importBrickPart(part, **kwargs)
                if result['success']:
                    nodes[brick.mayaIdentifier][part.mayaIdentifier] = result['node']
                else:
                    exc.append('Brick {}: {}'.format(part.designID.split(';')[0], result['message']))

        # Set XML path on group
        if brickDirectory.group and 'LEGO_XML' not in mc.listAttr(brickDirectory.group):
            mc.addAttr(brickDirectory.group, longName='LEGO_XML', dataType='string')
            mc.setAttr(brickDirectory.group + '.LEGO_XML', xmlPath, type='string')

        # Create selection sets
        for selectionSet in lxfml.selectionSets:
            selectionSetName = selectionSet.name
            if not mc.objExists(selectionSetName):
                selectionSetName = mc.sets([], name=selectionSetName)
            bricks = [next(iter(nodes[brick.mayaIdentifier].values())).rsplit('|', 1)[0] for brick in selectionSet.bricks
                      if brick.mayaIdentifier in nodes]
            mc.sets(bricks, add=selectionSetName)

        # Clear any new unknown plugins
        newUnknownPlugins = set(mc.unknownPlugin(query=True, list=True) or ()) - unknownPlugins
        for plugin in newUnknownPlugins:
            logger.info('Removing unknown plugin: %s', plugin)
            try:
                mc.unknownPlugin(plugin, remove=True)
            except Exception as e:
                exc.append('{}: {}'.format(plugin, e))


def processInFile():
    return BrickDirectory('').processBricksInFile()


def batchProcess():
    """Shortcut function to run as a batch process."""
    import arrow
    logger.setPath(os.path.dirname(mc.file(query=True, sceneName=True)))
    result = processInFile()
    if result:
        logger.info('Result: %s', result)
        mc.file(save=True, force=True)
    else:
        logger.info('Result: No update required')
