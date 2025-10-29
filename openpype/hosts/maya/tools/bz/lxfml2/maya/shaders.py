import logging
import os

import maya.cmds as mc

from .utils import getSceneBricks


logger = logging.getLogger('lego-importer')


def referenceShaders(path, namespace='LEGO_shaders'):
    """Ensures the shaders are referenced.

    Returns the shader namespace.
    """
    refNode = '{}RN'.format(namespace)
    # Check if the existing shader reference path matches the input path
    try:
        if os.path.normpath(mc.referenceQuery(refNode, filename=True)) == os.path.normpath(path):
            return mc.referenceQuery(refNode, namespace=True).lstrip(':')

    # No shaders exist
    except RuntimeError:
        pass

    # Remove the existing shader reference
    else:
        mc.file(referenceNode=refNode, removeReference=True)

    # Bring in the new shader reference
    nodes = mc.file(path, reference=True, type="mayaAscii", namespace=namespace, returnNewNodes=True)

    # Get the namespace
    refNode = mc.ls((node for node in nodes if ':' not in node), exactType='reference')[0]
    return mc.referenceQuery(refNode, namespace=True).lstrip(':')


def assignShaders(path=None, namespace='shaders', shadingGroup='*_{}_*_SG'):
    """Assign shaders to each brick.

    Returns the shader namespace.
    """
    # Ensure the correct shader is referenced
    if path is not None:
        namespace = referenceShaders(path, namespace=namespace)

    # Read the materialID attribute of each brick to assign the shader
    for brick in getSceneBricks():
        try:
            materialID = int(mc.getAttr(brick + '.LEGO_materialIDs').split(',')[0])
        except ValueError:
            logger.warning('%s is missing material data, possibly due to a failed import', brick)
            continue

        shadingEngines = mc.ls(namespace + ':' + shadingGroup.format(materialID), exactType='shadingEngine')
        if not shadingEngines:
            logger.warning('No shaders found for material ID %s', materialID)
            continue
        elif len(shadingEngines) > 1:
            logger.warning('Multiple shaders found for material ID %s', materialID)

        logger.debug('Setting shader of {} to {}'.format(brick, shadingEngines[0]))
        mc.sets(brick, edit=True, forceElement=shadingEngines[0])

    return namespace
