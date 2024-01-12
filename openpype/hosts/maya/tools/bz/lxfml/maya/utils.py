import maya.cmds as mc


def isBrickALocator(brick):
    """Determine if the brick is a locator."""
    return mc.nodeType(mc.listRelatives(brick, children=True, path=True)[0]) == 'locator'


def getSceneBricks():
    """Get all bricks in the scene.

    If there is no LEGO_Bricks group, then it will get any top level transform nodes.
    """
    nodes = (node.rsplit('.', 1)[0] for node in mc.ls('*.LEGO_importData'))
    return [node for node in nodes if mc.listRelatives(node, children=True, type='mesh')]
