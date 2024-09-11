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


def scaleObject(obj, scaleFactor):
    """Scale an object by a factor."""
    scalePivot = mc.xform(obj, query=True, scalePivot=True, worldSpace=True)
    mc.xform(obj, scalePivot=[0, 0, 0], worldSpace=1)
    mc.xform(obj, scale=[scaleFactor, scaleFactor, scaleFactor], worldSpace=True, relative=True)
    mc.xform(obj, scalePivot=[x * scaleFactor for x in scalePivot], worldSpace=True)
    mc.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True, normal=False, preserveNormals=True)
