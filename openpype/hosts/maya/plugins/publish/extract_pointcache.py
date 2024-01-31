import os
import importlib
from maya import cmds
from openpype.hosts.maya.api import fbx
importlib.reload(fbx)
from openpype.pipeline import publish
from openpype.hosts.maya.api.lib import (
    extract_alembic,
    suspended_refresh,
    maintained_selection,
    iter_visible_nodes_in_range
)


class ExtractAlembic(publish.Extractor):
    """Produce an alembic of just point positions and normals.

    Positions and normals, uvs, creases are preserved, but nothing more,
    for plain and predictable point caches.

    Plugin can run locally or remotely (on a farm - if instance is marked with
    "farm" it will be skipped in local processing, but processed on farm)
    """

    label = "Extract Pointcache (Alembic)"
    hosts = ["maya"]
    families = ["pointcache", "model", "vrayproxy.alembic"]
    targets = ["local", "remote"]

    def process(self, instance):


        if instance.data.get("farm"):
            self.log.debug("Should be processed on farm, skipping.")
            return
        if instance.data.get("exportFBX", False):
            self.log.debug("Skipping abc cache exporting fbx.")
            return
        nodes, roots = self.get_members_and_roots(instance)

        # Collect the start and end including handles
        start = float(instance.data.get("handleStart", 1))
        end = float(instance.data.get("handleEnd", 1))

        attrs = instance.data.get("attr", "").split(";")
        attrs = [value for value in attrs if value.strip()]
        attrs += instance.data.get("userDefinedAttributes", [])
        attrs += ["cbId"]

        attr_prefixes = instance.data.get("attrPrefix", "").split(";")
        attr_prefixes = [value for value in attr_prefixes if value.strip()]

        self.log.debug("Extracting pointcache..")
        dirname = self.staging_dir(instance)

        parent_dir = self.staging_dir(instance)
        filename = "{name}.abc".format(**instance.data)
        path = os.path.join(parent_dir, filename)

        options = {
            "step": instance.data.get("step", 1.0),
            "attr": attrs,
            "attrPrefix": attr_prefixes,
            "writeVisibility": True,
            "writeCreases": True,
            "writeColorSets": instance.data.get("writeColorSets", False),
            "writeFaceSets": instance.data.get("writeFaceSets", False),
            "uvWrite": True,
            "selection": True,
            "worldSpace": instance.data.get("worldSpace", True)
        }

        if not instance.data.get("includeParentHierarchy", True):
            # Set the root nodes if we don't want to include parents
            # The roots are to be considered the ones that are the actual
            # direct members of the set
            options["root"] = roots

        if int(cmds.about(version=True)) >= 2017:
            # Since Maya 2017 alembic supports multiple uv sets - write them.
            options["writeUVSets"] = True

        if instance.data.get("visibleOnly", False):
            # If we only want to include nodes that are visible in the frame
            # range then we need to do our own check. Alembic's `visibleOnly`
            # flag does not filter out those that are only hidden on some
            # frames as it counts "animated" or "connected" visibilities as
            # if it's always visible.
            nodes = list(iter_visible_nodes_in_range(nodes,
                                                     start=start,
                                                     end=end))

        suspend = not instance.data.get("refresh", False)
        with suspended_refresh(suspend=suspend):
            with maintained_selection():
                cmds.select(nodes, noExpand=True)
                extract_alembic(
                    file=path,
                    startFrame=start,
                    endFrame=end,
                    **options
                )

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            "name": "abc",
            "ext": "abc",
            "files": filename,
            "stagingDir": dirname
        }
        instance.data["representations"].append(representation)

        instance.context.data["cleanupFullPaths"].append(path)

        self.log.info("Extracted {} to {}".format(instance, dirname))

        # Extract proxy.
        if not instance.data.get("proxy"):
            self.log.info("No proxy nodes found. Skipping proxy extraction.")
            return

        path = path.replace(".abc", "_proxy.abc")
        if not instance.data.get("includeParentHierarchy", True):
            # Set the root nodes if we don't want to include parents
            # The roots are to be considered the ones that are the actual
            # direct members of the set
            options["root"] = instance.data["proxyRoots"]


        with suspended_refresh(suspend=suspend):
            with maintained_selection():
                cmds.select(instance.data["proxy"])
                extract_alembic(
                    file=path,
                    startFrame=start,
                    endFrame=end,
                    **options
                )

        representation = {
            "name": "proxy",
            "ext": "abc",
            "files": os.path.basename(path),
            "stagingDir": dirname,
            "outputName": "proxy"
        }
        instance.data["representations"].append(representation)

    def get_members_and_roots(self, instance):
        return instance[:], instance.data.get("setMembers")


class ExtractAnimation(ExtractAlembic):
    label = "Extract Animation"
    families = ["animation"]

    def get_members_and_roots(self, instance):

        # Collect the out set nodes
        out_sets = [node for node in instance if node.endswith("out_SET")]
        if len(out_sets) != 1:
            raise RuntimeError("Couldn't find exactly one out_SET: "
                               "{0}".format(out_sets))
        out_set = out_sets[0]
        roots = cmds.sets(out_set, query=True)

        # Include all descendants
        nodes = roots + cmds.listRelatives(roots,
                                           allDescendents=True,
                                           fullPath=True) or []

        return nodes, roots

    def process(self, instance):
        super().process(instance)

        # Switch the reference to the realtime representation for caching
        rig_reference_node = None
        for node in instance:
            if not cmds.referenceQuery(node, isNodeReferenced=True):
                continue
            rig_reference_node = cmds.referenceQuery(node, referenceNode=True)
            break

        referenced_rig_file = cmds.referenceQuery(rig_reference_node, filename=True)
        realtime_repr_file = referenced_rig_file.rsplit('.ma',1)[0] + '.mb'
        if os.path.exists(realtime_repr_file):
            cmds.file(realtime_repr_file, loadReference=rig_reference_node)

        out_sets = [node for node in instance if node.endswith("joints_SET")]
        geo_sets = [node for node in instance if node.endswith("out_SET")]

        if instance.data.get("exportFBX", False) and out_sets:
            parent_dir = self.staging_dir(instance)
            fbxfilename = "{name}.fbx".format(**instance.data)
            fbxpath = os.path.join(parent_dir, fbxfilename)

            ### WRITE FBX
            #instance.data['animationOnly']=True

            joints_to_export = cmds.sets(out_sets[0], query=True)
            joints_to_export = cmds.listRelatives(joints_to_export,ad=True,type="joint")
            fbx_exporter = fbx.FBXExtractor(log=self.log)
            instance.data["upAxis"]="z"
            fbx_exporter.set_options_from_instance(instance)

            fbx_exporter.export(joints_to_export, fbxpath.replace("\\","/"))

            # Get Namespace to store in publish representation
            _node = cmds.referenceQuery(out_sets[0], rfn=True)
            _namespace =str(cmds.referenceQuery(_node,namespace=True))
            self.log.info('Storing Representation namespace as "{}" '.format(_namespace))

            representation = {
                "name": "fbx",
                "ext": "fbx",
                "files": fbxfilename,
                "stagingDir": parent_dir,
                "outputName": "fbxanim",
                "namespace":_namespace
            }
            instance.data["representations"].append(representation)

        # Switch back to the animation reference
        if os.path.exists(realtime_repr_file):
            cmds.file(referenced_rig_file, loadReference=rig_reference_node)