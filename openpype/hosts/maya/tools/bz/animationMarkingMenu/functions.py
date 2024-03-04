from maya import cmds as mc
from maya.api import OpenMaya as om
import json
import re
import math

SELECTION_ISOLATED = False
IKFK_STRETCH_OPTIONVAR_NAME = "bzAnimationMarkingMenuIKFKStretch"
IKFK_TIMELINE_OPTIONVAR_NAME = "bzAnimationMarkingMenuIKFKAcrossTimeline"

def _radiansToDegrees(rad):
    return rad * 180 / math.pi

def _getSelectedCharacterNodes():
    '''Returns the character nodes associated with currently selected controls.'''
    charNodes = []
    for each in mc.ls(sl=1, fl=1):
        if mc.objExists(each + ".animControl"):
            if mc.objExists(each + ".assetInfo"):
                charNode = each
            else:
                charNode = mc.listConnections(each + ".animControl")[0]
            if not charNode in charNodes:
                charNodes.append(charNode)
    return charNodes

def _getAllCharacterNodes():
    '''Returns all character nodes in the scene.'''
    charNodes = mc.ls("C_characterNode_CTL", recursive=True)
    return [i for i in charNodes if mc.objExists(i + ".assetInfo")]

def _getGeometriesForSmoothing(charNode):
    '''Returns a list of all geometries that need to be smoothed. 
    This will be all the connections from the chrNode.reference attribute that are not also connected from the chrNode.ignoreSmootingGeometries'''
    allGeos = set(mc.listConnections(charNode + ".reference"))
    ignoreSmoothingGeos = set((mc.listConnections(charNode + ".ignoreSmootingGeometries") \
                if mc.objExists(charNode + ".ignoreSmootingGeometries") else []))   
    return list(allGeos - ignoreSmoothingGeos)

def _getControlsFromCharacterNode(charNode):
    '''Returns all controls registered to a character node.'''
    controls = (mc.listConnections(charNode + ".assetInfo.controls.bodyControls") or []) + \
        (mc.listConnections(charNode + ".assetInfo.controls.faceControls") or [])
    controls.remove(charNode)
    return controls

def camelCaseToUnderscores(name):
    splitName = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower().split("_")
    niceName = splitName[0].capitalize() + "_" + splitName[1] + "".join(
        [each.capitalize() for each in splitName[2:-1]]) + "_" + splitName[-1].upper()
    return niceName

def _getPoleVectorPosition(kMatch):
    '''Returns the pole vector position from the current FK chain pose.'''
    # Get side multiplier
    sideMultiplier = 1.
    if kMatch.fk00Control.split(":")[-1].split("_")[0] == "R":
        sideMultiplier = -1.

    # Get length
    upperLength = mc.getAttr(kMatch.fk01Joint + ".tx")

    # Sample the preferred angle from the ik elbow/knee - 
    # The IK limb node is written in such a way where the limb is never completely straight,
    # so we can reliably sample the joint rotations to be used as a preferred angle.
    preferredAngle = [sorted([-.001, i, .001])[1] 
        for i in mc.getAttr(kMatch.ik01Joint + ".r")[0]]
    rotateOrder = mc.getAttr(kMatch.fk01Joint + ".ro")
    preferredAngle.append(rotateOrder)

    # Get fk chain world matrices
    selectionList = om.MSelectionList()
    selectionList.add(kMatch.fk00Joint)
    selectionList.add(kMatch.fk01Joint)
    selectionList.add(kMatch.fk02Joint)
    dagPath00 = selectionList.getDagPath(0)
    dagPath01 = selectionList.getDagPath(1)
    dagPath02 = selectionList.getDagPath(2)
    worldMatrix00 = dagPath00.inclusiveMatrix()
    worldMatrix01 = dagPath01.inclusiveMatrix()
    worldMatrix02 = dagPath02.inclusiveMatrix()

    # Get end joint local matrix relative to mid
    localMatrix02 = worldMatrix02 * worldMatrix01.inverse()

    # Construct transformation matrices and rotate mid matrix by offset
    transformationMatrix00 = om.MTransformationMatrix(worldMatrix00)
    transformationMatrix01 = om.MTransformationMatrix(worldMatrix01)
    transformationMatrix01.rotateByComponents(preferredAngle, 
        om.MSpace.kObject, asQuaternion=False)

    # Transpose end local matrix by rotated mid matrix
    rotatedWorldMatrix02 = localMatrix02 * transformationMatrix01.asMatrix()
    transformationMatrix02 = om.MTransformationMatrix(rotatedWorldMatrix02)

    # Get joint positions
    startPosition = transformationMatrix00.translation(om.MSpace.kWorld)
    midPosition = transformationMatrix01.translation(om.MSpace.kWorld)
    endPosition = transformationMatrix02.translation(om.MSpace.kWorld)

    # Calculate direction
    endDifference = endPosition - startPosition
    midDifference = midPosition - startPosition
    dotProduct = midDifference * endDifference
    projection = dotProduct / endDifference.length()
    endNormal = endDifference.normal()
    projectionVector = endNormal * projection
    direction = (midDifference - projectionVector).normal()

    # Calculate normals
    normal = (endDifference ^ midDifference).normal()
    binormal = (normal ^ direction).normal()

    # Construct rotation matrix
    matrixM = om.MMatrix([direction.x, direction.y, direction.z, 0,
        normal.x, normal.y, normal.z, 0,
        binormal.x, binormal.y, binormal.z, 0,
        0, 0, 0, 1])

    # Construct final matrix
    transformationMatrix = om.MTransformationMatrix(matrixM)
    transformationMatrix.setTranslation(midPosition, om.MSpace.kWorld)
    transformationMatrix.translateBy(
        om.MVector.kXaxisVector * upperLength * 1.375 * sideMultiplier, om.MSpace.kObject)

    # Return world position
    return transformationMatrix.translation(om.MSpace.kWorld)

def getAvailableSpaces(control):
    '''Returns a control's available spaces, if any exist.'''
    if not mc.objExists(control + ".space"):
        return
    return mc.addAttr(control + ".space", q=1, en=1).split(":")

def spaceMatch(index, *_):
    '''Changes a control's space to a new index and matches its world space position and 
    rotation to the new space.'''
    # Get dag path
    control = mc.ls(sl=1, fl=1)[0]
    mSelectionList = om.MSelectionList()
    mSelectionList.add(control)
    dagPath = mSelectionList.getDagPath(0)

    # Get previous world matrix
    worldMatrix = dagPath.inclusiveMatrix()

    # Switch space
    mc.setAttr(control + ".space", index)

    # Get new local matrix
    parentInverseMatrix = dagPath.exclusiveMatrixInverse()
    localMatrix = worldMatrix * parentInverseMatrix
    transformationMatrix = om.MTransformationMatrix(localMatrix)
    translation = transformationMatrix.translation(om.MSpace.kWorld)
    rotation = transformationMatrix.rotation(asQuaternion=False)
    smallestEulerSolution = rotation.closestSolution(om.MEulerRotation.kIdentity)
    reorderedEuler = smallestEulerSolution.reorder(mc.getAttr(control + ".ro"))

    # Set using cmds to leverage undo support
    mc.setAttr(control + ".t", *translation)

    # Set rotation only if it is settable. 
    # The only case where rotation is locked on a space switchable control
    # so far are pole vectors.
    if mc.getAttr(control + ".r", settable=True):
        
        # NOTE Setting rotation using xform does not use smallest euler solution
        mc.setAttr(control + ".r", *[_radiansToDegrees(i) for i in reorderedEuler])

def toggleOrientAndMatch(*_):
    '''Toggles a control's orient state and matches its world space rotation.'''
    # Get dag path
    control = mc.ls(sl=1, fl=1)[0]
    mSelectionList = om.MSelectionList()
    mSelectionList.add(control)
    dagPath = mSelectionList.getDagPath(0)

    # Get world space rotation
    worldMatrix = dagPath.inclusiveMatrix()

    # Toggle orient value
    roundedOrientValue = round(mc.getAttr(control + ".orient"))
    mc.setAttr(control + ".orient", 1. - roundedOrientValue)

    # Get new local matrix
    parentInverseMatrix = dagPath.exclusiveMatrixInverse()
    localMatrix = worldMatrix * parentInverseMatrix
    transformationMatrix = om.MTransformationMatrix(localMatrix)
    rotation = transformationMatrix.rotation(asQuaternion=False)
    smallestEulerSolution = rotation.closestSolution(om.MEulerRotation.kIdentity)
    reorderedEuler = smallestEulerSolution.reorder(mc.getAttr(control + ".ro"))

    # Set using cmds to leverage undo support
    # NOTE Setting rotation using xform does not use smallest euler solution
    mc.setAttr(control + ".r", *[_radiansToDegrees(i) for i in reorderedEuler])

class bindPose():
    @staticmethod
    def revertAssetsToBindPose(*_):
        for charNode in _getSelectedCharacterNodes():
            bindPose._revertAssetToBindPose(charNode)

    @staticmethod
    def revertSelectedToBindPose(*_):
        for each in mc.ls(sl=1, fl=1):
            if mc.objExists(each + ".bindPose"):
                bindPose._revertToBindPose(each)

    @staticmethod
    def _revertToBindPose(control):
        bindPose = json.loads(mc.getAttr(control + ".bindPose"))

        for attr, value in bindPose.items():
            mc.setAttr(control + "." + attr, value)

    @staticmethod
    def _revertAssetToBindPose(charNode, *_):
        controls = _getControlsFromCharacterNode(charNode)

        for each in controls:
            bindPose._revertToBindPose(each)

            if mc.objExists(each + ".gimbal"):
                bindPose._revertToBindPose(
                    mc.listConnections(each + ".gimbal")[0])

class ikFkMatch():
    class kMatchStruct():
        def __init__(self, ikFkSwitchControl):
            kMatchInfoCompound = ikFkSwitchControl + ".kMatchInfo"
            self.fk00Joint = mc.listConnections(kMatchInfoCompound + ".fk00Joint")[0]
            self.fk01Joint = mc.listConnections(kMatchInfoCompound + ".fk01Joint")[0]
            self.fk02Joint = mc.listConnections(kMatchInfoCompound + ".fk02Joint")[0]
            self.fk03Joint = (None if not mc.objExists(kMatchInfoCompound + ".fk03Joint") 
                else mc.listConnections(kMatchInfoCompound + ".fk03Joint")[0])

            self.fk00Control = mc.listConnections(kMatchInfoCompound + ".fk00Control")[0]
            self.fk01Control = mc.listConnections(kMatchInfoCompound + ".fk01Control")[0]
            self.fk02Control = mc.listConnections(kMatchInfoCompound + ".fk02Control")[0]
            self.fk03Control = (None if not mc.objExists(kMatchInfoCompound + ".fk03Control")
                else mc.listConnections(kMatchInfoCompound + ".fk03Control")[0])

            self.ikControl = mc.listConnections(kMatchInfoCompound + ".ikControl")[0]
            self.ikPvControl = mc.listConnections(kMatchInfoCompound + ".ikPvControl")[0]
            self.lowerIkControl = (None if not mc.objExists(kMatchInfoCompound + ".lowerIkControl")
                else mc.listConnections(kMatchInfoCompound + ".lowerIkControl")[0])

            self.ik00Joint = mc.listConnections(kMatchInfoCompound + ".ik00Joint")[0]
            self.ik01Joint = mc.listConnections(kMatchInfoCompound + ".ik01Joint")[0]
            self.ik02Joint = mc.listConnections(kMatchInfoCompound + ".ik02Joint")[0]
            self.ik03Joint = (None if not mc.objExists(kMatchInfoCompound + ".ik03Joint") 
                else mc.listConnections(kMatchInfoCompound + ".ik03Joint")[0])
        def getFkControls(self):
            fkCtls = [self.fk00Control, self.fk01Control, self.fk02Control]
            if self.fk03Control is not None:
                return fkCtls+[self.fk03Control]
            return fkCtls
        def getIKControls(self):
            ikCtls = [self.ikControl, self.ikPvControl]
            if self.lowerIkControl is not None:
                return ikCtls+[self.lowerIkControl]
            return ikCtls
    @staticmethod
    def doMatch(*_):
        # Get switch controls and determine new state from last selection
        switchControls = ikFkMatch._getSelectedIkFkSwitches()
        if mc.getAttr(switchControls[-1] + ".fkIkBlend") < .5:
            ikFkMatch._fkToIk()
        else:
            ikFkMatch._ikToFk()
        
    @staticmethod
    def doMatchAcrossTimeline(*_):
        # Let's get selected time range
        import maya.mel
        aPlayBackSlider = maya.mel.eval('$tmpVar=$gPlayBackSlider')
        selectedTimeRange = mc.timeControl(aPlayBackSlider, q=1, rng=1)[1:-1].split(":")
        selectedTimeRange = [int(selectedTimeRange[0]), int(selectedTimeRange[1])]
        # If the selected time range is just one frame then we will cal the doMatch() function
        if selectedTimeRange[1] - selectedTimeRange[0] == 1:
            ikFkMatch.doMatch()
            return
        # In this case we continue with the matching across the timeline
        ikState = 0
        switchControls = ikFkMatch._getSelectedIkFkSwitches()
        if mc.getAttr(switchControls[-1] + ".fkIkBlend") > .5:
            ikState = 1
        ikFkMatch._matchAcrossTimeline(
                ikState=ikState, timeRangeMin=selectedTimeRange[0], timeRangeMax=selectedTimeRange[1])

    @staticmethod
    def _matchAcrossTimeline(ikState, timeRangeMin, timeRangeMax):
        '''
        ikState         : int : 0 meaning current state is FK and we will switch to IK 
                                1 meaning current state is IK and we will switch to FK
        timeRangeMin    : int : start of frame range 
        timeRangeMax    : int : end of frame rance 
        
        '''
        # Get switch controls and determine new state from last selection
        switchControls = ikFkMatch._getSelectedIkFkSwitches()
        # Dictinary that will hold for each time stamp and 
        # the controls that are keyed at this time stamps
        # We are storing this information in order to avoid running 
        # through the time slide for each selected limb
         
        # {timeSramp : [targetControls0, targetControls1]}
        keyedControlsAtTimeStamp = {} 

        for switchControl in switchControls:  
            # Find all the corresponding controls for the current state
            kMatch = ikFkMatch.kMatchStruct(switchControl)
            sourceControls = kMatch.getFkControls() if ikState==0 else kMatch.getIKControls()
            targetControls = kMatch.getFkControls() if ikState==1 else kMatch.getIKControls()
            # Find all the time stamps at which we have key frames 
            keyFrames = set()
            for ctl in sourceControls:
                # keyFrames = selectedTimeRange.intersection(set(mc.keyframe(ctl, q=1, tc=1) or []))
                keyFrames = keyFrames.union(set(mc.keyframe(ctl, q=1, tc=1) or []))
            for key in keyFrames:
                if key not in keyedControlsAtTimeStamp.keys():
                    keyedControlsAtTimeStamp[key] = []
                keyedControlsAtTimeStamp[key] += targetControls+[switchControl]
        
        selectedTimeRange = set(range(timeRangeMin, timeRangeMax))
        selectedTimeRange = selectedTimeRange.intersection(set(keyedControlsAtTimeStamp.keys()))
        # Let's get user tangent settings
        inTangent = mc.keyTangent(q=True, g=True, inTangentType=True)[0]
        outTangent = mc.keyTangent(q=True, g=True, outTangentType=True)[0]
        for time in sorted(list(selectedTimeRange)):
            mc.currentTime(time)
            ikFkMatch._ikToFk() if ikState else ikFkMatch._fkToIk()
            mc.setKeyframe(keyedControlsAtTimeStamp[time], time=time)
            mc.keyTangent(keyedControlsAtTimeStamp[time], 
                            time=(time, time),
                            itt = inTangent,
                            ott = outTangent)

    @staticmethod
    def _fkToIk(*_):
        '''Switches selected switchable limbs from FK to IK and matches world space position.'''

        # Iterate over switchable controls
        for ikFkSwitchControl in ikFkMatch._getSelectedIkFkSwitches():
            kMatch = ikFkMatch.kMatchStruct(ikFkSwitchControl)

            # Get dag paths
            mSelectionList = om.MSelectionList()
            mSelectionList.add(kMatch.fk03Joint or kMatch.fk02Joint)
            mSelectionList.add(kMatch.ik03Joint or kMatch.ik02Joint)
            mSelectionList.add(kMatch.ikControl)
            fkJointDagPath = mSelectionList.getDagPath(0)
            ikJointDagPath = mSelectionList.getDagPath(1)
            ikControlDagPath = mSelectionList.getDagPath(2)

            # Get matrices
            fkJointWorldMatrix = fkJointDagPath.inclusiveMatrix()
            ikJointInverseWorldMatrix = ikJointDagPath.inclusiveMatrixInverse()
            ikControlWorldMatrix = ikControlDagPath.inclusiveMatrix()
            ikCtlOffset = ikControlWorldMatrix * ikJointInverseWorldMatrix
            ikLocalMatrix = ikCtlOffset * fkJointWorldMatrix

            # Get new local matrix
            ikParentInverseMatrix = ikControlDagPath.exclusiveMatrixInverse()
            ikLocalMatrix = ikLocalMatrix * ikParentInverseMatrix
            transformationMatrix = om.MTransformationMatrix(ikLocalMatrix)
            translation = transformationMatrix.translation(om.MSpace.kWorld)
            rotation = transformationMatrix.rotation(asQuaternion=False)
            smallestEulerSolution = rotation.closestSolution(om.MEulerRotation.kIdentity)
            reorderedEuler = smallestEulerSolution.reorder(mc.getAttr(kMatch.ikControl + ".ro"))

            # Set using cmds to leverage undo support
            # NOTE Setting rotation using xform does not use smallest euler solution
            mc.setAttr(kMatch.ikControl + ".t", *translation)
            mc.setAttr(kMatch.ikControl + ".r", *[_radiansToDegrees(i) for i in reorderedEuler])

            # Position pole vector
            # NOTE This can be set using xform as the control has no rotation
            poleVectorPosition = _getPoleVectorPosition(kMatch)
            mc.xform(kMatch.ikPvControl, t=poleVectorPosition, ws=1)

            # If chain is a quadruped leg, position the lowerIk control
            if kMatch.ik03Joint:
                
                # Get quad ankle matrix
                mSelectionList.add(kMatch.fk02Joint)
                mSelectionList.add(kMatch.lowerIkControl)
                fkJoint02DagPath = mSelectionList.getDagPath(3)
                ikLowerControlDagPath = mSelectionList.getDagPath(4)
                fkJoint02WorldMatrix = fkJoint02DagPath.inclusiveMatrix()

                # Get new local matrix
                ikLowerControlParentInverseMatrix = ikLowerControlDagPath.exclusiveMatrixInverse()
                ikLocalMatrix = fkJoint02WorldMatrix * ikLowerControlParentInverseMatrix
                transformationMatrix = om.MTransformationMatrix(ikLocalMatrix)
                rotation = transformationMatrix.rotation(asQuaternion=False)
                smallestEulerSolution = rotation.closestSolution(om.MEulerRotation.kIdentity)
                reorderedEuler = smallestEulerSolution.reorder(mc.getAttr(kMatch.lowerIkControl + ".ro"))

                # Set using cmds to leverage undo support
                # NOTE Setting rotation using xform does not use smallest euler solution
                mc.setAttr(kMatch.lowerIkControl + ".r", *[_radiansToDegrees(i) for i in reorderedEuler])

            # Handle stretch matching
            if mc.optionVar(q=IKFK_STRETCH_OPTIONVAR_NAME) == 1:

                # Get lengths
                length01 = mc.getAttr(kMatch.fk01Joint + ".tx")
                length02 = mc.getAttr(kMatch.fk02Joint + ".tx")
                totalLength = length01 + length02

                # Get orig lengths
                ikLimbNode = mc.listConnections(kMatch.ik00Joint + ".r", s=1, d=0)[0]
                origLength01 = mc.getAttr(ikLimbNode + ".upperLength")
                origLength02 = mc.getAttr(ikLimbNode + ".lowerLength")
                origTotalLength = origLength01 + origLength02

                # Calculate stretch weights
                totalStretch = (totalLength - origTotalLength) / origTotalLength
                mc.setAttr(kMatch.ikControl + ".lengthScale", totalStretch)

                # Calculate bias multiplier and reorder bias equation to solve for bias weight
                # The original equation is;
                # length01 = origLength01 * (totalStretch + 1) + biasMultiplier * biasWeight
                biasMultiplier = totalLength * .2
                biasWeight = (length01 - origLength01 * (totalStretch + 1)) / biasMultiplier

                # Finalise length bias
                mc.setAttr(kMatch.ikControl + ".lengthBias", biasWeight)

                # NOTE There is an edge case for quadruped legs -
                # Currently there is no stretch control for the haunch control,
                # so if the user matches from FK to IK with stretch values, the
                # tool is unable to match correctly and results will be incorrect.
                
                # This can be fixed in the quadruped module if necessary, but an 
                # exception will have to be worked into this stretch matching.

            # Otherwise reset IK stretch values
            else:
                mc.setAttr(kMatch.ikControl + ".lengthScale", 0)
                mc.setAttr(kMatch.ikControl + ".lengthBias", 0)

            # Disable pole vector lock
            if mc.objExists(kMatch.ikPvControl + ".elbowLock"):
                mc.setAttr(kMatch.ikPvControl + ".elbowLock", 0)
            else:
                mc.setAttr(kMatch.ikPvControl + ".kneeLock", 0)

            # Finalise blend attr
            mc.setAttr(ikFkSwitchControl + ".fkIkBlend", 1)

    @staticmethod
    def _ikToFk(*_):
        '''Switches selected switchable limbs from IK to FK and matches world space position.'''

        # Iterate over switchable controls
        for ikFkSwitchControl in ikFkMatch._getSelectedIkFkSwitches():
            
            # Build match struct and iterate matchables
            kMatch = ikFkMatch.kMatchStruct(ikFkSwitchControl)
            for ik, fk in zip(
                [kMatch.ik00Joint, kMatch.ik01Joint, kMatch.ik02Joint, kMatch.ik03Joint], 
                [kMatch.fk00Control, kMatch.fk01Control, kMatch.fk02Control, kMatch.fk03Control]
                ):

                # Skip unmatchables
                if not ik or not fk:
                    continue

                # Get ik world matrix
                mSelectionList = om.MSelectionList()
                mSelectionList.add(ik)
                mSelectionList.add(fk)
                ikDagPath = mSelectionList.getDagPath(0)
                fkDagPath = mSelectionList.getDagPath(1)
                ikWorldMatrix = ikDagPath.inclusiveMatrix()
                fkParentInverseMatrix = fkDagPath.exclusiveMatrixInverse()

                # Handle end rotation offset
                endIkJoint = (kMatch.ik03Joint or kMatch.ik02Joint)
                endFkJoint = (kMatch.fk03Joint or kMatch.fk02Joint)
                if ik == endIkJoint:

                    # Get fk matrices
                    mSelectionList.add(endFkJoint)
                    fkEndJointDagPath = mSelectionList.getDagPath(2)

                    fkWorldMatrix = fkDagPath.inclusiveMatrix()
                    ikEndJointWorldInverseMatrix = fkEndJointDagPath.inclusiveMatrixInverse()

                    # Construct and apply matrix offset
                    fkOffsetMatrix = fkWorldMatrix * ikEndJointWorldInverseMatrix
                    ikWorldMatrix = fkOffsetMatrix * ikWorldMatrix

                # Get world rotation
                localMatrix = ikWorldMatrix * fkParentInverseMatrix
                transformationMatrix = om.MTransformationMatrix(localMatrix)
                rotation = transformationMatrix.rotation(asQuaternion=False)
                smallestEulerSolution = rotation.setToClosestSolution(om.MEulerRotation(1, 1, 1))
                reorderedEuler = smallestEulerSolution.reorder(mc.getAttr(fk + ".ro"))

                # Set using cmds to leverage undo support.
                # NOTE Setting rotation using xform does not use smallest euler solution, 
                #      which is why we use setAttr.

                # Support locked elbow/knee channels:
                # This is a long-requested change to the limb modules from animation - 
                # to lock X/Z rotation channels so that animators can't go off model.
                # If both channels are locked, set Y channel ONLY.
                if mc.getAttr(fk + ".rx", l=True) and mc.getAttr(fk + ".rz", l=True):
                    mc.setAttr(fk + ".ry", _radiansToDegrees(reorderedEuler[1]))

                # Otherwise we set all channels.
                # We do this rather than comparing the current FK control to kMatch.kf01Control
                # so that we can still support unlocked X/Z channels for high end projects.
                else:
                    mc.setAttr(fk + ".r", *[_radiansToDegrees(i) for i in reorderedEuler])

            # Handle stretch matching
            if mc.optionVar(q=IKFK_STRETCH_OPTIONVAR_NAME) == 1:

                # Get current lengths
                length01 = mc.getAttr(kMatch.ik01Joint + ".tx")
                length02 = mc.getAttr(kMatch.ik02Joint + ".tx")

                # Get orig lengths
                ikLimbNode = mc.listConnections(kMatch.ik00Joint + ".r", s=1, d=0)[0]
                origLength01 = mc.getAttr(ikLimbNode + ".upperLength")
                origLength02 = mc.getAttr(ikLimbNode + ".lowerLength")

                # Calculate stretch weights
                stretch01 = (length01 - origLength01) / origLength01
                stretch02 = (length02 - origLength02) / origLength02

                # Apply stretch weights
                mc.setAttr(kMatch.fk00Control + ".stretch", stretch01)
                mc.setAttr(kMatch.fk01Control + ".stretch", stretch02)

                # ADD QUAD STRETCH
                if kMatch.fk03Control:
                    mc.setAttr(kMatch.fk02Control + ".stretch", stretch01)

            # Otherwise reset FK stretch values
            else:
                mc.setAttr(kMatch.fk00Control + ".stretch", 0)
                mc.setAttr(kMatch.fk01Control + ".stretch", 0)

            # Finalise blend attr
            mc.setAttr(ikFkSwitchControl + ".fkIkBlend", 0)

    @staticmethod
    def _getSelectedIkFkSwitches():
        ikFkSwitches = []
        for each in mc.ls(sl=1, fl=1):
            if mc.objExists(each + ".fk02Control"):
                ikFkSwitch = each
            elif mc.objExists(each + ".kMatchable"):
                ikFkSwitch = mc.listConnections(each + ".kMatchable")[0]
            else:
                continue
            if not ikFkSwitch in ikFkSwitches:
                ikFkSwitches.append(ikFkSwitch)
        return ikFkSwitches

class controlSets():
    @staticmethod
    def _getSelectedSets():
        selection = []
        sets = []
        for each in mc.ls(sl=1, fl=1):
            if mc.objExists(each + ".controlSet"):
                controlSet = mc.listConnections(each + ".controlSet", p=1)

                if controlSet:
                    if mc.nodeType(controlSet[0].split(".")[0]) == "network":
                        # New control set structure. Added to accomodate children sets.
                        controlHierarchy = mc.listConnections(each + ".controlSet")

                        if controlHierarchy:
                            controlHierarchy = controlHierarchy[0]

                            selection += mc.listConnections(controlHierarchy + ".controls")

                            setPlug = mc.listConnections(controlHierarchy + ".set", p=1)[0]
                            if setPlug not in sets:
                                sets.append(setPlug)

                    elif controlSet and controlSet[0].split(".")[1] not in sets:
                        # Old control Set structure
                        selection += mc.listConnections(controlSet[0])
                        sets.append(controlSet[0])

        return sets, selection

    @staticmethod
    def _getChildrenSets(parentSets):
        selection = []
        sets = []
        for _set in parentSets:
            setConnections = mc.listConnections(_set)
            if setConnections:
                if mc.nodeType(setConnections[0]) != "network":
                    return []
                controlHierarchy = mc.listConnections(_set)[0]
                
                childrenControlHierarchies = mc.listConnections(controlHierarchy + ".children")
                if childrenControlHierarchies:
                    selection += [ctl for child in (childrenControlHierarchies or []) for ctl in mc.listConnections(child + ".controls")]
                    # Recursive
                    childrenSets = [mc.listConnections(childHierarchy + ".set", p=1)[0] for childHierarchy in childrenControlHierarchies]
                    selection += controlSets._getChildrenSets(childrenSets)
                # else:
                #     mc.warning("The set - %s - does not have any children." % _camelCaseToUnderscores(_set.split(".")[1]))
                    
        return selection

    @staticmethod
    def selectSet(*_):
        selection = controlSets._getSelectedSets()[1]
        mc.select(selection)

    @staticmethod
    def selectSetAndChildren(*_):
        sets, selection = controlSets._getSelectedSets()
        selection += controlSets._getChildrenSets(sets)
        mc.select(selection)

    @staticmethod
    def setAvailable(*_):
        return bool(controlSets._getSelectedSets()[0])

class generic():
    @staticmethod
    def toggleSelectedVisibility(*_):
        charNodes = _getSelectedCharacterNodes()
        visibility = mc.getAttr(mc.listRelatives(
            charNodes[-1], s=1)[0] + ".lodVisibility")

        generic._toggleVisibility(charNodes, visibility)

    @staticmethod
    def toggleAllVisibility(*_):
        charNodes = _getAllCharacterNodes()

        if charNodes:
            visibility = round(sum([mc.getAttr(mc.listRelatives(charNode, s=1)[
                               0] + ".lodVisibility") for charNode in charNodes]) / len(charNodes))
            generic._toggleVisibility(charNodes, visibility)

    @staticmethod
    def _toggleVisibility(charNodes, visibility):
        for charNode in charNodes:
            for control in _getControlsFromCharacterNode(charNode) + [charNode]:
                generic._setVisibility(control, 1 - visibility)

    @staticmethod
    def _setVisibility(ctl, visibility):
        for shape in mc.listRelatives(ctl, s=1):
            mc.setAttr(shape + ".lodVisibility", visibility)

    @staticmethod
    def isolateSelected(*_):
        global SELECTION_ISOLATED
        generic._toggleVisibility(_getAllCharacterNodes(), 1)
        for ctl in mc.ls(sl=1,fl=1):
            if mc.objExists(ctl + ".animControl"):
                generic._setVisibility(ctl, 1)
        SELECTION_ISOLATED = True

    @staticmethod
    def clearIsolated(*_):
        global SELECTION_ISOLATED
        generic._toggleVisibility(_getAllCharacterNodes(), 0)
        SELECTION_ISOLATED = False

    @staticmethod
    def _getOppositeSelection():
        selection = []
        for ctl in mc.ls(sl=1,fl=1):
            if mc.objExists(ctl + ".animControl"):
                if ":" in ctl:
                    namespace, name = ctl.split(":")
                else:
                    namespace = None
                    name = ctl
                side = name[0]
                if side == "L":
                    opposite = name.replace("L_","R_")
                elif side == "R":
                    opposite = name.replace("R_","L_")
                else:
                    selection.append(ctl)
                    continue
                oppositeCtl = ":".join([namespace, opposite]) if namespace else opposite
                if mc.objExists(oppositeCtl):
                    selection.append(oppositeCtl)
        return selection

    @staticmethod
    def flipSelection(*_):
        mc.select(generic._getOppositeSelection())

    @staticmethod
    def mirrorSelection(*_):
        mc.select(generic._getOppositeSelection(), add=1)

    @staticmethod
    def toggleSelectedReference(*_):
        charNodes = _getSelectedCharacterNodes()
        reference = mc.getAttr(charNodes[-1] + ".reference")

        generic._toggleReference(charNodes, reference)

    @staticmethod
    def toggleAllReference(*_):
        charNodes = _getAllCharacterNodes()

        if charNodes:
            reference = round(sum([mc.getAttr(charNode + ".reference")
                                   for charNode in charNodes]) / len(charNodes))

            generic._toggleReference(charNodes, reference)

    @staticmethod
    def _toggleReference(charNodes, reference):
        for charNode in charNodes:
            mc.setAttr(charNode + ".reference", 1 - reference)

    @staticmethod
    def referenceAll(*_):
        for charNode in _getAllCharacterNodes():
            mc.setAttr(charNode + ".reference", 1)

    @staticmethod
    def toggleSelectedSmoothing(*_):
        charNodes = _getSelectedCharacterNodes()

        lastCharNodeGeometries = _getGeometriesForSmoothing(charNodes[-1])

        def isMesh(geo):
            if mc.nodeType(mc.listRelatives(geo, c=1, s=1)[0]) == "mesh":
                return True
            return False

        smooth = round(sum([(mc.displaySmoothness(geometry, polygonObject=1, q=1)[
                       0] - 1) / 2.0 for geometry in lastCharNodeGeometries if isMesh(geometry)]) / len(lastCharNodeGeometries))
        generic._toggleSmoothing(charNodes, smooth)

    @staticmethod
    def toggleAllSmoothing(*_):
        charNodes = _getAllCharacterNodes()

        if charNodes:
            allSmooth = 0
            for charNode in charNodes:
                charNodeGeometries = _getGeometriesForSmoothing(charNode)
                allSmooth += round(sum([(mc.displaySmoothness(geometry, polygonObject=1, q=1)[
                                   0] - 1) / 2.0 for geometry in charNodeGeometries]) / len(charNodeGeometries))
            allSmooth = round(allSmooth / len(charNodes))

            generic._toggleSmoothing(charNodes, allSmooth)

    @staticmethod
    def _toggleSmoothing(charNodes, smooth):
        for charNode in charNodes:
            for geometry in _getGeometriesForSmoothing(charNode):
                mc.displaySmoothness(
                    geometry, polygonObject=(1-smooth) * 2 + 1)

    @staticmethod
    def unsmoothAll(*_):
        for charNode in _getAllCharacterNodes():
            for geometry in _getGeometriesForSmoothing(charNode):
                mc.displaySmoothness(geometry, polygonObject=1)

    @staticmethod
    def selectControlsFromCharacterNode(*_):
        selection = [control for charNode in _getSelectedCharacterNodes(
        ) for control in _getControlsFromCharacterNode(charNode)]
        mc.select(selection)

    @staticmethod
    def keyControlsOnCharacterNode(*_):
        controls = [control for charNode in _getSelectedCharacterNodes()
                    for control in _getControlsFromCharacterNode(charNode)]
        for control in controls:
            for attr in mc.listAttr(control, k=1, u=1, v=1) or []:
                connections = mc.listConnections(
                    control + "." + attr, s=1, d=0)
                if connections:
                    if "animCurve" not in mc.nodeType(connections[0], inherited=1):
                        continue
                mc.setKeyframe(control + "." + attr)
