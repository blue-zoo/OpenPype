# -*- coding: utf-8 -*-
"""Validate if instance asset is the same as context asset."""
from __future__ import absolute_import

import pyblish.api
from openpype import AYON_SERVER_ENABLED
import openpype.hosts.maya.api.action
from openpype.pipeline.publish import (
    RepairAction,
    ValidateContentsOrder,
    PublishValidationError,
    OptionalPyblishPluginMixin
)

from maya import cmds


class ValidateInstanceInContext(pyblish.api.InstancePlugin,
                                OptionalPyblishPluginMixin):
    """Validator to check if instance asset match context asset.

    When working in per-shot style you always publish data in context of
    current asset (shot). This validator checks if this is so. It is optional
    so it can be disabled when needed.

    Action on this validator will select invalid instances in Outliner.
    """

    order = ValidateContentsOrder
    label = "Instance in same Context"
    optional = True
    hosts = ["maya"]
    actions = [
        openpype.hosts.maya.api.action.SelectInvalidAction, RepairAction
    ]

    def process(self, instance):
        if not self.is_active(instance.data):
            return

        # Multiple Layout publishes going on in layout breakout.
        if instance.data.get("task") == 'Layout':
            return

        _allSets = cmds.ls("*.creator_identifier", long=True, type="objectSet", recursive=True,
                        objectsOnly=True) or []
        _RigSets = [s for s in _allSets if cmds.getAttr(s+".creator_identifier") in  ["io.openpype.creators.maya.rig"] ]
        _staticProxyMeshSets = [s for s in _allSets if cmds.getAttr(s+".creator_identifier") in  ["io.openpype.creators.maya.unreal_maya_placeholder"] ]


        # There is a static proxy and a rig Set
        if _RigSets and _staticProxyMeshSets:
            if "Environments" in instance.data.get("assetEntity",{}).get("data",{}).get("parents",[]):
                self.log.info("Skipping Instance / context check")
                return

        asset = instance.data.get("asset")
        context_asset = self.get_context_asset(instance)
        if asset != context_asset:
            raise PublishValidationError(
                message=(
                    "Instance '{}' publishes to different asset than current "
                    "context: {}. Current context: {}".format(
                        instance.name, asset, context_asset
                    )
                ),
                description=(
                    "## Publishing to a different asset\n"
                    "There are publish instances present which are publishing "
                    "into a different asset than your current context.\n\n"
                    "Usually this is not what you want but there can be cases "
                    "where you might want to publish into another asset or "
                    "shot. If that's the case you can disable the validation "
                    "on the instance to ignore it."
                )
            )

    @classmethod
    def get_invalid(cls, instance):
        return [instance.data["instance_node"]]

    @classmethod
    def repair(cls, instance):
        context_asset = cls.get_context_asset(instance)
        instance_node = instance.data["instance_node"]
        if AYON_SERVER_ENABLED:
            asset_name_attr = "folderPath"
        else:
            asset_name_attr = "asset"
        cmds.setAttr(
            "{}.{}".format(instance_node, asset_name_attr),
            context_asset,
            type="string"
        )

    @staticmethod
    def get_context_asset(instance):
        return instance.context.data["asset"]
