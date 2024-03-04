
try:
	import animation.character_class as cc
except:
	pass
from . import functions
import maya.cmds as mc


def selectAllControls(*args):
    charNodes = functions._getSelectedCharacterNodes()
    
    mc.select(*[mc.listConnections(charNode + ".character") for charNode in charNodes])
    
def keyAllControls(*args):
    charNodes = functions._getSelectedCharacterNodes()
    
    for charNode in charNodes:
        c = cc.char(charNode)
        c.key_all_controls(skip_top=False)
        
def toggle_controls(*args):
    charNodes = functions._getSelectedCharacterNodes()
    
    for charNode in charNodes:
        char = cc.char(charNode)
        relatives = mc.listRelatives(char.return_character_controls()[0],c=1,shapes=1,ni=1)
        for shape in relatives:
            if mc.nodeType(shape) == 'nurbsCurve':
                vis = mc.getAttr(shape+".lodVisibility")
        if vis:
            char.toggle_control_visibility(enable=False)
        else:
            char.toggle_control_visibility(enable=True)
            
def revertSelectedToBindpose(*args):
    for charNode in functions._getSelectedCharacterNodes():
        char = cc.char(charNode)
        char.revert_selected_to_bind_pose(mc.ls(sl=1))
        
def revertSelectedAssetsToBindpose(*args):
    for charNode in functions._getSelectedCharacterNodes():
        char = cc.char(charNode)
        char.restore_character_to_bind_pose()

## IK FK MATCH BLOCK
def return_ik_fk_control(control):
    marked=[]
    for attr in ['IK_WRIST_MARKER','FK_WRIST_MARKER','IK_SWITCH_MENU']:
        active_controller = False
        if mc.attributeQuery(attr,node=control,exists=True):
            active_controller = mc.listConnections(control+"."+attr,s=0,d=1)
            if active_controller ==None:
                active_controller = mc.listConnections(control+"."+attr,s=1,d=0)
                if active_controller not in [None,[],'']:
                    active_controller = active_controller[0]
            else:
                active_controller = control
            if active_controller:
                marked.append(active_controller)
    if not marked == []:
        return marked[0]
    else:
        return False
    
def flip_switch_attr(node):
    node_address = mc.getAttr(node+".IKFK_SWITCH_ATTR")
    type = mc.getAttr(node+'.'+node_address,type=True)    
    if type in ['double','interger','float','long']:
        current = mc.getAttr(node+'.'+node_address)
        print(current)
        if float(current) > .5 :
            mc.setAttr(node+'.'+node_address,0)
        else:
            mc.setAttr(node+'.'+node_address,1)
    
    if type in ['bool']:
        plug = mc.getAttr(node+'.'+node_address)
        current = mc.getAttr(node+'.'+node_address)
        if current:
            mc.setAttr(node+'.'+node_address,False)
            print(node+'.'+node_address,False)
        else:
            mc.setAttr(node+'.'+node_address,True)

def perform_match_ik_fk(node, *args):
    # Get
    
    ik_wrist = mc.listConnections(node+".IK_WRIST_MARKER",s=0,d=1)
    fk_wrist = mc.listConnections(node+".FK_WRIST_MARKER",s=0,d=1)
    ik_match_vector = mc.listConnections(node+".IK_MATCH_VECTOR_MARKER",s=0,d=1)
    ik_vector_ctrl = mc.listConnections(node+".IK_VECTOR_CTRL_MARKER",s=0,d=1)
    
    # Query
    if mc.attributeQuery("ikSnap",node=node,exists=True):
        ikSnap = mc.listConnections(node+".ikSnap")[0]
        wrist_location = mc.xform(ikSnap,q=1,m=1,ws=1)
    else:
        wrist_location = mc.xform(fk_wrist,q=1,m=1,ws=1)
    elbow_location = mc.xform(ik_match_vector,q=1,m=1,ws=1)
    
    # Set
    mc.xform(ik_wrist,m=wrist_location,ws=1)
    mc.xform(ik_vector_ctrl,m=elbow_location,ws=1)
    flip_switch_attr(node)

def perform_match_fk_ik(node, *args):
    # Get
    ik_wrist = mc.listConnections(node+".IK_WRIST_MARKER",s=0,d=1)
    fk_wrist = mc.listConnections(node+".FK_WRIST_MARKER",s=0,d=1)
    fk_shoulder = mc.listConnections(node+".FK_SHOULDER_MARKER",s=0,d=1)
    fk_elbow = mc.listConnections(node+".FK_ELBOW_MARKER",s=0,d=1)
    ik_elbow = mc.listConnections(node+".IK_ELBOW_MARKER",s=0,d=1)
    ik_shoulder = mc.listConnections(node+".IK_SHOULDER_MARKER",s=0,d=1)
            
    # Query
    if mc.attributeQuery("fkSnap",node=node,exists=True):
        fkSnap = mc.listConnections(node+".fkSnap")[0]
        wrist_location = mc.xform(fkSnap,q=1,m=1,ws=1)
    else:
        wrist_location = mc.xform(ik_wrist,q=1,m=1,ws=1)
    
    """
    --- old version --- used getAttr to get rid of the wrong rotation values
    
    elbow_location = mc.xform(ik_elbow,q=1,m=1,ws=1)
    shoulder_location = mc.xform(ik_shoulder,q=1,m=1,ws=1)
    
    # Set
    mc.xform(fk_shoulder,m=shoulder_location,ws=1)
    mc.xform(fk_elbow,m=elbow_location,ws=1)
    mc.xform(fk_wrist,m=wrist_location,ws=1)
    """
    
    elbow_rotation = mc.getAttr(ik_elbow[0] + ".r")[0]
    shoulder_rotation = mc.getAttr(ik_shoulder[0] + ".r")[0]
    mc.setAttr(fk_shoulder[0] + ".r", shoulder_rotation[0], shoulder_rotation[1], shoulder_rotation[2])
    mc.setAttr(fk_elbow[0] + ".r", elbow_rotation[0], elbow_rotation[1], elbow_rotation[2])
    mc.xform(fk_wrist,m=wrist_location,ws=1)
    
    flip_switch_attr(node)
## END IK FK MATCH BLOCK
