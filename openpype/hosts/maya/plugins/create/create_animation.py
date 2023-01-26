from openpype.hosts.maya.api import (
    lib,
    plugin
)
from openpype.lib import (
    BoolDef,
    TextDef
)


class CreateAnimation(plugin.MayaCreator):
    """Animation output for character rigs"""

    identifier = "io.openpype.creators.maya.animation"
    label = "Animation"
    family = "animation"
    icon = "male"

    write_color_sets = False
    write_face_sets = False

    # TODO: Would be great if we could visually hide this from the creator
    #       by default but do allow to generate it through code.

    def get_instance_attr_defs(self):

        defs = lib.collect_animation_defs()

        defs.extend([
            BoolDef("writeColorSets",
                    label="Write vertex colors",
                    tooltip="Write vertex colors with the geometry",
                    default=self.write_color_sets),
            BoolDef("writeFaceSets",
                    label="Write face sets",
                    tooltip="Write face sets with the geometry",
                    default=self.write_face_sets),
            BoolDef("writeNormals",
                    label="Write normals",
                    tooltip="Write normals with the deforming geometry",
                    default=True),
            BoolDef("renderableOnly",
                    label="Renderable Only",
                    tooltip="Only export renderable visible shapes",
                    default=False),
            BoolDef("visibleOnly",
                    label="Visible Only",
                    tooltip="Only export dag objects visible during "
                            "frame range",
                    default=False),
            BoolDef("includeParentHierarchy",
                    label="Include Parent Hierarchy",
                    tooltip="Whether to include parent hierarchy of nodes in "
                            "the publish instance",
                    default=False),
            BoolDef("worldSpace",
                    label="World-Space Export",
                    default=True),
            TextDef("attr",
                    label="Custom Attributes",
                    default="",
                    placeholder="attr1, attr2"),
            TextDef("attrPrefix",
                    label="Custom Attributes Prefix",
                    placeholder="prefix1, prefix2")
        ])

        # TODO: Implement these on a Deadline plug-in instead?
        """
        # Default to not send to farm.
        self.data["farm"] = False
        self.data["priority"] = 50
        """

        return defs
