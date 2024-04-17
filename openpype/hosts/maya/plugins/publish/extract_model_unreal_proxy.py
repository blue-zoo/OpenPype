# -*- coding: utf-8 -*-
"""Extract model as Maya Scene."""
import os

from maya import cmds

from openpype.pipeline import publish
from openpype.hosts.maya.api import lib
from openpype.hosts.maya.api.lib import (
    extract_alembic,
    suspended_refresh,
    maintained_selection,
    iter_visible_nodes_in_range
)


class ExtractModelProxy(publish.Extractor):
    """Extract as Model (Maya Scene).

    Only extracts contents based on the original "setMembers" data to ensure
    publishing the least amount of required shapes. From that it only takes
    the shapes that are not intermediateObjects

    During export it sets a temporary context to perform a clean extraction.
    The context ensures:
        - Smooth preview is turned off for the geometry
        - Default shader is assigned (no materials are exported)
        - Remove display layers

    """

    label = "Maya Placeholder"
    hosts = ["maya"]
    families = ["placeholder"]

    def process(self, instance):

        """Plugin entry point."""

        # Define extract output file path
        stagingdir = self.staging_dir(instance)
        filename = "{0}.abc".format(instance.name)
        path = os.path.join(stagingdir, filename)

        # Perform extraction
        self.log.info("Performing extraction ... to {p}".format(p=path))

        # Get only the shape contents we need in such a way that we avoid
        # taking along intermediateObjects
        members = instance.data("setMembers")

        start = float(instance.data.get("frameStart", 100))
        end = float(instance.data.get("frameStart", 100))


        options = {
            "step": 1.0,
            "writeVisibility": True,
            "writeCreases": True,
            "writeColorSets": False,
            "writeFaceSets": False,
            "uvWrite": True,
            "selection": True,
            "worldSpace": True
        }

        options["writeUVSets"] = True

        _toExport = []
        for member in members:
            _toExport.extend(cmds.listRelatives(member, ad=1, typ='mesh', fullPath = True, noIntermediate=True) or [])
        _toExport.extend(members)

        with suspended_refresh(suspend=True):
            with maintained_selection():
                cmds.select(_toExport, noExpand=True)
                sel = cmds.ls(sl=1)
                print("sel: ",sel)
                extract_alembic(
                    file=path,
                    startFrame=start,
                    endFrame=end,
                    **options,
                    verbose=True
                )

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': 'abc',
            'ext': 'abc',
            'files': filename,
            "stagingDir": stagingdir,
        }

        instance.data["representations"].append(representation)
        self.log.info("Extracted instance '%s' to: %s" % (instance.name, path))
