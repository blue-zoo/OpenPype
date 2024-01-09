import math
import os
import json

from maya import cmds
from maya.api import OpenMaya as om

from openpype.client import get_representation_by_id
from openpype.pipeline import publish


class ExtractLayoutMayaFile(publish.Extractor):
    """Extract a layout."""

    label = "Extract Layout Scene"
    hosts = ["maya"]
    families = ["layout_multi"]
    project_container = "AVALON_CONTAINERS"
    optional = True
    scene_type = "ma"

    def process(self, instance):
        import os
        # Define extract output file path
        stagingdir = self.staging_dir(instance)

        # Perform extraction
        self.log.info("Performing extraction..")

        if "representations" not in instance.data:
            instance.data["representations"] = []

        json_data = []
        # TODO representation queries can be refactored to be faster
        project_name = instance.context.data["projectName"]
        _instanceSet = str(instance)

        # Shot node
        _shotNodes = cmds.listConnections(_instanceSet+".__shotNode",d=0,s=1)
        if not _shotNodes or len(_shotNodes) != 1:
            raise Exception('The Instance Set "{s}" does not have a single linked Camera Seqeuncer Shot'.format(s=_instanceSet) )

        _shotNode = _shotNodes[0]

        cmds.file(save=True,force=True)
        _orginalfile = cmds.file(q=1,sn=1)

        # Set frame to the correct Frame time
        _layoutShotStartFrame = instance.data.get("assetEntity").get("data").get("frameStart")
        _layoutShotEndFrame = instance.data.get("assetEntity").get("data").get("frameEnd")
        _layoutShotStartHandle = instance.data.get("assetEntity").get("data").get("handleStart")
        _layoutShotEndHandle = instance.data.get("assetEntity").get("data").get("handleEnd")

        cmds.currentTime(_layoutShotStartFrame)

        for asset in cmds.sets(_instanceSet, query=True):

            # Find the container
            project_container = self.project_container
            container_list = cmds.ls(project_container)

            if len(container_list) == 0:
                self.log.warning("Project container is not found!")
                self.log.warning("The asset(s) may not be properly loaded after published") # noqa
                continue

            grp_loaded_ass = instance.data.get("groupLoadedAssets", False)
            if grp_loaded_ass:
                asset_list = cmds.listRelatives(asset, children=True)
                for asset in asset_list:
                    grp_name = asset.split(':')[0]
            else:
                grp_name = asset.split(':')[0]
            containers = cmds.ls("{}*_CON".format(grp_name))
            if len(containers) == 0:
                self.log.warning("{} isn't from the loader".format(asset))
                self.log.warning("It may not be properly loaded after published") # noqa
                continue
            container = containers[0]

            representation_id = cmds.getAttr(
                "{}.representation".format(container))

            representation = get_representation_by_id(
                project_name,
                representation_id,
                fields=["parent", "context.family"]
            )

            self.log.info(representation)

            version_id = representation.get("parent")
            family = representation.get("context").get("family")

            json_element = {
                "family": family,
                "instance_name": cmds.getAttr(
                    "{}.namespace".format(container)),
                "representation": str(representation_id),
                "version": str(version_id)
            }

            loc = cmds.xform(asset, query=True, translation=True)
            rot = cmds.xform(asset, query=True, rotation=True, euler=True)
            scl = cmds.xform(asset, query=True, relative=True, scale=True)

            json_element["transform"] = {
                "translation": {
                    "x": loc[0],
                    "y": loc[1],
                    "z": loc[2]
                },
                "rotation": {
                    "x": math.radians(rot[0]),
                    "y": math.radians(rot[1]),
                    "z": math.radians(rot[2])
                },
                "scale": {
                    "x": scl[0],
                    "y": scl[1],
                    "z": scl[2]
                }
            }

            row_length = 4
            t_matrix_list = cmds.xform(asset, query=True, matrix=True)

            transform_mm = om.MMatrix(t_matrix_list)
            transform = om.MTransformationMatrix(transform_mm)

            t = transform.translation(om.MSpace.kWorld)
            t = om.MVector(t.x, t.z, -t.y)
            transform.setTranslation(t, om.MSpace.kWorld)
            transform.rotateBy(
                om.MEulerRotation(math.radians(-90), 0, 0), om.MSpace.kWorld)
            transform.scaleBy([1.0, 1.0, -1.0], om.MSpace.kObject)

            t_matrix_list = list(transform.asMatrix())

            t_matrix = []
            for i in range(0, len(t_matrix_list), row_length):
                t_matrix.append(t_matrix_list[i:i + row_length])

            json_element["transform_matrix"] = [
                list(row)
                for row in t_matrix
            ]

            basis_list = [
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, -1, 0,
                0, 0, 0, 1
            ]

            basis_mm = om.MMatrix(basis_list)
            basis = om.MTransformationMatrix(basis_mm)

            b_matrix_list = list(basis.asMatrix())
            b_matrix = []

            for i in range(0, len(b_matrix_list), row_length):
                b_matrix.append(b_matrix_list[i:i + row_length])

            json_element["basis"] = []
            for row in b_matrix:
                json_element["basis"].append(list(row))

            json_data.append(json_element)

        json_filename = "{}.json".format(instance.name)
        json_path = os.path.join(stagingdir, json_filename)

        with open(json_path, "w+") as file:
            json.dump(json_data, fp=file, indent=2)

        json_representation = {
            'name': 'json',
            'ext': 'json',
            'files': json_filename,
            "stagingDir": stagingdir,
        }

        instance.data["representations"].append(json_representation)

        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}.{1}".format(instance.name, self.scene_type)
        path = os.path.join(dir_path, filename)

        _layoutPublishSet = instance.data.get("instance_node")
        _layoutPublishSetMembers = cmds.sets( _layoutPublishSet, q=True )
        _cameraPublishSets = cmds.listConnections(_layoutPublishSet+".__cameraSet",s=0,d=1) or []
        _layoutShotNodes = cmds.listConnections(_layoutPublishSet+".__shotNode",s=1,d=0) or []

        # To Export Selection
        _toExport = [_layoutPublishSet]
        _layoutPublishSetMembers = [ n for n in cmds.ls(_layoutPublishSetMembers,long=True)  ]
        _toExport.extend( _layoutPublishSetMembers )

        # Go through the animation reference containers and add them to the exportable sets
        _layoutPublishSetMembersChildren = cmds.listRelatives(_layoutPublishSetMembers, c=True) or []
        _layoutReferenceNodes = [cmds.referenceQuery(n, rfn=True ) for n in _layoutPublishSetMembersChildren if cmds.referenceQuery(n, inr=True )]
        _allReferenceSets = cmds.ls("*.loader", long=True, type="objectSet", recursive=True,
                        objectsOnly=True) or []
        _referenceLoaderSets = [set for set in _allReferenceSets for setContent in cmds.sets( set, q=True ) if setContent in _layoutReferenceNodes ]
        _toExport.extend( _referenceLoaderSets )

        if _cameraPublishSets:
            _cameraPublishSet = _cameraPublishSets[0]
            _cameraPublishSetMembers = cmds.sets( _cameraPublishSet, q=True )
            _cameraPublishSetMembers = [ n for n in cmds.ls(_cameraPublishSetMembers,long=True)  ]

            _toExport.append( _cameraPublishSet )
            _toExport.extend( _cameraPublishSetMembers )

        if _layoutShotNodes:
            _layoutShotNode = _layoutShotNodes[0]
            _shotNodeSequenceStartFrame = cmds.shot(_layoutShotNode,sequenceStartTime=True,query=True)


        # As this is altering the layout scene do in an exception loop that will open the original file.

        try:
            # Add other publish sets that were referenced in the layout / camera publish sets
            _allSets = cmds.ls("*.creator_identifier", long=True, type="objectSet", recursive=True,
                            objectsOnly=True) or []
            _allSets = [s for s in _allSets if cmds.getAttr(s+".creator_identifier") not in  ["io.openpype.creators.maya.layoutMayaFile","io.openpype.creators.maya.camera"] ]
            for set in _allSets:
                members = cmds.sets(set,q=True) or []
                for member in members:
                    for dag in cmds.ls(member,long=True):
                        if dag in _toExport:
                            _toExport.append( set )
                            continue

            # Set the publishing instance to regular publish
            cmds.setAttr(_layoutPublishSet+".creator_identifier","io.openpype.creators.maya.layout",type="string")
            cmds.setAttr(_layoutPublishSet+".family","layout",type="string")
            _preExportTask = cmds.getAttr(_layoutPublishSet+".task")
            _preExportFolderPath = cmds.getAttr(_layoutPublishSet+".folderPath")

            # Set all of the tasks to Animation on all publoshign instances
            _allSets = cmds.ls("*.creator_identifier", long=True, type="objectSet", recursive=True,
                            objectsOnly=True) or []

            for _set in _allSets:
                cmds.setAttr(_set+".task","Animation",type="string")
                # If its an animation publish set its folder path to the shot and the time to the shot time
                if cmds.getAttr(_set+".creator_identifier") in  ["io.openpype.creators.maya.animation"]:
                    cmds.setAttr(_set+".folderPath",_preExportFolderPath,type="string")
                    cmds.setAttr(_set+".active",True)
                    cmds.setAttr(_set+".frameStart",_layoutShotStartFrame)
                    cmds.setAttr(_set+".frameEnd",_layoutShotEndFrame)
                    cmds.setAttr(_set+".handleStart",_layoutShotStartHandle)
                    cmds.setAttr(_set+".handleEnd",_layoutShotEndHandle)

            # Set the start and end frame of the camera publish to the shot
            cmds.setAttr(_cameraPublishSet+".frameStart",_layoutShotStartFrame)
            cmds.setAttr(_cameraPublishSet+".frameEnd",_layoutShotEndFrame)
            cmds.setAttr(_cameraPublishSet+".handleStart",_layoutShotStartHandle)
            cmds.setAttr(_cameraPublishSet+".handleEnd",_layoutShotEndHandle)
            cmds.setAttr(_cameraPublishSet+".shiftSequenceAmimation",False)

            # Adjust animation so that animation starts on start frame of shot
            _timeOffset = float(_layoutShotStartFrame) - float(_shotNodeSequenceStartFrame)
            self.log.info('Offsetting {s} by {f}'.format(s= instance.data.get("name") ,f=_timeOffset))
            offsetAllKeys(_timeOffset)

            # Select everything to export
            cmds.select( _toExport ,replace=True,noExpand=True)

            cmds.file(path,
                        force=True,
                        typ="mayaAscii" if self.scene_type == "ma" else "mayaBinary",  # noqa: E501
                        exportSelected=True,
                        preserveReferences=True,
                        channels=True,
                        constraints=True,
                        expressions=True,
                        constructionHistory=True)

            if "representations" not in instance.data:
                instance.data["representations"] = []

            # Set the publish back to multi layout, and all publish instances back to
            # the original task

            cmds.setAttr(_layoutPublishSet+".creator_identifier","io.openpype.creators.maya.multishotlayout",type="string")
            cmds.setAttr(_layoutPublishSet+".family","layout_multi",type="string")
            for _set in _allSets:
                cmds.setAttr(_set+".task",_preExportTask,type="string")

                # If its an animation publish set its folder path to the shot
                if cmds.getAttr(_set+".creator_identifier") in  ["io.openpype.creators.maya.animation"]:
                    cmds.setAttr(_set+".folderPath",_preExportFolderPath,type="string")
                    cmds.setAttr(_set+".active",False)

            representation = {
                'name': self.scene_type,
                'ext': self.scene_type,
                'files': filename,
                "stagingDir": dir_path
            }
            instance.data["representations"].append(representation)
            self.log.info("Extracted instance '%s' to: %s" % (instance.name, path))

        except Exception as e:
            cmds.file( _orginalfile ,open=True,force=True)
            raise e
        else:
            cmds.file( _orginalfile ,open=True,force=True)



def offsetAllKeys( offset, includeReferenced=False):
    """
    startFrame : int : Where should the offset begin?
    offset : int : How large should the offset be?
    includeReferenced : bool : Default False : Should referenced animCurves be
        included?
    """
    animCurves = cmds.ls(type='animCurve')
    if not includeReferenced:
        animCurves = [ac for ac in animCurves if not cmds.referenceQuery(ac,inr=True) ]

    if animCurves:
        cmds.keyframe(animCurves, edit=True, includeUpperBound=False, animation="objects",
                    time=(), relative=True, option='over', timeChange=offset)
