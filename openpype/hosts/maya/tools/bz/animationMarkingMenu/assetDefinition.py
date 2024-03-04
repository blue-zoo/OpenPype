import json

import maya.cmds as mc


def _validate(node):
    '''Validate existence of object'''
    if mc.objExists(node):
        return 1
    mc.warning(node + " does not exist.")
    return 0


def defineControl(control, topNode="C_characterName_CTL"):
    '''Define single control'''
    if not _validate(control) or not _validate(topNode):
        return

    if not mc.objExists(control + ".controlInfo"):
        mc.addAttr(control, ln="controlInfo",
                   at="compound", numberOfChildren=2)
    for attr in ["animControl", "controlType"]:
        if not mc.objExists(control + ".controlInfo." + attr):
            mc.addAttr(control, ln=attr, at="message", p="controlInfo")
    if topNode not in (mc.listConnections(control + ".controlInfo.animControl", s=1, d=0) or []):
        mc.connectAttr(topNode + ".assetInfo.character",
                       control + ".controlInfo.animControl", f=1)
    if topNode not in (mc.listConnections(control + ".controlInfo.controlType", s=1, d=0) or []):
        mc.connectAttr(topNode + ".assetInfo.controls.bodyControls",
                       control + ".controlInfo.controlType", f=1)


def defineControls(controls, topNode="C_characterName_CTL"):
    '''Define list of controls'''
    if not isinstance(controls, list):
        mc.warning("The function defineControls expects a list of controls.")
        return

    for control in controls:
        defineControl(control, topNode)


def defineTopNode(topNode="C_characterName_CTL"):
    '''Define top node'''
    if not _validate(topNode):
        return

    if not mc.objExists(topNode + ".assetInfo"):
        mc.addAttr(topNode, ln="assetInfo", at="compound", numberOfChildren=2)
    if not mc.objExists(topNode + ".assetInfo.character"):
        mc.addAttr(topNode, ln="character", at="message", p="assetInfo")
    if not mc.objExists(topNode + ".assetInfo.controls"):
        mc.addAttr(topNode, ln="controls", at="compound",
                   p="assetInfo", numberOfChildren=2)
        for attr in ["bodyControls", "faceControls"]:
            if not mc.objExists(topNode + ".assetInfo.controls." + attr):
                mc.addAttr(topNode, ln=attr, at="message", p="controls")
    if not mc.objExists(topNode + ".reference"):
        mc.addAttr(topNode, ln="reference", at="short", min=0, max=1)
        mc.setAttr(topNode + ".reference", 1)
        mc.setAttr(topNode + ".reference", e=1, k=0, cb=1)

    defineControl(topNode, topNode)


def _writeControlBindPose(control):
    '''Write single control's bind pose.'''
    if not _validate(control):
        return

    controlBindPose = {}
    attributes = (mc.listAttr(control, k=1, u=1) or []) + \
        (mc.listAttr(control, cb=1, u=1) or [])
    for attr in attributes:
        if not mc.listConnections(control + "." + attr, s=1, d=0):
            controlBindPose[attr] = mc.getAttr(control + "." + attr)

    if not mc.objExists(control + ".bindPose"):
        mc.addAttr(control, ln="bindPose", dt="string", k=False)
    mc.setAttr(control + ".bindPose", e=1, l=0)
    mc.setAttr(control + ".bindPose",
               json.dumps(controlBindPose), type="string")
    mc.setAttr(control + ".bindPose", e=1, l=1)


def writeBindPose(topNode="C_characterName_CTL"):
    '''Write bind pose for all defined controls'''
    controls = (mc.listConnections(topNode + ".assetInfo.character") or [])

    for control in controls:
        _writeControlBindPose(control)

        if mc.objExists(control + ".gimbal"):
            gimbalControl = mc.listConnections(control + ".gimbal")[0]
            _writeControlBindPose(gimbalControl)


def defineGeometry(geo, topNode="C_characterName_CTL"):
    '''Define single piece of geo for reference'''
    if not _validate(geo) or not _validate(topNode):
        return

    if not isinstance(geo, (str,u''.__class__)):
        mc.warning(
            "defineGeometry takes a single piece of geo and a topNode as input.")
        return

    if not mc.objExists(topNode + ".reference"):
        mc.warning(topNode + " has not been defined as a top node.")
        return

    if mc.nodeType(geo) == "transform":
        geo = mc.listRelatives(geo, c=1, s=1)[0]
    mc.setAttr(geo + ".overrideDisplayType", 2)
    mc.connectAttr(topNode + ".reference", geo + ".overrideEnabled")


def defineGeometries(geometries, topNode="C_characterName_CTL"):
    '''Define a list of geometries for referencing'''
    for geo in geometries:
        defineGeometry(geo, topNode)
