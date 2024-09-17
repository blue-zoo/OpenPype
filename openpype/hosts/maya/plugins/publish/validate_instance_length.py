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
from openpype.pipeline import (
    get_current_asset_name,
    get_current_project_name,
    Anatomy
)
import copy
from maya import cmds


class ValidateInstanceLength(pyblish.api.InstancePlugin,
                                OptionalPyblishPluginMixin):
    """Validator to check if instance asset match context asset.

    When working in per-shot style you always publish data in context of
    current asset (shot). This validator checks if this is so. It is optional
    so it can be disabled when needed.

    Action on this validator will select invalid instances in Outliner.
    """

    order = ValidateContentsOrder
    label = "Instance Set Name Length"
    optional = False
    hosts = ["maya"]
    families = ["animation"]

    actions = [
        openpype.hosts.maya.api.action.SelectInvalidAction, RepairAction
    ]



    def process(self, instance):

        if not self.is_active(instance.data):
            return

        _subset = instance.data.get("subset")
        path = self.getFilePathLength(instance,_subset)

        if len(path) > 259:
            mess = "Instance '{m}' Publish Set Name will make a file path greater than 260 ".format(m=instance.name)
            raise PublishValidationError(
                message=mess,
                description=("## Cannot make a file with this length")
            )

    @classmethod
    def get_invalid(cls, instance):
        return [instance.data["instance_node"]]

    @classmethod
    def repair(cls, instance):


        _subsetName = copy.copy( instance.data.get("instance_node"))
        _subsetNamNoAnimation = _subsetName
        while(  len(cls.getFilePathLength(instance,_subsetNamNoAnimation)) > 259 and not doesExist(_subsetNamNoAnimation) ):
            _subsetNamNoAnimation = _subsetNamNoAnimation[ 0: len(_subsetNamNoAnimation)-1 ]

        cmds.setAttr(_subsetName+".subset",_subsetNamNoAnimation,type="string")
        cmds.rename(_subsetName,_subsetNamNoAnimation)


    @classmethod
    def getFilePathLength(self,instance,_subset):
        anatomy = Anatomy()
        _sourceRoot = anatomy.roots['sourceRoot'].value

        _folder = instance.data.get("asset")
        _shot = instance.data.get("assetEntity").get("name")
        _code = instance.data.get("projectEntity").get("code")

        _path = "{source}{hier}/publish/animation/{subset}/v000/{code}_{shot}_{subset}_v000_fbxanim.fbx".format(
            source = _sourceRoot,
            hier = _folder,
            shot = _shot,
            subset = _subset,
            code = _code


        )
        print(_path)
        print(len(_path))
        #import pdb;pdb.set_trace()

        return _path


    @staticmethod
    def get_context_asset(instance):
        return instance.context.data["asset"]

def doesExist(name):
    if name in cmds.ls("*.subset" ):
        return True
