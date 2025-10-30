"""Script by Harry Latham."""

import maya.cmds as cmds
import maya.mel as mel
import os
import sys

# --- Configuration ---
BASE_LIBRARY_PATH = r"Y:\LEGO\2013s_LegoCitySeries4\Libraries\brickDatabase\CommonParts"

STYLE_PATHS = {
    "Render": os.path.join(BASE_LIBRARY_PATH, "Render"),
    "Cinematic": os.path.join(BASE_LIBRARY_PATH, "Cinematic"),
    "Realtime": os.path.join(BASE_LIBRARY_PATH, "Realtime")
}

# The custom attribute that identifies a common part
COMMON_PART_ATTR = "VME_CommonPartType"

# --- Main Logic ---

def find_fbx_case_insensitive(directory, filename):
    """Finds a file in a directory, ignoring case."""
    if not os.path.isdir(directory):
        cmds.warning("Directory does not exist: %s" % directory)
        return None

    target_name_lower = filename.lower()
    try:
        for f in os.listdir(directory):
            if f.lower() == target_name_lower:
                return os.path.join(directory, f)
    except Exception as e:
        cmds.warning("Could not list directory: %s. Error: %s" % (directory, e))
        return None

    return None

def copy_user_attributes(source_obj, dest_obj):
    """Copies user-defined attributes from source to destination."""
    user_attrs = cmds.listAttr(source_obj, userDefined=True) or []

    for attr_name in user_attrs:
        if cmds.objExists(dest_obj + "." + attr_name):
            continue

        try:
            attr_type = cmds.getAttr(source_obj + "." + attr_name, type=True)
            attr_val = cmds.getAttr(source_obj + "." + attr_name)

            if attr_type == 'string':
                cmds.addAttr(dest_obj, longName=attr_name, dataType='string')
                cmds.setAttr(dest_obj + '.' + attr_name, attr_val, type='string')

            elif attr_type in ['double', 'float', 'long', 'short', 'byte', 'bool']:
                kwargs = {'longName': attr_name, 'attributeType': attr_type}
                if attr_type == 'bool':
                    kwargs['attributeType'] = 'bool'
                elif attr_type in ['long', 'short', 'byte']:
                    kwargs['attributeType'] = 'long'
                elif attr_type in ['double', 'float']:
                    kwargs['attributeType'] = 'double'

                cmds.addAttr(dest_obj, **kwargs)
                cmds.setAttr(dest_obj + '.' + attr_name, attr_val)

            else:
                print("Cannot copy attribute '%s' of unsupported type: %s" % (attr_name, attr_type))

        except Exception as e:
            cmds.warning("Failed to copy attribute: %s. Error: %s" % (attr_name, e))

def ensure_fbx_plugin_loaded():
    """Ensures FBX plugin is loaded."""
    try:
        if not cmds.pluginInfo("fbxmaya.mll", query=True, loaded=True):
            cmds.loadPlugin("fbxmaya.mll", quiet=True)
        return True
    except Exception as e:
        cmds.warning("Could not load FBX plugin: %s" % e)
        return False

def import_fbx_get_root(fbx_path):
    """Imports FBX and returns the root transform node."""
    if not ensure_fbx_plugin_loaded():
        return None

    # Store current scene state to find new nodes
    transforms_before = set(cmds.ls(type='transform', long=True))

    try:
        # Simple import without namespace
        new_nodes = cmds.file(fbx_path, i=True, type="FBX", ignoreVersion=True, mergeNamespacesOnClash=False, namespace=":", returnNewNodes=True)

        # Find new transforms
        transforms_after = set(cmds.ls(type='transform', long=True))
        new_transforms = transforms_after - transforms_before

        # Delete non transform / mesh nodes
        cmds.sets(new_transforms, edit=True, forceElement='initialShadingGroup')
        toDelete = set(cmds.ls(new_nodes)) - set(cmds.ls(new_nodes, type=['transform', 'mesh', 'locator']))
        if toDelete:
            cmds.delete(toDelete)

        if new_transforms:
            # Return the first new transform (usually the root)
            return list(new_transforms)[0]

    except Exception as e:
        cmds.warning("FBX import failed: %s" % e)

    return None

def swap_common_part(original_obj, style, path):
    """
    Simple replacement: imports FBX and replaces original object.
    """
    if not cmds.objExists(original_obj):
        return None

    if not cmds.objExists(original_obj + "." + COMMON_PART_ATTR):
        return None

    # Get part name from attribute
    part_name = cmds.getAttr(original_obj + "." + COMMON_PART_ATTR)
    if not part_name:
        return None

    original_short_name = original_obj.split('|')[-1]

    # Find FBX file
    style_folder = os.path.join(path, style)
    if not os.path.exists(style_folder):
        return None

    fbx_name = part_name + ".fbx"
    fbx_path = find_fbx_case_insensitive(style_folder, fbx_name)

    if not fbx_path:
        cmds.warning("FBX not found: %s" % fbx_name)
        return None

    print("Swapping '%s' -> %s" % (original_short_name, fbx_name))

    # Store original data
    try:
        original_matrix = cmds.xform(original_obj, q=True, worldSpace=True, matrix=True)
        original_parent = cmds.listRelatives(original_obj, parent=True, fullPath=True)
        original_visibility = cmds.getAttr(original_obj + ".visibility")
    except Exception as e:
        cmds.warning("Could not get transform data: %s" % e)
        return None

    # Import new geometry
    imported_root = import_fbx_get_root(fbx_path)

    if not imported_root:
        cmds.warning("Failed to import: %s" % fbx_path)
        return None

    # Apply original transform
    cmds.xform(imported_root, worldSpace=True, matrix=original_matrix)
    cmds.setAttr(imported_root + ".visibility", original_visibility)

    # Copy user attributes
    copy_user_attributes(original_obj, imported_root)

    # Reparent
    if original_parent:
        try:
            imported_root = cmds.parent(imported_root, original_parent[0])[0]
        except Exception as e:
            print("Note: Could not reparent: %s" % e)

    # Delete original and rename new
    cmds.delete(original_obj)

    try:
        final_name = cmds.rename(imported_root, original_short_name)
    except:
        final_name = cmds.rename(imported_root, original_short_name + "#")

    # Assign material
    material_name = "shaders:Anim_MasterShader_MAT"
    if cmds.objExists(material_name):
        # Use destination=True instead of ets
        shading_groups = cmds.listConnections(material_name, destination=True, type='shadingEngine')
        if shading_groups:
            shading_group = shading_groups[0]
            shapes = cmds.listRelatives(final_name, allDescendents=True, type='mesh', fullPath=True)
            if shapes:
                try:
                    cmds.sets(shapes, edit=True, forceElement=shading_group)
                except Exception as e:
                    print("Note: Could not assign material: %s" % e)

    print("... Success: '%s'" % final_name)
    return final_name

def run_style_update(style, path):
    """Finds all common parts and swaps them."""
    print("--- Starting Common Part Update: %s ---" % style)

    # Find all objects with the common part attribute
    parts_to_swap = []
    for transform in cmds.ls(type='transform', long=True):
        if cmds.objExists(transform + "." + COMMON_PART_ATTR):
            parts_to_swap.append(transform)

    if not parts_to_swap:
        cmds.warning("No common parts found in scene")
        return

    print("Found %d parts to update" % len(parts_to_swap))

    success_count = 0
    new_selection = []

    for part in parts_to_swap:
        try:
            new_part = swap_common_part(part, style, path)
            if new_part:
                new_selection.append(new_part)
                success_count += 1
        except Exception as e:
            cmds.warning("Failed to swap %s: %s" % (part, e))

    if new_selection:
        cmds.select(new_selection, replace=True)

    print("--- Complete: %d/%d parts swapped ---" % (success_count, len(parts_to_swap)))

# --- UI ---
class CommonPartStylerUI(object):
    def __init__(self):
        self.window_name = "CommonPartStylerWindow"

    def create(self):
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        cmds.window(self.window_name, title="Common Part Styler", width=300)
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10)

        cmds.text("Select style:")
        self.style_menu = cmds.optionMenu(label="Style")
        for style in sorted(STYLE_PATHS.keys()):
            cmds.menuItem(label=style)

        cmds.optionMenu(self.style_menu, edit=True, value="Render")
        cmds.separator(height=10)

        cmds.button(
            label="Update All Common Parts",
            command=self.on_update,
            height=40,
            backgroundColor=(0.4, 0.6, 0.4)
        )

        cmds.showWindow(self.window_name)

    def on_update(self, *args):
        style = cmds.optionMenu(self.style_menu, q=True, value=True)
        cmds.undoInfo(openChunk=True)
        try:
            run_style_update(style)
        except Exception as e:
            cmds.warning("Error: %s" % e)
        finally:
            cmds.undoInfo(closeChunk=True)

# --- Run ---
if __name__ == "__main__":
    ui = CommonPartStylerUI()
    ui.create()
