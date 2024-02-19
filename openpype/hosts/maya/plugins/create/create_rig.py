from maya import cmds

from openpype.hosts.maya.api import plugin


class CreateRig(plugin.MayaCreator):
    """Artist-friendly rig with controls to direct motion"""

    identifier = "io.openpype.creators.maya.rig"
    label = "Rig"
    family = "rig"
    icon = "wheelchair"

    def create(self, subset_name, instance_data, pre_create_data):

        instance = super(CreateRig, self).create(subset_name,
                                                 instance_data,
                                                 pre_create_data)

        instance_node = instance.get("instance_node")

        self.log.info("Creating Rig instance set up ...")
        controls = cmds.sets(name=subset_name + "_controls_SET", empty=True)
        joints = cmds.sets(name=subset_name + "_joints_SET", empty=True)
        pointcache = cmds.sets(name=subset_name + "_out_SET", empty=True)
        cmds.sets([controls, pointcache,joints], forceElement=instance_node)

        return instance


class RealtimeRig(CreateRig):
    """Builds on top of the standard rig to add support for having a
    realtime rig (mesh and single skeletal hierarchy) inside the same
    rig instance, which at publish time will get split into:
    - an fbx file containing the realtime geometry and realtime joints
    - an .ma file containing the animation rig and geometry
    - an .realtime.ma file  containing the animation rig and the realtime
    skeleton, which is driven by the animation rig

    Animators and layout artists should always bring the .ma (non-realtime)
    representation, as that contains the optimised animation rig.

    At animation publish time, if the .realtime.ma representation exists, the
    rig reference will be swapped to it before being cached out.
    """

    identifier = "io.openpype.creators.maya.realtimerig"
    label = "Rig - Realtime"
    family = "rig"
    icon = "wheelchair"

    def create(self, subset_name, instance_data, pre_create_data):
        instance = super(RealtimeRig, self).create(
            subset_name, instance_data, pre_create_data)

        instance_node = instance.get("instance_node")

        self.log.info("Creating realtime_out_SET...")
        realtime_geo = cmds.sets(name=subset_name + "_realtime_out_SET", empty=True)
        cmds.sets([realtime_geo], forceElement=instance_node)
