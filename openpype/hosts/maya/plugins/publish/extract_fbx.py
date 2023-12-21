# -*- coding: utf-8 -*-
import os

from maya import cmds  # noqa
import maya.mel as mel  # noqa
import pyblish.api

from openpype.pipeline import publish
from openpype.hosts.maya.api.lib import maintained_selection
from openpype.hosts.maya.api import fbx


class ExtractFBX(publish.Extractor):
    """Extract FBX from Maya.

    This extracts reproducible FBX exports ignoring any of the
    settings set on the local machine in the FBX export options window.

    """
    order = pyblish.api.ExtractorOrder
    label = "Extract FBX"
    families = ["fbx"]

    def process(self, instance):
        fbx_exporter = fbx.FBXExtractor(log=self.log)

        # Define output path
        staging_dir = self.staging_dir(instance)
        filename = "{0}.fbx".format(instance.name)
        path = os.path.join(staging_dir, filename)

        # The export requires forward slashes because we need
        # to format it into a string in a mel expression
        path = path.replace('\\', '/')

        self.log.info("Extracting FBX to: {0}".format(path))

        members = instance.data["setMembers"]
        self.log.info("Members: {0}".format(members))
        self.log.info("Instance: {0}".format(instance[:]))

        fbx_exporter.set_options_from_instance(instance)

        if instance.data.get("family") == "camera" and instance.data.get("shiftSequenceAmimation"):
            _shotStartFrame = instance.data.get("assetEntity").get("data").get("frameStart")
            _cameraPublishSet = instance.data.get("instance_node")
            _layoutPublishSets = cmds.listConnections(_cameraPublishSet+".cameraSet",s=1,d=0) or []
            _layoutShotNodes = cmds.listConnections(_layoutPublishSets[0]+".shotNode",s=1,d=0) or []
            _shotNodeSequenceStartFrame = cmds.shot(_layoutShotNodes[0],sequenceStartTime=True,query=True)

            _timeOffset = float(_shotStartFrame) - float(_shotNodeSequenceStartFrame)
            _timeOffsetInv = _timeOffset*-1
            self.log.info('Offsetting {s} by {f}'.format(s= instance.data.get("name") ,f=_timeOffset))
            offsetAllKeys(_timeOffset)
            self.log.info('Resetting {s} by {f}'.format(s= instance.data.get("name") ,f=_timeOffsetInv))
            offsetAllKeys(_timeOffsetInv)
            cmds.setAttr(_cameraPublishSet+".shiftSequenceAmimation",False)


        # Export
        with maintained_selection():
            fbx_exporter.export(members, path)
            cmds.select(members, r=1, noExpand=True)
            mel.eval('FBXExport -f "{}" -s'.format(path))

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


def offsetAllKeys( offset, includeReferenced=False):
    """
    startFrame : int : Where should the offset begin?
    offset : int : How large should the offset be?
    includeReferenced : bool : Default False : Should referenced animCurves be
        included?
    """
    animCurves = cmds.ls(type='animCurve')
    if not includeReferenced:
        animCurves = [ac for ac in animCurves if not cmds.referenceQuery(ac,inr=True) ]

    if animCurves:
        cmds.keyframe(animCurves, edit=True, includeUpperBound=False, animation="objects",
                    time=(), relative=True, option='over', timeChange=offset)
