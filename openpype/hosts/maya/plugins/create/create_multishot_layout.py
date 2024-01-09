from ayon_api import (
    get_folder_by_name,
    get_folder_by_path,
    get_folders,
)
from maya import cmds  # noqa: F401

from openpype import AYON_SERVER_ENABLED
from openpype.client import get_assets
from openpype.hosts.maya.api import plugin
from openpype.lib import BoolDef, EnumDef, TextDef
from openpype.pipeline import (
    Creator,
    get_current_asset_name,
    get_current_project_name,
)


from openpype.pipeline.create import CreatorError


class CreateMultishotLayout(plugin.MayaCreator):
    """Create a multi-shot layout in the Maya scene.

    This creator will create a Camera Sequencer in the Maya scene based on
    the shots found under the specified folder. The shots will be added to
    the sequencer in the order of their clipIn and clipOut values. For each
    shot a Layout will be created.

    """
    identifier = "io.openpype.creators.maya.multishotlayout"
    label = "Camera Sequencer Layout Files"
    family = "layout"
    icon = "project-diagram"

    def get_pre_create_attr_defs(self):
        # Present artist with a list of parents of the current context
        # to choose from. This will be used to get the shots under the
        # selected folder to create the Camera Sequencer.

        """
        Todo: `get_folder_by_name` should be switched to `get_folder_by_path`
              once the fork to pure AYON is done.

        Warning: this will not work for projects where the asset name
                 is not unique across the project until the switch mentioned
                 above is done.
        """


        project_name = get_current_project_name()
        folder_path = get_current_asset_name()
        if "/" in folder_path:
            current_folder = get_folder_by_path(project_name, folder_path)
        else:
            current_folder = get_folder_by_name(
                project_name, folder_name=folder_path
            )

        current_path_parts = current_folder["path"].split("/")

        # populate the list with parents of the current folder
        # this will create menu items like:
        # [
        #   {
        #       "value": "",
        #       "label": "project (shots directly under the project)"
        #   }, {
        #       "value": "shots/shot_01", "label": "shot_01 (current)"
        #   }, {
        #       "value": "shots", "label": "shots"
        #   }
        # ]

        # add the project as the first item
        items_with_label = [
            {
                "label": f"{self.project_name} "
                         "(shots directly under the project)",
                "value": ""
            }
        ]

        # go through the current folder path and add each part to the list,
        # but mark the current folder.
        for part_idx, part in enumerate(current_path_parts):
            label = part
            if label == current_folder["name"]:
                label = f"{label} (current)"

            value = "/".join(current_path_parts[:part_idx + 1])

            items_with_label.append({"label": label, "value": value})

        # Remove the project and production folder from the children option
        del items_with_label[0]
        del items_with_label[0]
        del items_with_label[0]

        return [
            EnumDef("shotParent",
                    default=current_folder["name"],
                    label="Shot Parent Folder",
                    items=items_with_label,
                    ),
            BoolDef("groupLoadedAssets",
                    label="Group Loaded Assets",
                    tooltip="Enable this when you want to publish group of "
                            "loaded asset",
                    default=False),
            TextDef("taskName",
                    label="Associated Task Name",
                    tooltip=("Task name to be associated "
                             "with the created Layout"),
                    default="Layout"),
        ]

    def create(self, subset_name, instance_data, pre_create_data):
        shots = list(
            self.get_related_shots(folder_path=pre_create_data["shotParent"])
        )
        if not shots:
            # There are no shot folders under the specified folder.
            # We are raising an error here but in the future we might
            # want to create a new shot folders by publishing the layouts
            # and shot defined in the sequencer. Sort of editorial publish
            # in side of Maya.
            raise CreatorError((
                "No shots found under the specified "
                f"folder: {pre_create_data['shotParent']}."))

        # Get layout creator
        layout_creator_id = "io.openpype.creators.maya.layoutMayaFile"
        layout_creator: Creator = self.create_context.creators.get(
            layout_creator_id)
        if not layout_creator:
            raise CreatorError(
                f"Creator {layout_creator_id} not found.")

        # TODO: Remove in later copies of ayon
        layout_creator.default_variant = "Main"

        # Get camera creator
        camera_creator_id = "io.openpype.creators.maya.camera"
        camera_creator: Creator = self.create_context.creators.get(
            camera_creator_id)
        if not layout_creator:
            raise camera_creator(
                f"Creator {camera_creator_id} not found.")
        # TODO: Remove in later copies of ayon
        camera_creator.default_variant = "Main"


        # Get OpenPype style asset documents for the shots
        op_asset_docs = get_assets(
            self.project_name, [s["id"] for s in shots])
        asset_docs_by_id = {doc["_id"]: doc for doc in op_asset_docs}

        for shot in shots:
            # we are setting shot name to be displayed in the sequencer to
            # `shot name (shot label)` if the label is set, otherwise just
            # `shot name`. So far, labels are used only when the name is set
            # with characters that are not allowed in the shot name.
            if not shot["active"]:
                continue

            # get task for shot
            asset_doc = asset_docs_by_id[shot["id"]]

            tasks = asset_doc.get("data").get("tasks").keys()
            layout_task = None
            if pre_create_data["taskName"] in tasks:
                layout_task = pre_create_data["taskName"]

            shot_name = shot['name']

            # Find existing Shot
            print("Looknig For -",shot_name,"-")
            _existingShot = cmds.ls(shot_name,et="shot")
            if not _existingShot:

                _shotNode = cmds.shot(sequenceStartTime=shot["attrib"]["clipIn"],
                        st=shot["attrib"]["clipIn"],
                        et=shot["attrib"]["clipOut"],
                        shotName=shot_name)
                _shotNode = cmds.rename(_shotNode,shot_name)
                cmds.addAttr(_shotNode, longName='__shotNode', attributeType='message' )

            else:
                _shotNode = _existingShot[0]
                cmds.shot(
                        _shotNode,
                        edit=True,
                        sequenceStartTime=shot["attrib"]["clipIn"],
                        st=shot["attrib"]["clipIn"],
                        et=shot["attrib"]["clipOut"]
                        )
            print(123,pre_create_data)
            # Create layout instance by the layout creator

            #import pdb
            #pdb.set_trace()
            instance_data = {
                "asset": shot["name"],
                "variant": layout_creator.get_default_variant()
            }
            if layout_task:
                instance_data["task"] = layout_task

            _layoutSubsetName = shot["name"]+"_"+layout_creator.get_subset_name(
                    layout_creator.get_default_variant(),
                    self.create_context.get_current_task_name(),
                    asset_doc,
                    self.project_name)

            _cameraSubsetName = shot["name"]+"_"+camera_creator.get_subset_name(
                    camera_creator.get_default_variant(),
                    self.create_context.get_current_task_name(),
                    asset_doc,
                    self.project_name)

            _existingLayoutSubset = ([s for s in cmds.ls("*.subset") if cmds.getAttr(s) == _layoutSubsetName])
            _existingCameraSubset = ([s for s in cmds.ls("*.subset") if cmds.getAttr(s) == _cameraSubsetName])

            #
            # Make the Layout Publish Set
            #

            if not _existingLayoutSubset:

                _publishLayoutInstance = layout_creator.create(
                    subset_name=_layoutSubsetName,
                    instance_data=instance_data,
                    pre_create_data={
                        "groupLoadedAssets": pre_create_data["groupLoadedAssets"]
                    }
                )
                _layoutPublishSet=_publishLayoutInstance.get("instance_node")

                cmds.addAttr(_layoutPublishSet, longName='__shotNode', attributeType='message' )
                cmds.addAttr(_layoutPublishSet, longName='__cameraSet', attributeType='message' )

            else:
                _layoutPublishSet = _existingLayoutSubset[0].split(".")[0]

            if not _existingCameraSubset:
                _publishCameraInstance = camera_creator.create(
                    subset_name=_cameraSubsetName,
                    instance_data=instance_data,
                    pre_create_data={}
                )
                _cameraPublishSet=_publishCameraInstance.get("instance_node")
                cmds.setAttr(_cameraPublishSet+".frameStart",shot["attrib"]["frameStart"])
                cmds.setAttr(_cameraPublishSet+".frameEnd",shot["attrib"]["frameEnd"])
                cmds.setAttr(_cameraPublishSet+".handleStart",shot["attrib"]["handleStart"])
                cmds.setAttr(_cameraPublishSet+".handleEnd",shot["attrib"]["handleEnd"])
                cmds.setAttr(_cameraPublishSet+".shiftSequenceAmimation",True)

                cmds.addAttr(_cameraPublishSet, longName='__cameraSet', attributeType='message' )

            else:
                _cameraPublishSet = _existingCameraSubset[0].split(".")[0]

            conns = cmds.listConnections(_shotNode+".__shotNode",p=True,s=0,d=1) or []
            if not _layoutPublishSet+".__shotNode" in conns:
                cmds.connectAttr(_shotNode+".__shotNode",_layoutPublishSet+".__shotNode",force=True)

            conns = cmds.listConnections(_layoutPublishSet+".__cameraSet",p=True,s=0,d=1) or []
            if not _cameraPublishSet+".__cameraSet" in conns:
                cmds.connectAttr(_layoutPublishSet+".__cameraSet",  _cameraPublishSet+".__cameraSet",force=True)


    def get_related_shots(self, folder_path: str):
        """Get all shots related to the current asset.

        Get all folders of type Shot under specified folder.

        Args:
            folder_path (str): Path of the folder.

        Returns:
            list: List of dicts with folder data.

        """
        # if folder_path is None, project is selected as a root
        # and its name is used as a parent id
        parent_id = self.project_name
        if folder_path:
            current_folder = get_folder_by_path(
                project_name=self.project_name,
                folder_path=folder_path,
            )
            parent_id = current_folder["id"]

        return get_shot_from_hierarchy(
            project_name=self.project_name,
            parent_ids=[parent_id],
        )


def get_shot_from_hierarchy(project_name,parent_ids,found = []):
    newFound = get_folders(
        project_name=project_name,
        parent_ids=parent_ids,
        fields=[
            "attrib.clipIn", "attrib.clipOut",
            "attrib.frameStart", "attrib.frameEnd",
            "attrib.handleStart", "attrib.handleEnd",
            "name", "label", "path", "folderType", "id"
        ])
    newFound = [f for f in newFound ]
    foundIds = [ x['id'] for x in found ]
    newFound = [f for f in newFound if f['id'] not in foundIds ]
    found.extend(newFound)
    for f in newFound:
        found = get_shot_from_hierarchy(project_name,[f["id"]],found = found)
    found = [f for f in found if f['folderType'] == "Shot"]
    return found


# blast this creator if Ayon server is not enabled
if not AYON_SERVER_ENABLED:
    del CreateMultishotLayout
