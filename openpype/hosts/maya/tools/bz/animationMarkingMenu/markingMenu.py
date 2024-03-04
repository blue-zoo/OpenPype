from maya import cmds as mc
from . import functions
from . import legacyFunctions
from functools import partial

class animationMarkingMenu():
    def __init__(self, modelPanel):
        if mc.popupMenu("bzAnimationMarkingMenu"+modelPanel, ex=1):
            mc.deleteUI("bzAnimationMarkingMenu"+modelPanel)

        mc.popupMenu("bzAnimationMarkingMenu"+modelPanel, p=modelPanel, mm=1, b=2, sh=1, aob=1, pmc=self._build)

    def _build(self, mMenu, panel):
        mc.popupMenu(mMenu, e=1, deleteAllItems=1)

        # Get selection
        selection = mc.ls(sl=1, fl=1) or []

        # Build generic menu and bail early if no objects are selected, 
        # or selection is not an anim control
        if not selection or not self._isSelectionAnimControl(selection):
            self._buildGenericMenu(mMenu)
            return

        # Store selection states
        spaceSwitchable = self._isSelectionSpaceSwitchable(selection)
        ikFkSwitchable = self._isSelectionIkFkSwitchable(selection)
        orientSwitchable = self._isSelectionOrientSwitchable(selection)

        # If selection is a legacy rig, build legacy menu and bail 
        if self._isSelectionLegacy(selection):
            self._buildLegacyAssetMenu(mMenu, spaceSwitchable)
            return

        # Otherwise build correct menu
        self._buildAssetMenu(mMenu, selection[0], spaceSwitchable, ikFkSwitchable, orientSwitchable)

    @staticmethod
    def _isSelectionAnimControl(selection):
        '''Returns true if the final object in selection is an animation control.'''
        return mc.objExists(selection[-1] + ".animControl")

    @staticmethod
    def _isSelectionLegacy(selection):
        '''Returns true if the final object in selection is a legacy animation control.'''
        return not (
            mc.objExists(selection[-1] + ".assetInfo")
         or mc.objExists(mc.listConnections(selection[-1] + ".animControl", s=1)[0] + ".assetInfo"))

    @staticmethod
    def _isSelectionSpaceSwitchable(selection):
        '''Returns True if the final object in selection is space switchable.'''
        # Validate space attr
        if not mc.objExists(selection[-1] + ".space"):
            return False
        # Validate selection length
        elif len(selection) > 1:
            return False
        # Validation passed
        return True

    @staticmethod
    def _isSelectionIkFkSwitchable(selection):
        '''Returns True if the final object in selection is IKFK switchable.'''
        # Validate current or legacy match attr
        if not mc.objExists(selection[-1] + ".kMatchable") and not mc.objExists(selection[-1] + ".kMatchInfo"):
            return False
        # Validation passed
        return True

    @staticmethod
    def _isSelectionOrientSwitchable(selection):
        '''Returns True if the final object in selection is orient switchable.'''
        # Validate orient attr
        if not mc.objExists(selection[-1] + ".orient"):
            return False
        # Validate selection length
        elif len(selection) > 1:
            return False
        # Validate that rotation and all child channels are settable
        elif not mc.getAttr(selection[-1] + ".r", settable=True):
            return False
        for i in "xyz":
            if not mc.getAttr(selection[-1] + ".r" + i, settable=True):
                return False
        # Validation passed
        return True

    @staticmethod
    def _buildAssetMenu(mMenu, firstControl, spaceSwitchable, ikFkSwitchable, orientSwitchable):
        sets = functions.controlSets._getSelectedSets()[0]
        setStr = "Control Set"
        if len(sets) == 1:
            setStr = "\'" + functions.camelCaseToUnderscores(sets[0].split(".")[1]) + "\'"

        mc.menuItem(p=mMenu, rp="NW", label="Toggle Visibility", c=functions.generic.toggleSelectedVisibility)

        # Sets
        setsSub = mc.menuItem(p=mMenu, rp="NE", label="Control Set", subMenu=1, en=functions.controlSets.setAvailable(), bld=1)

        mc.menuItem(p=setsSub, rp="N", label="Select " + setStr, c=functions.controlSets.selectSet)
        mc.menuItem(p=setsSub, rp="S", label="Select %s and Children" % setStr, c=functions.controlSets.selectSetAndChildren)
        
        mc.menuItem(p=mMenu, rp="E", label="Select All Controls", c=functions.generic.selectControlsFromCharacterNode)

        # Selection (flip, mirror, isolate)
        selectionSub = mc.menuItem(p=mMenu, rp="SE", label="Selection", subMenu=1, bld=1)

        if functions.SELECTION_ISOLATED:
            mc.menuItem(p=selectionSub, rp="E", label="Clear Isolation", c=functions.generic.clearIsolated)
        else:
            mc.menuItem(p=selectionSub, rp="E", label="Isolate Selection", c=functions.generic.isolateSelected)

        mc.menuItem(p=selectionSub, rp="N", label="Flip Selection", c=functions.generic.flipSelection)
        mc.menuItem(p=selectionSub, rp="S", label="Mirror Selection", c=functions.generic.mirrorSelection)

        mc.menuItem(p=mMenu, rp="W", label="Toggle Referencing", c=functions.generic.toggleSelectedReference)
        mc.menuItem(p=mMenu, rp="N", label="Key Controls", c=functions.generic.keyControlsOnCharacterNode)
        mc.menuItem(p=mMenu, rp="SW", label="Toggle Smoothing", c=functions.generic.toggleSelectedSmoothing)

        mc.menuItem(p=mMenu, l='Revert Selected to Bind Pose', c=functions.bindPose.revertSelectedToBindPose)
        mc.menuItem(p=mMenu, l='Revert Asset to Bind Pose', c=functions.bindPose.revertAssetsToBindPose)

        # Space switch
        mc.menuItem(p=mMenu, d=1)
        spaceSwitchSub = mc.menuItem(p=mMenu, l="Switch Space", subMenu=1, en=spaceSwitchable, bld=1)
        if spaceSwitchable:
            for i, option in enumerate(functions.getAvailableSpaces(firstControl)):
                mc.menuItem(p=spaceSwitchSub, l=option, c=partial(functions.spaceMatch, i))

        # Kinematic toggle
        mc.menuItem(p=mMenu, d=1)
        mc.menuItem(p=mMenu, l="Toggle IK/FK", c=functions.ikFkMatch.doMatchAcrossTimeline, en=ikFkSwitchable, bld=1)
        mc.menuItem(p=mMenu, l="Match Stretch", c=animationMarkingMenu._toggleFkIkStretchMatching, 
            en=ikFkSwitchable, cb=mc.optionVar(q=functions.IKFK_STRETCH_OPTIONVAR_NAME))
        mc.menuItem(p=mMenu, l="Match Across Selected Keys", c=animationMarkingMenu._toggleFkIkAcrossTimeline, 
            en=ikFkSwitchable, cb=mc.optionVar(q=functions.IKFK_TIMELINE_OPTIONVAR_NAME))
        
        # Orient toggle
        mc.menuItem(p=mMenu, d=1)                   
        mc.menuItem(p=mMenu, l="Toggle Orient", c=functions.toggleOrientAndMatch, 
            en=orientSwitchable, bld=1)

    @staticmethod
    def _toggleFkIkStretchMatching(*_):

        # Get current value, or 0 if value type is incorrect
        oldValue = mc.optionVar(q=functions.IKFK_STRETCH_OPTIONVAR_NAME)
        if not isinstance(oldValue, int):
            oldValue = 0

        # Invert value and finalise
        newValue = sorted([1 - oldValue, 0, 1])[1]
        mc.optionVar(iv=[functions.IKFK_STRETCH_OPTIONVAR_NAME, newValue])

    @staticmethod
    def _toggleFkIkAcrossTimeline(*_):

        # Get current value, or 0 if value type is incorrect
        oldValue = mc.optionVar(q=functions.IKFK_TIMELINE_OPTIONVAR_NAME)
        if not isinstance(oldValue, int):
            oldValue = 0

        # Invert value and finalise
        newValue = sorted([1 - oldValue, 0, 1])[1]
        mc.optionVar(iv=[functions.IKFK_TIMELINE_OPTIONVAR_NAME, newValue])

    @staticmethod
    def _buildGenericMenu(mMenu):
        mc.menuItem(p=mMenu, rp='N', label='Toggle All Control Visibility', c=functions.generic.toggleAllVisibility)
        mc.menuItem(p=mMenu, rp='S', label='Clear Isolation', c=functions.generic.clearIsolated, en=functions.SELECTION_ISOLATED)    
        mc.menuItem(p=mMenu, rp='E', label='Toggle All Referencing', c=functions.generic.toggleAllReference)
        mc.menuItem(p=mMenu, rp='W', label='Toggle All Smoothing', c=functions.generic.toggleAllSmoothing)
        mc.menuItem(p=mMenu, label='All Smoothing Off', c=functions.generic.unsmoothAll)
        mc.menuItem(p=mMenu, label='All Referencing On', c=functions.generic.referenceAll)

    @staticmethod
    def _buildLegacyAssetMenu(mMenu, spaceSwitchable):
        mc.menuItem(p=mMenu, rp="NW", label="Toggle Visibility", c=legacyFunctions.toggle_controls)
        mc.menuItem(p=mMenu, rp="NE", label="Select Set", en=0)
        mc.menuItem(p=mMenu, rp="E", label="Select All Controls", c=legacyFunctions.selectAllControls)
        mc.menuItem(p=mMenu, rp="W", label="Toggle Referencing", c=functions.generic.toggleSelectedReference)
        mc.menuItem(p=mMenu, rp="N", label="Key Controls", c=legacyFunctions.keyAllControls)
        mc.menuItem(p=mMenu, rp="SW", label="Toggle Smoothing", c=functions.generic.toggleSelectedSmoothing)
        mc.menuItem(p=mMenu, rp="S", label="LEGACY MODE", en=0, bld=1)

        mc.menuItem(p=mMenu, l='Revert Selected to Bind Pose', c=legacyFunctions.revertSelectedToBindpose)
        mc.menuItem(p=mMenu, l='Revert Asset to Bind Pose', c=legacyFunctions.revertSelectedAssetsToBindpose)

        spaceSwitchSub = mc.menuItem(p=mMenu, l="Space Switch", subMenu=1, en=spaceSwitchable)
        if spaceSwitchable:
            for i, option in enumerate(functions.getAvailableSpaces(mc.ls(sl=1, fl=1)[0])):
                mc.menuItem(p=spaceSwitchSub, l=option, c=partial(functions.spaceMatch, i))

        sel = mc.ls(sl=1, fl=1)
        ikFkSwitchCtl = False
        if len(sel) == 1:
            ikFkSwitchCtl = legacyFunctions.return_ik_fk_control(mc.ls(sl=1, fl=1)[0])
        ikFkSwitchSub = mc.menuItem(p=mMenu, l="IK/FK Switch", subMenu=1, en=bool(ikFkSwitchCtl))
        mc.menuItem(p=ikFkSwitchSub, l="FK -> IK", c=partial(legacyFunctions.perform_match_ik_fk, ikFkSwitchCtl))
        mc.menuItem(p=ikFkSwitchSub, l="IK -> FK", c=partial(legacyFunctions.perform_match_fk_ik, ikFkSwitchCtl))


def deleteOldMarkingMenu():
    for each in mc.lsUI(m=1):
        if "BZMENUMARK" in each:
            mc.deleteUI(each)


def deleteNewMarkingMenu():
    for each in mc.lsUI(m=1):
        if "bzAnimationMarkingMenu" in each:
            mc.deleteUI(each)


def initAnimationMarkingMenu():
    for panel in (mc.getPanel(typ='modelPanel') or []):
        animationMarkingMenu(panel)
