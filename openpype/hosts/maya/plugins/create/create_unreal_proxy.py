from openpype.hosts.maya.api import plugin
from openpype.lib import (
    BoolDef,
    TextDef
)


class CreateUnrealProxy(plugin.MayaCreator):
    """StandIn Geometry for Unreal Asset in Maya"""

    identifier = "io.openpype.creators.maya.unreal_maya_placeholder"
    label = "Maya Placeholder"
    family = "placeholder"
    icon = "cube"
    default_variants = ["Main" ]


    def process(self, instance):
        return instance
