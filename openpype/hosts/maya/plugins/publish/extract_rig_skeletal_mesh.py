# -*- coding: utf-8 -*-
"""Create Unreal Skeletal Mesh data to be extracted as FBX."""
import os
from contextlib import contextmanager

from maya import cmds  # noqa

import pyblish.api

from openpype.pipeline import publish
from openpype.hosts.maya.api import fbx
from openpype.hosts.maya.api.lib import maintained_selection


class ExtractUnrealSkeletalMeshFbx(publish.Extractor):
    """Extract Unreal Skeletal Mesh as FBX from Maya. """

    order = pyblish.api.ExtractorOrder - 0.1
    label = "Extract Unreal Skeletal Mesh - FBX"
    hosts = ["maya"]
    families = ["rirg"]
    optional = True

    def process(self, instance):
        fbx_exporter = fbx.FBXExtractor(log=self.log)

        # Define output path
        staging_dir = self.staging_dir(instance)
        filename = "{0}.fbx".format(instance.name)
        path = os.path.join(staging_dir, filename)
        import pdb
        pdb.set_trace()
        set_members =  instance.data.get("setMembers",[])
        geo = [s for s in set_members if s.endswith("out_SET")]
        joints = [s for s in set_members if s.endswith("joints_SET")]
        if not len(joints) == 1 or not len(geo) == 1:
            self.log.info('No "joints_SET" or "out_SET detected')
            return


        to_extract = geo + joints

        # The export requires forward slashes because we need
        # to format it into a string in a mel expression
        path = path.replace('\\', '/')

        self.log.info("Extracting FBX to: {0}".format(path))
        self.log.info("Members: {0}".format(to_extract))
        self.log.info("Instance: {0}".format(instance[:]))

        fbx_exporter.set_options_from_instance(instance)

        # This magic is done for variants. To let Unreal merge correctly
        # existing data, top node must have the same name. So for every
        # variant we extract we need to rename top node of the rig correctly.
        # It is finally done in context manager so it won't affect current
        # scene.

        # we rely on hierarchy under one root.
        '''
        original_parent = to_extract[0].split("|")[1]

        parent_node = instance.data.get("asset")

        renamed_to_extract = []
        for node in to_extract:
            node_path = node.split("|")
            node_path[1] = parent_node
            renamed_to_extract.append("|".join(node_path))
        '''

        fbx_exporter.set_options_from_instance(instance)

        # Export
        with maintained_selection():
            cmds.select(to_extract, r=1, noExpand=True)
            fbx_exporter.export(to_extract, path)

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': 'fbx',
            'ext': 'fbx',
            'files': filename,
            "stagingDir": staging_dir,
        }
        instance.data["representations"].append(representation)

        self.log.info("Extract FBX successful to: {0}".format(path))


class ExtractUnrealSkeletalMeshFbxRig(ExtractUnrealSkeletalMeshFbx):
    """Extract Unreal Skeletal Mesh as FBX from Maya. """

    order = pyblish.api.ExtractorOrder - 0.1
    label = "Extract Unreal Skeletal Mesh - FBX"
    hosts = ["maya"]
    families = ["rirg"]
    optional = True

    def process(self, instance):
        import pdb;pdb.set_trace()

        super().process(instance)
