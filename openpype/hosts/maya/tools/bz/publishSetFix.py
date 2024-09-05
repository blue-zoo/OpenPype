
def fixPublishSetNames():
    import maya.cmds as cmds
    publishSets = [s for s in cmds.ls(et="objectSet") if cmds.ls(s+".creator_identifier") if cmds.getAttr(s+".family") == "animation" ]
    for set in publishSets:
        subset = cmds.getAttr(set+".subset")
        short = subset.replace("animation","")
        short = short.replace("_rigMain","")
        print("renaming ",set," as ", short)
        cmds.setAttr(set+".subset", short,type="string")
        cmds.rename(set,short)
