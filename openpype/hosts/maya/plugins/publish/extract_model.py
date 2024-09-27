# -*- coding: utf-8 -*-
"""Extract model as Maya Scene."""
import os

from maya import cmds
from maya import cmds as mc

from openpype.pipeline import publish
from openpype.hosts.maya.api import lib

def unpinAllMeshUVs():
    '''Unpins any all pinned UVs for all UV sets for all mesh nodes.
    Necessary to eliminate crashes and dropped deformers.'''

    # Iterate all mesh nodes
    for mesh in mc.ls(typ="mesh"):

        # NOTE Before we can force-unpin and delete history we need to cache any incoming
        # mesh connections. We must disconnect these before deleting history, and restore
        # them afterwards. This process has potential so slow down publishing, but this
        # is very unlikely to become a bottleneck unless a model scene contains hundreds
        # of proxies or FX caches.

        # This step MUST be implemented in order to support necessary construction history
        # such as RedshiftProxyMesh and AlembicNode nodes.

        # Get incoming inMesh connections
        inMeshAttr = "{}.inMesh".format(mesh)
        inMeshSourcePlug = mc.listConnections(inMeshAttr, source=True, plugs=True)
        if inMeshSourcePlug:
            inMeshSourcePlug = inMeshSourcePlug[0]

            # Keep locked state and unlock if locked
            isLocked = mc.getAttr(inMeshAttr, lock=True)
            if isLocked:
                mc.setAttr(inMeshAttr, lock=False)

            # Disconnect incoming mesh attr
            mc.disconnectAttr(inMeshSourcePlug, inMeshAttr)

        # Bank orig selected set and iterate all sets
        origSet = mc.polyUVSet(mesh, q=1, currentUVSet=True)
        allSets = mc.polyUVSet(mesh, q=True, allUVSets=True)
        for set in allSets:

            # Switch active set and unpin all UVs
            mc.polyUVSet(mesh, currentUVSet=True, uvSet=set)
            mc.polyPinUV(mesh, op=2, ch=False)

        # Restore original selected set if one existed; otherwise, use first set
        # Don't ask me why no set would be selected, this just kept crashing.
        mc.polyUVSet(mesh, currentUVSet=True, uvSet=origSet[0] if origSet else allSets[0])

        # Delete non-deformer history
        mc.bakePartialHistory(mesh, preDeformers=True, prePostDeformers=True)

        # Restore connection and locked state if necessary
        if inMeshSourcePlug:
            mc.connectAttr(inMeshSourcePlug, inMeshAttr)
            if isLocked:
                mc.setAttr(inMeshAttr, lock=True)
#unpinAllMeshUVs()

class ExtractModel(publish.Extractor,
                   publish.OptionalPyblishPluginMixin):
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

    label = "Model (Maya Scene)"
    hosts = ["maya"]
    families = ["model"]
    scene_type = "ma"
    optional = True

    def process(self, instance):
        """Plugin entry point."""
        if not self.is_active(instance.data):
            return

        ext_mapping = (
            instance.context.data["project_settings"]["maya"]["ext_mapping"]
        )
        if ext_mapping:
            self.log.debug("Looking in settings for scene type ...")
            # use extension mapping for first family found
            for family in self.families:
                try:
                    self.scene_type = ext_mapping[family]
                    self.log.debug(
                        "Using {} as scene type".format(self.scene_type))
                    break
                except KeyError:
                    # no preset found
                    pass
        # Define extract output file path
        stagingdir = self.staging_dir(instance)
        filename = "{0}.{1}".format(instance.name, self.scene_type)
        path = os.path.join(stagingdir, filename)

        # Perform extraction
        self.log.debug("Performing extraction ...")

        # Get only the shape contents we need in such a way that we avoid
        # taking along intermediateObjects
        members = instance.data("setMembers")
        members = cmds.ls(members,
                          dag=True,
                          shapes=True,
                          type=("mesh", "nurbsCurve"),
                          noIntermediate=True,
                          long=True)

        unpinAllMeshUVs()
        with lib.no_display_layers(instance):
            with lib.displaySmoothness(members,
                                       divisionsU=0,
                                       divisionsV=0,
                                       pointsWire=4,
                                       pointsShaded=1,
                                       polygonObject=1):
                with lib.shader(members,
                                shadingEngine="initialShadingGroup"):
                    with lib.maintained_selection():
                        cmds.select(members, noExpand=True)
                        cmds.file(path,
                                  force=True,
                                  typ="mayaAscii" if self.scene_type == "ma" else "mayaBinary",  # noqa: E501
                                  exportSelected=True,
                                  preserveReferences=False,
                                  channels=False,
                                  constraints=False,
                                  expressions=False,
                                  constructionHistory=False)

                        # Store reference for integration

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': self.scene_type,
            'ext': self.scene_type,
            'files': filename,
            "stagingDir": stagingdir,
        }
        instance.data["representations"].append(representation)

        self.log.debug("Extracted instance '%s' to: %s" % (instance.name,
                                                           path))
