"""Script by Harry Latham."""

import re
import maya.cmds as mc

def renameSceneObjects(nodes=None):
    """
    Renames selected objects and their entire hierarchy based on specific project conventions.

    - Prefixes: C_, L_, R_ (default C_)
    - Suffixes: _GRP (groups), _PLY (geometry), _PRX (Redshift Proxies)
    - Naming:
        - Groups/Proxies: Adds a unique IDxxxx (e.g., ID0001)
        - Geometry: Adds a unique 4-digit number (e.g., 0001)
    - Cleanup: Removes extra underscores from base names.
    - Special: 'Brick_' or 'Part_' names are truncated (e.g., Brick_123_abc -> Brick123)
    - Special: For geometry, strips trailing numbers from base name (e.g., knob01D1 -> knob01D)
    """
    # --- Define Naming Conventions ---
    PREFIXES = {'C_', 'L_', 'R_'}
    SUFFIXES = {'_GRP', '_PLY', '_PRX'}
    DEFAULT_PREFIX = 'C_'
    GROUP_SUFFIX = '_GRP'
    GEO_SUFFIX = '_PLY'
    LOC_SUFFIX = '_LOC'
    PROXY_SUFFIX = '_PRX'

    # --- Get Objects ---
    if nodes is None:
        # Get selected transform roots
        selected_roots = mc.ls(selection=True, long=True, type='transform')
        if not selected_roots:
            print("No objects selected to rename.")
            return []
        # Get all descendants (dag=True) of the selection, including the roots
        objects = mc.ls(selected_roots, dag=True, long=True, type='transform')
    else:
        # Get all transforms in the scene
        objects = mc.ls(nodes, long=True, type='transform')

    if not objects:
        print("No objects found to rename.")
        return []

    # Sort by hierarchy (deepest first) to avoid renaming parents before children
    objects.sort(key=lambda obj: obj.count('|'), reverse=True)

    # --- Process Objects ---
    name_counts = {} # Tracks counts for each base name (e.g., "C_Box_PLY")
    result = [] # Tracks what was renamed

    for obj in objects:
        if not mc.objExists(obj):
            # Object might have been renamed already as part of a hierarchy
            continue

        # Skip default camera transforms
        if obj in ('|persp', '|top', '|front', '|side'):
            continue

        original_full_path = obj
        original_short_name = obj.split('|')[-1]

        # --- 1. Determine Type and Target Suffix ---
        target_suffix = ''
        # Get non-intermediate shapes
        shape_nodes = mc.listRelatives(obj, shapes=True, fullPath=True, noIntermediate=True)

        if shape_nodes:
            # Has shapes, check if it's a proxy
            is_proxy = is_locator = False
            for shape in shape_nodes:
                if mc.listConnections(shape, type="RedshiftProxyMesh"):
                    is_proxy = True
                    break
                if mc.nodeType(shape) == 'locator':
                    is_locator = True
                    break

            if is_proxy:
                target_suffix = PROXY_SUFFIX
            elif is_locator:
                target_suffix = LOC_SUFFIX
            else:
                # It's standard geometry
                target_suffix = GEO_SUFFIX
        else:
            # No shapes, assume it's a group
            target_suffix = GROUP_SUFFIX

        # --- 2. Determine Base Name (Handling Special Cases) ---
        base_name = original_short_name

        if base_name.startswith('Brick_') or base_name.startswith('Part_'):
            # Special rule for Brick/Part: e.g., "Brick_73983_..." -> "Brick73983"
            parts = base_name.split('_')
            if len(parts) >= 2:
                base_name = parts[0] + parts[1]
        else:
            # General Cleanup: Remove prefix/suffix, then clean underscores
            temp_name = original_short_name

            # Strip known prefix from temp name
            for p in PREFIXES:
                if temp_name.startswith(p):
                    temp_name = temp_name[len(p):]
                    break

            # Strip known suffix from temp name
            for s in SUFFIXES:
                if temp_name.endswith(s):
                    temp_name = temp_name[:-len(s)]
                    break

            # Clean all remaining underscores from the "middle" part
            base_name = temp_name.replace('_', '')

        # --- 2.5. *** NEW *** Strip trailing numbers for Geometry ---
        # If it's geometry, strip trailing numbers from the base_name
        # so knob01D1 and knob01D2 are both treated as knob01D
        if target_suffix == GEO_SUFFIX:
            base_name = re.sub(r'\d+$', '', base_name)

        # --- 3. Determine Final Prefix ---
        final_prefix = ''
        # Check if the *original* name had a valid prefix
        for p in PREFIXES:
            if original_short_name.startswith(p):
                final_prefix = p
                break

        if not final_prefix:
            # No valid prefix found, use default
            final_prefix = DEFAULT_PREFIX

        # --- 4. Construct Base Name and Find Unique ID ---
        # This is the name *before* the ID, used for tracking counts
        name_base_for_counting = "{}{}{}".format(final_prefix, base_name, target_suffix)

        # Get the next available count for this base name
        current_count = name_counts.get(name_base_for_counting, 0)

        while True:
            current_count += 1

            # --- *** MODIFIED *** Naming Logic ---
            if target_suffix == GEO_SUFFIX:
                # Geometry gets a 4-digit number (e.g., 0001)
                number_string = "{:04d}".format(current_count)
                final_name = "{}{}{}{}".format(final_prefix, base_name, number_string, target_suffix)
            else:
                # Groups/Proxies get an ID string (e.g., ID0001)
                id_string = "ID{:04d}".format(current_count)
                final_name = "{}{}{}{}".format(final_prefix, base_name, id_string, target_suffix)
            # --- End Modified Naming Logic ---

            if not mc.objExists(final_name):
                # This name is unique, we can use it
                break

        # --- 5. Rename ---
        try:
            # Rename the object using its FULL, UNIQUE PATH to avoid ambiguity.
            new_name = mc.rename(original_full_path, final_name)

            # Successful rename, update the master count
            name_counts[name_base_for_counting] = current_count
            result.append({'oldName': original_full_path, 'newName': new_name, 'failed': False, 'type': 'convention'})
        except RuntimeError as e:
            # Failed to rename
            result.append({'oldName': original_full_path, 'newName': final_name, 'failed': True, 'type': 'convention', 'reason': str(e)})

    return result

# --- Original Functions (Preserved for reference, but not used by new main) ---

def renameDuplicates(selection=True):
    """Renames nodes with duplicate names

    Args:
        selection (bool): If True, renames objects in the current selection only.
                          If False, renames objects in the whole scene.

    Returns:
        list: List of renamed nodes
    """

    # Find objects with duplicate names in the selection or whole scene
    if selection:
        duplicates = [f for f in mc.ls(selection=True, type='transform') if '|' in f]
    else:
        duplicates = [f for f in mc.ls(type='transform') if '|' in f]

    # Sort duplicates by hierarchy to rename child objects first
    duplicates.sort(key=lambda obj: (obj.count('|') * -1, obj))

    renamed = []
    result = []
    for name in duplicates:
        # Extract the base name
        m = re.compile("[^|]*$").search(name)
        shortname = m.group(0)

        # Check if all the names with this short name have been renamed (don't rename the first one)
        if not shortname in renamed:
            renamed.append(shortname)
            continue

        # Extract the numeric suffix e.g., group1_GRP1 = group1_GRP
        m2 = re.compile(".*[^0-9]").match(shortname)
        if m2:
            stripSuffix = m2.group(0)
        else:
            stripSuffix = shortname

        # Split off the last underscore into basename, suffix e.g., group1_GRP = group1, GRP
        suffix = stripSuffix.split("_")[-1]
        baseName = "_".join(stripSuffix.split("_")[:-1])

        # Extract the numeric suffix from basename e.g., group1 = group
        m2 = re.compile(".*[^0-9]").match(baseName)
        if m2:
            baseName = m2.group(0)

        # Calculate the new name, cannot use # in rename because basename may already exist in other objects
        number = 1
        newname = '{}{}_{}'.format(baseName, number, suffix)
        while mc.objExists(newname):
            number += 1
            newname = '{}{}_{}'.format(baseName, number, suffix)

        # Rename the object
        try:
            newname = mc.rename(name, newname)
        except RuntimeError:
            # Record the failure
            result.append({'oldName': name, 'newName': newname, 'failed': True, 'type': 'duplicate'})
            continue

        result.append({'oldName': name, 'newName': newname, 'failed': False, 'type': 'duplicate'})

    return result

def renameProxies(selection=True):
    """Rename selected transforms so the shape node, rsproxy, and rsproxyplaceholder have the correct name

    Args:
        selection (bool): If True, renames objects in the current selection only.
                          If False, renames objects in the whole scene.

    Returns:
        list: List of renamed nodes
    """
    # Get selected transforms
    if selection:
        selected = mc.ls(selection=True, type='transform')
    else:
        selected = mc.ls(type='transform')

    result = []
    for transformName in selected:
        m = re.compile("[^|]*$").search(transformName)
        shortname = m.group(0)

        # Rename shape node
        shape_node = mc.listRelatives(transformName, shapes=True, fullPath=True)
        if shape_node is None:
            continue
        if shape_node[0] in ('|persp|perspShape', '|front|frontShape', '|side|sideShape', '|top|topShape'):
            continue
        shape_nodeName = shortname + "Shape"
        try:
            shape_nodeName = mc.rename(shape_node[0], shape_nodeName)
        except RuntimeError:
            # Record the failure and move on to the next transform node
            result.append({'oldName': shape_node[0], 'newName': shape_nodeName, 'failed': True, 'type': 'Shape'})
            continue

        m = re.compile("[^|]*$").search(shape_node[0])
        shape_shortname = m.group(0)
        if not (shape_shortname == shape_nodeName or shape_shortname == "|" + shape_nodeName):
            result.append({'oldName': shape_node[0], 'newName': shape_nodeName, 'failed': False, 'type': 'Shape'})

        # Rename RS proxy node
        proxyNode = mc.listConnections(shape_nodeName, type="RedshiftProxyMesh")
        if proxyNode is None:
            continue
        if not proxyNode[0]:
            continue
        rsProxyName = shortname + "Proxy"

        try:
            rsProxyName = mc.rename(proxyNode[0], rsProxyName)
        except RuntimeError:
            # Record the failure and move on to the next transform node
            result.append({'oldName': proxyNode[0], 'newName': rsProxyName, 'failed': True, 'type': 'Proxy'})
            continue

        if not (proxyNode[0] == rsProxyName or proxyNode[0] == "|" + rsProxyName):
            result.append({'oldName': proxyNode[0], 'newName': rsProxyName, 'failed': False, 'type': 'Proxy'})

        # Rename RS Placeholder
        proxyShape_input = mc.listConnections(rsProxyName + '.outMesh', plugs=True, source=True, destination=True)
        if proxyShape_input is None:
            continue
        proxyShape = proxyShape_input[0].split(".")
        if proxyShape is None:
            continue

        rsProxyShapeName = shortname + "ProxyPlaceholder"
        try:
            rsProxyShapeName = mc.rename(proxyShape[0], rsProxyShapeName)
        except RuntimeError:
            # Record the failure and move on to the next transform node
            result.append({'oldName': proxyShape[0], 'newName': rsProxyShapeName, 'failed': True,
                           'type': 'ProxyPlaceholder'})
            continue

        if not (proxyShape[0] == rsProxyShapeName or proxyShape[0] == "|" + rsProxyShapeName):
            result.append({'oldName': proxyShape[0], 'newName': rsProxyShapeName, 'failed': False,
                           'type': 'ProxyPlaceholder'})

    return result

def removeNumbers(selection=True):
    """Removes numbers after suffixes e.g., group1_GRP1 = group1_GRP

    Args:
        selection (bool): If True, removes numbers from objects in the current selection only.
                          If False, removes numbers from objects in the whole scene.

    Returns:
        list: List of renamed nodes
    """
    # Get objects in the selection or whole scene
    if selection:
        all_objects = mc.ls(selection=True, dag=True, long=True)
    else:
        all_objects = mc.ls(dag=True, long=True)

    result = []
    for objName in all_objects:
        # Extract the base name
        m = re.compile("[^|]*$").search(objName)
        shortname = m.group(0)

        # Extract the numeric suffix e.g., group1_GRP1 = group1_GRP
        stripSuffix = re.sub(r'\d+$', '', shortname)
        if stripSuffix == shortname:
            continue

        # Split off the last underscore into basename, suffix e.g., group1_GRP = group1, GRP
        suffix = stripSuffix.split("_")[-1]
        if not suffix in ['PLY', 'PRX', 'GRP', 'LOC']:
            continue
        baseName = "_".join(stripSuffix.split("_")[:-1])

        # Remove numbers from basename
        baseName = re.sub(r'\d+$', '', baseName)

        # Calculate the new name, cannot use # in rename because basename may already exist in other objects
        number = 1
        newname = '{}{}_{}'.format(baseName, number, suffix)
        while mc.objExists(newname):
            number += 1
            newname = '{}{}_{}'.format(baseName, number, suffix)

        try:
            newname = mc.rename(objName, newname)
        except RuntimeError:
            # Record the failure and move on to the next transform node
            result.append({'oldName': objName, 'newName': newname, 'failed': True, 'type': 'number'})
            continue
        result.append({'oldName': objName, 'newName': newname, 'failed': False, 'type': 'number'})

    return result

# --- UPDATED MAIN FUNCTION ---
# This now calls the new, all-in-one renaming function.
def main():
    """
    Runs the new renaming convention on the current selection.
    """
    print("Running new scene object renaming convention...")
    renaming_results = renameSceneObjects()

    print("Renaming complete. {} objects processed.".format(len(renaming_results)))
    failures = [r for r in renaming_results if r['failed']]
    if failures:
        print("WARNING: {} objects failed to rename:".format(len(failures)))
        for f in failures:
            print("  - {} -> {} (Reason: {})".format(f['oldName'], f['newName'], f.get('reason', 'Unknown')))

if __name__ == '__main__':
    main()
