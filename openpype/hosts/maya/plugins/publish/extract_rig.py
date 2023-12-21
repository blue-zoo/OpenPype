# -*- coding: utf-8 -*-
"""Extract rig as Maya Scene."""
import os

from maya import cmds

from openpype.pipeline import publish
from openpype.hosts.maya.api.lib import maintained_selection
from openpype.hosts.maya.api import fbx


class ExtractRig(publish.Extractor):
    """Extract rig as Maya Scene."""

    label = "Extract Rig (Maya Scene)"
    hosts = ["maya"]
    families = ["_rig"]
    scene_type = "ma"


    def process(self, instance):
        """Plugin entry point."""
        ext_mapping = (
            instance.context.data["project_settings"]["maya"]["ext_mapping"]
        )
        if ext_mapping:
            self.log.debug("Looking in settings for scene type ...")
            # use extension mapping for first family found
            for family in self.families:
                try:
                    self.scene_type = ext_mapping[family]
                    self.log.info(
                        "Using '.{}' as scene type".format(self.scene_type))
                    break
                except AttributeError:
                    # no preset found
                    pass
        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}.{1}".format(instance.name, self.scene_type)
        path = os.path.join(dir_path, filename)

        # Perform extraction
        self.log.info("Performing extraction ...")
        with maintained_selection():
            cmds.select(instance, noExpand=True)
            cmds.file(path,
                      force=True,
                      typ="mayaAscii" if self.scene_type == "ma" else "mayaBinary",  # noqa: E501
                      exportSelected=True,
                      preserveReferences=False,
                      channels=True,
                      constraints=True,
                      expressions=True,
                      constructionHistory=True)

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': self.scene_type,
            'ext': self.scene_type,
            'files': filename,
            "stagingDir": dir_path
        }
        instance.data["representations"].append(representation)

        self.log.info("Extracted instance '%s' to: %s" % (instance.name, path))


class ExtractUnrealSkeletalMeshFbxRig(ExtractRig):
    """Extract Unreal Skeletal Mesh as FBX from Maya. """

    label = "Extract Unreal Skeletal Mesh - FBX"
    hosts = ["maya"]
    families = ["rig"]
    optional = True

    def process(self, instance):

        # Do the rig export prior to the publishing
        super().process(instance)

        _oldFile = cmds.file(q=1,sn=1)

        fbx_exporter = fbx.FBXExtractor(log=self.log)

        # Define output path
        staging_dir = self.staging_dir(instance)
        filename = "{0}.fbx".format(instance.name)
        path = os.path.join(staging_dir, filename)


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
        instance.data["upAxis"]="z"

        fbx_exporter.set_options_from_instance(instance)

        # This magic is done for variants. To let Unreal merge correctly
        # existing data, top node must have the same name. So for every
        # variant we extract we need to rename top node of the rig correctly.
        # It is finally done in context manager so it won't affect current
        # scene.

        # we rely on hierarchy under one root.

        # Export
        with maintained_selection():
            to_extract = [g for s in to_extract for g in cmds.sets(s, q=1)]
            cmds.select(to_extract, r=1, noExpand=True)

            print("EXPORTING ",to_extract)
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

        # Reopen
        cmds.file(_oldFile, open=True,force=True)
