import maya.cmds as mc


def attachWearable(wearable, attachTo):
    # Grab the script node from the wearable compound
    scriptNode = mc.listConnections(wearable + ":C_characterNode_CTL.wearable.scriptNode")[0]

    # Grab the actual script to be executed as we need to replace names
    script = mc.getAttr(scriptNode + ".before")

    # Inject the specified namespaces
    script = script.replace("{{ATTACH_TO_NAMESPACE}}", attachTo + ":")
    script = script.replace("{{ATTACHED_NAMESPACE}}", wearable + ":")

    # Set the modified script to the scriptNode
    mc.setAttr(scriptNode + ".before", script, typ="string")

    # Run the attach script
    mc.scriptNode(scriptNode, eb=1)

    # Set the scriptNode to evaluate on Open/Close from here on as it has already
    # been attached and we want the script to be ran every time to accomodate
    # potential updates to it
    # NOTE: We no longer need to do this, since we are running the scriptNodes
    # manually with a callback stored in here `Pipeline/security/maya/callbacks.py`
    #mc.setAttr(scriptNode + ".scriptType", 1)

    # Populate the other wearable related attributes
    mc.setAttr(wearable + ":C_characterNode_CTL.wearable.activated", 1)
    mc.connectAttr(attachTo + ":C_characterNode_CTL.message",
                   wearable + ":C_characterNode_CTL.wearable.attachedTo")

    return True

