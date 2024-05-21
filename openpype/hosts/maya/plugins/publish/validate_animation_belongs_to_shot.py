import pyblish.api
import openpype.hosts.maya.api.action
from openpype.pipeline.context_tools import get_current_context
from openpype.pipeline.publish import (
    RepairAction,
    PublishValidationError,
    ValidateContentsOrder
)
from maya import cmds


class ValidateAnimationBelongsToShot(pyblish.api.InstancePlugin):
    """Animation publishing from a layout or animation file should
    always belong to the shot that layout or animation file belongs to."""

    order = ValidateContentsOrder
    hosts = ["maya"]
    families = ["animation"]
    label = "Validate Animation Belongs To Shot"
    actions = [openpype.hosts.maya.api.action.SelectInvalidAction,
               RepairAction]

    def process(self, instance):
        context = get_current_context()

        if context["asset_name"] != instance.data["asset"]:
            raise PublishValidationError(f'{instance.data["name"]} does not '
                                         f'belong to {context["asset_name"]}.',
                title="Animation instance does not belong to the current shot")

    @classmethod
    def get_invalid(cls, instance):
        return [instance.data["name"]]

    @classmethod
    def repair(cls, instance):
        context = get_current_context()
        cmds.setAttr(f'{instance.data["name"]}.folderPath',
                     context["asset_name"], typ="string")
        print(f'Repaired {instance.data["name"]}.')
