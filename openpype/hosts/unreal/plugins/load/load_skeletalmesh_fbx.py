# -*- coding: utf-8 -*-
"""Load Skeletal Meshes form FBX."""
import os
import re

from openpype.pipeline import (
    get_representation_path,
    AYON_CONTAINER_ID
)
from openpype.hosts.unreal.api import plugin
from openpype.hosts.unreal.api import pipeline as unreal_pipeline
import unreal  # noqa

BOILERPLATE_BP_PATH = "/Game/Utilities/UtilityBlueprints/BP_BZAsset_BoilerPlate"

SOCKET_BONE_PREFIX = "_sock_"   # all sockets are confirmed to start with this
SOCKET_FLIP_SCALE = (1, -1, -1)


def _flip_socket_bones_on_mesh(skeletal_mesh_path):
    """Mirror socket bones on a freshly (re)imported SKM.

    Automated equivalent of the 'Skeletal Mesh Update' editor utility widget:
    scales every bone whose name starts with `_sock_` by `(1, -1, -1)`.
    Imported locally and wrapped so a failure only logs — it must never abort
    the asset import pipeline.
    """
    try:
        import skeletal_mesh_helpers  # lives in /Content/Python
        skeletal_mesh_helpers.set_scale_for_bones_matching(
            skeletal_mesh_path, SOCKET_BONE_PREFIX,
            scale=SOCKET_FLIP_SCALE, prefix_only=True)
    except Exception as exc:
        unreal.log_warning(f"[Socket Flip] Skipped {skeletal_mesh_path}: {exc}")


def get_blueprint_name(asset_name, version):
    """Add BP_ prefix and version suffix to asset name."""
    return f"BP_{asset_name}_v{version:03d}"


def clean_instance_name(instance_name):
    """Strip subset name and trailing underscore from instance name.

    Transforms 'PRP_ArcticPole_rigMain_01_' to 'PRP_ArcticPole_01'.
    Subset names are camelCase (start with lowercase letter).
    """
    return re.sub(r'_([a-z][a-zA-Z0-9]*)_(\d+)_?$', r'_\2', instance_name)


def set_skeletal_mesh_on_blueprint(bp_asset, skeletal_mesh):
    """Set the skeletal mesh on a Blueprint's inherited AssetSkeletalMesh component.

    Uses SubobjectDataSubsystem to find the inherited SkeletalMeshComponent,
    then SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint() to
    get the child-specific override (not the parent's shared template).
    """
    bp_name = bp_asset.get_name()
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    if not subsystem:
        print(f"[BP Wrapper] ERROR: Could not get SubobjectDataSubsystem")
        return False

    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = subsystem.k2_gather_subobject_data_for_blueprint(context=bp_asset)

    # Find the AssetSkeletalMesh SubobjectData
    target_data = None
    for handle in handles:
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        if not data:
            continue
        export = data.export_text()
        if 'SkeletalMeshComponent' in export and 'AssetSkeletalMesh' in export:
            target_data = data
            break

    if not target_data:
        print(f"[BP Wrapper] ERROR: No AssetSkeletalMesh component found on {bp_name}")
        return False

    # get_object_for_blueprint returns the child BP's override component,
    # not the parent's shared template
    child_comp = lib.get_object_for_blueprint(target_data, bp_asset)
    if not child_comp:
        print(f"[BP Wrapper] ERROR: get_object_for_blueprint returned None for {bp_name}")
        return False

    child_comp.set_editor_property('skeletal_mesh_asset', skeletal_mesh)
    bp_asset.modify()
    print(f"[BP Wrapper] Set skeletal mesh on {bp_name}")
    return True


def validate_blueprint_has_component(bp_asset):
    """
    Check if a Blueprint has the AssetSkeletalMesh component.

    Args:
        bp_asset: The Blueprint asset to validate

    Returns:
        bool: True if the component exists, False otherwise
    """
    try:
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        if not subsystem:
            return False

        handles = subsystem.k2_gather_subobject_data_for_blueprint(context=bp_asset)

        for handle in handles:
            data = subsystem.k2_find_subobject_data_from_handle(handle)
            if not data:
                continue

            export = data.export_text()
            if 'SkeletalMeshComponent' in export and 'AssetSkeletalMesh' in export:
                return True

        return False
    except:
        return False


class SkeletalMeshFBXLoader(plugin.Loader):
    """Load Unreal SkeletalMesh from FBX."""

    families = ["rig", "skeletalMesh"]
    label = "Import FBX Skeletal Mesh"
    representations = ["fbx"]
    icon = "cube"
    color = "orange"

    def load(self, context, name, namespace, options):
        """Load and containerise representation into Content Browser.

        This is a two step process. First, import FBX to temporary path and
        then call `containerise()` on it - this moves all content to new
        directory and then it will create AssetContainer there and imprint it
        with metadata. This will mark this path as container.

        Args:
            context (dict): application context
            name (str): subset name
            namespace (str): in Unreal this is basically path to container.
                             This is not passed here, so namespace is set
                             by `containerise()` because only then we know
                             real path.
            options (dict): Those would be data to be imprinted. This is not
                used now, data are imprinted by `containerise()`.

        Returns:
            list(str): list of container content

        """
        # Create directory for asset and Ayon container
        root = "/Game/Ayon/"

        if options and options.get("asset_dir"):
            root = options["asset_dir"]
        asset = context.get('asset').get('name')
        suffix = "_CON"
        if asset:
            asset_name = "{}_{}".format(asset, name)
        else:
            asset_name = "{}".format(name)
        version = context.get('version').get('name')
        tools = unreal.AssetToolsHelpers().get_asset_tools()

        # Version check for 5.7+ BP wrapping
        ue_version = unreal.SystemLibrary.get_engine_version().split('.')
        ue_major = int(ue_version[0])
        ue_minor = int(ue_version[1])
        is5_7_or_later = ue_major == 5 and ue_minor >= 7

        import pprint

        print(pprint.pformat(context))
        print( context.get("hierarchy",None) )
        hier = context.get("representation",{}).get("context").get("hierarchy",None)
        if hier:
            root +="/"+hier


        asset_dir, container_name = tools.create_unique_asset_name(
            f"{root}/{asset}/{name}_v{version:03d}", suffix="")

        container_name += suffix
        #
        #
        # FIXME - Does not load fbx if folder exists, should check if subassets of folder exist

        if not (unreal.EditorAssetLibrary.does_asset_exist(asset_dir + '/' + asset_name)
                and unreal.EditorAssetLibrary.does_asset_exist(asset_dir + '/' + asset_name + '_Skeleton')):
            unreal.EditorAssetLibrary.make_directory(asset_dir)

            task = unreal.AssetImportTask()

            path = self.filepath_from_context(context)
            task.set_editor_property('filename', path)
            task.set_editor_property('destination_path', asset_dir)
            task.set_editor_property('destination_name', asset_name)
            task.set_editor_property('replace_existing', True)
            task.set_editor_property('automated', True)
            task.set_editor_property('save', False)

            # set import options here
            options = unreal.FbxImportUI()
            options.set_editor_property('import_as_skeletal', True)
            options.set_editor_property('import_animations', True)
            options.set_editor_property('import_mesh', True)
            options.set_editor_property('import_materials', True)
            options.set_editor_property('import_textures', False)
            options.set_editor_property('skeleton', None)
            options.set_editor_property('create_physics_asset', False)

            options.anim_sequence_import_data.set_editor_property(
                'import_custom_attribute', True)
            options.anim_sequence_import_data.set_editor_property(
                'remove_redundant_keys', False)
            options.anim_sequence_import_data.set_editor_property(
                'set_material_drive_parameter_on_custom_attribute', True)
            options.anim_sequence_import_data.set_editor_property(
                'do_not_import_curve_with_zero', False)

            options.set_editor_property(
                'mesh_type_to_import',
                unreal.FBXImportType.FBXIT_SKELETAL_MESH)

            options.skeletal_mesh_import_data.set_editor_property(
                'import_content_type',
                unreal.FBXImportContentType.FBXICT_ALL)
            # set to import normals, otherwise Unreal will compute them
            # and it will take a long time, depending on the size of the mesh
            options.skeletal_mesh_import_data.set_editor_property(
                'normal_import_method',
                unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)

            options.skeletal_mesh_import_data.set_editor_property(
                'import_meshes_in_bone_hierarchy',
                True)

            # set the search location for materials to All Assets, so it
            # searches across the project, but for anything that it doesn't
            # find, set the default action to _Create New Instanced Materials_,
            # so we get instances of a base material. Ideally we want to have
            # the instances created with no base material, but in that case it
            # just creates Materials, so instead we create a temporary material,
            # which gets deleted after the FBX import. Admittedly, that's a horrible
            # workflow, but it's the only way I have found to create material instances
            # with no base material
            created_temp_material = False
            temp_material_name = '_temp_base_MAT'
            temp_material_path = '/Game/' + temp_material_name
            if not unreal.Paths.file_exists(temp_material_path):
                unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                    temp_material_name, '/Game', unreal.Material, unreal.MaterialFactoryNew()
                )
                created_temp_material = True

            fbx_import_data = unreal.FbxTextureImportData()
            fbx_import_data.set_editor_property(
                'base_material_name', unreal.SoftObjectPath(temp_material_path))

            fbx_import_data.set_editor_property(
                'material_search_location',
                unreal.MaterialSearchLocation.ALL_ASSETS)

            options.set_editor_property('texture_import_data', fbx_import_data)

            task.options = options
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])  # noqa: E501

            # Load the asset we just imported
            newly_imported_SKM = unreal.load_asset(asset_dir + '/' + asset_name)

            if newly_imported_SKM:
                # We can't just set the editor property, we have to access
                # via Nanite Settings object then set it back, weird
                nanite_settings = newly_imported_SKM.get_editor_property("nanite_settings")
                nanite_settings.enabled = False
                newly_imported_SKM.set_editor_property("nanite_settings", nanite_settings)

                # Save the asset directly, we are directly after the asset
                # I am considering not doing this save since we're not
                # directly saving the skeletal mesh either, inconsistent
                unreal.EditorAssetLibrary.save_loaded_asset(newly_imported_SKM)

                # Mirror-flip socket bones (`_sock_` prefix) on the fresh SKM
                _flip_socket_bones_on_mesh(asset_dir + '/' + asset_name)


            if created_temp_material:
                # Delete temporary base material, only if we created it, as we
                # could have run into a case where a material with that path
                # has already been created manually
                unreal.EditorAssetLibrary.delete_asset(temp_material_path)

            # Check if we have a previous version and if it has any
            # blueprints in its version folder copy them over to
            # the new one
            # NOTE: i can't find a way of just listing a directory, so
            # instead I am querying all assets in the asset directory
            # and getting their parents to get all version folders
            asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
            asset_parent_dir = unreal.Paths.get_path(asset_dir)
            latest_version_folder = ''
            for asset_data in asset_registry.get_assets_by_path(
                        asset_parent_dir, recursive=True):
                package_parent = unreal.Paths.get_path(asset_data.package_name)
                package_parent_parent = unreal.Paths.get_path(package_parent)
                if package_parent_parent == asset_parent_dir\
                        and package_parent > latest_version_folder\
                        and package_parent < asset_dir:
                    latest_version_folder = package_parent

            if latest_version_folder:
                if is5_7_or_later:
                    # 5.7+: Find previous version's BP and copy with new version suffix
                    prev_version_match = re.search(r'_v(\d+)$', latest_version_folder)
                    if prev_version_match:
                        prev_version = int(prev_version_match.group(1))
                        prev_bp_name = get_blueprint_name(asset, prev_version)
                        new_bp_name = get_blueprint_name(asset, version)
                        prev_bp_path = f"{latest_version_folder}/{prev_bp_name}"
                        if unreal.EditorAssetLibrary.does_asset_exist(prev_bp_path):
                            prev_bp = unreal.EditorAssetLibrary.load_asset(prev_bp_path)
                            if prev_bp and validate_blueprint_has_component(prev_bp):
                                unreal.EditorAssetLibrary.duplicate_asset(
                                    prev_bp_path,
                                    f"{asset_dir}/{new_bp_name}")
                else:
                    # Pre-5.7: Copy all BPs from previous version
                    blueprints_to_copy = unreal.AssetRegistryHelpers.\
                        get_blueprint_assets(unreal.ARFilter(
                            package_paths=[latest_version_folder]))

                    for bp_asset_data in blueprints_to_copy:
                        bp_name_to_copy = unreal.Paths.get_clean_filename(bp_asset_data.package_name)
                        unreal.EditorAssetLibrary.duplicate_asset(
                            str(bp_asset_data.package_name),
                            unreal.Paths.combine([asset_dir, bp_name_to_copy]))

            # UE 5.7+: Create or update Blueprint wrapper for the skeletal mesh
            if is5_7_or_later and newly_imported_SKM:
                bp_name = get_blueprint_name(asset, version)
                bp_path = f"{asset_dir}/{bp_name}"

                # Check if BP exists and is valid
                bp_exists = unreal.EditorAssetLibrary.does_asset_exist(bp_path)
                bp_needs_recreation = False

                if bp_exists:
                    # Validate the existing BP has the AssetSkeletalMesh component
                    bp_asset = unreal.EditorAssetLibrary.load_asset(bp_path)
                    if not bp_asset or not validate_blueprint_has_component(bp_asset):
                        print(f"[BP Wrapper] Existing BP at {bp_path} is invalid. Recreating from boilerplate.")
                        bp_needs_recreation = True

                if not bp_exists or bp_needs_recreation:
                    if bp_needs_recreation:
                        unreal.EditorAssetLibrary.delete_asset(bp_path)
                    # Copy from boilerplate
                    print(f"[BP Wrapper] Creating BP from boilerplate: {bp_path}")
                    unreal.EditorAssetLibrary.duplicate_asset(
                        BOILERPLATE_BP_PATH,
                        bp_path
                    )

                # Load BP and set the skeletal mesh
                bp_asset = unreal.EditorAssetLibrary.load_asset(bp_path)
                if bp_asset:
                    set_skeletal_mesh_on_blueprint(bp_asset, newly_imported_SKM)
                    # Force this off — the boilerplate has it disabled but it
                    # sometimes gets reset during duplication/import
                    bp_asset.set_editor_property(
                        'run_construction_script_in_sequencer', False)
                    unreal.EditorAssetLibrary.save_asset(bp_path)

            # Create Asset Container
            if not unreal.EditorAssetLibrary.does_asset_exist(
                    asset_dir + '/' + container_name):
                unreal_pipeline.create_container(
                    container=container_name, path=asset_dir)
        else:
            # Exit without doing anything as if the skeletal mesh already has been
            # imported we don't want to do anything to it, and especially we don't
            # want to resave it as that tries to check it out on perforce leading
            # to people checking things out that really don't need to be checked
            # out which in turns lead to people clicking _make writable_ and that
            # leads to desync and the necessity of reconciling offline work which
            # is slow and people forget to do
            print(f'[Skelmesh Checkout Prevention]: Skipping loading {asset_dir} as it is already loaded.')
            return unreal.EditorAssetLibrary.list_assets(
                asset_dir, recursive=True, include_folder=True
            )


        data = {
            "schema": "ayon:container-2.0",
            "id": AYON_CONTAINER_ID,
            "asset": asset,
            "namespace": asset_dir,
            "container_name": container_name,
            "asset_name": asset_name,
            "loader": str(self.__class__.__name__),
            "representation": context["representation"]["_id"],
            "parent": context["representation"]["parent"],
            "family": context["representation"]["context"]["family"]
        }
        unreal_pipeline.imprint(
            f"{asset_dir}/{container_name}", data)

        asset_content = unreal.EditorAssetLibrary.list_assets(
            asset_dir, recursive=True, include_folder=True
        )

        for a in asset_content:
            unreal.EditorAssetLibrary.save_asset(a)

        return asset_content

    def update(self, container, representation):
        # Version check for 5.7+ BP wrapping
        ue_version = unreal.SystemLibrary.get_engine_version().split('.')
        ue_major = int(ue_version[0])
        ue_minor = int(ue_version[1])
        is5_7_or_later = ue_major == 5 and ue_minor >= 7

        # Check if the target version had nanite enabled before we update
        existing_has_nanite_enabled = False
        last_version_skm = unreal.load_asset(container["namespace"] + '/' + container["asset_name"])

        if last_version_skm:
            nanite_settings = last_version_skm.get_editor_property("nanite_settings")
            existing_has_nanite_enabled = nanite_settings.enabled

        name = container["asset_name"]
        source_path = get_representation_path(representation)
        destination_path = container["namespace"]

        task = unreal.AssetImportTask()

        task.set_editor_property('filename', source_path)
        task.set_editor_property('destination_path', destination_path)
        task.set_editor_property('destination_name', name)
        task.set_editor_property('replace_existing', True)
        task.set_editor_property('automated', True)
        task.set_editor_property('save', True)

        # set import options here
        options = unreal.FbxImportUI()
        options.set_editor_property('import_as_skeletal', True)
        options.set_editor_property('import_animations', False)
        options.set_editor_property('import_mesh', True)
        options.set_editor_property('import_materials', False)
        options.set_editor_property('import_textures', False)
        options.set_editor_property('skeleton', None)
        options.set_editor_property('create_physics_asset', False)

        options.skeletal_mesh_import_data.set_editor_property(
            'import_meshes_in_bone_hierarchy',
            True)

        options.set_editor_property('mesh_type_to_import',
                                    unreal.FBXImportType.FBXIT_SKELETAL_MESH)

        options.skeletal_mesh_import_data.set_editor_property(
            'import_content_type',
            unreal.FBXImportContentType.FBXICT_ALL
        )
        # set to import normals, otherwise Unreal will compute them
        # and it will take a long time, depending on the size of the mesh
        options.skeletal_mesh_import_data.set_editor_property(
            'normal_import_method',
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        )

        task.options = options
        # do import fbx and replace existing data
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])  # noqa: E501

        container_path = "{}/{}".format(container["namespace"],
                                        container["objectName"])

        # Load the asset we just imported
        newly_imported_SKM = unreal.load_asset(container["namespace"] + '/' + container["asset_name"])

        if newly_imported_SKM:
            # We can't just set the editor property, we have to access
            # via Nanite Settings object then set it back, weird
            nanite_settings = newly_imported_SKM.get_editor_property("nanite_settings")
            nanite_settings.enabled = existing_has_nanite_enabled
            newly_imported_SKM.set_editor_property("nanite_settings", nanite_settings)

            # Save the asset directly, we are directly after the asset
            # I am considering not doing this save since we're not
            # directly saving the skeletal mesh either, inconsistent
            unreal.EditorAssetLibrary.save_loaded_asset(newly_imported_SKM)

            # Mirror-flip socket bones (`_sock_` prefix); reimport resets the
            # ref pose from the FBX, so this has to run on update too
            _flip_socket_bones_on_mesh(
                container["namespace"] + '/' + container["asset_name"])

            # UE 5.7+: Update Blueprint wrapper's SkeletalMeshComponent
            if is5_7_or_later:
                asset_name = container.get("asset", "")
                version_match = re.search(r'_v(\d+)$', destination_path)
                if version_match:
                    ver = int(version_match.group(1))
                    bp_name = get_blueprint_name(asset_name, ver)
                    bp_path = f"{destination_path}/{bp_name}"

                    if unreal.EditorAssetLibrary.does_asset_exist(bp_path):
                        bp_asset = unreal.EditorAssetLibrary.load_asset(bp_path)
                        if bp_asset:
                            set_skeletal_mesh_on_blueprint(bp_asset, newly_imported_SKM)
                            bp_asset.set_editor_property(
                                'run_construction_script_in_sequencer', False)
                            unreal.EditorAssetLibrary.save_asset(bp_path)

        # update metadata
        unreal_pipeline.imprint(
            container_path,
            {
                "representation": str(representation["_id"]),
                "parent": str(representation["parent"])
            })

        asset_content = unreal.EditorAssetLibrary.list_assets(
            destination_path, recursive=True, include_folder=True
        )

        for a in asset_content:
            unreal.EditorAssetLibrary.save_asset(a)

    def remove(self, container):
        path = container["namespace"]
        parent_path = os.path.dirname(path)

        unreal.EditorAssetLibrary.delete_directory(path)

        asset_content = unreal.EditorAssetLibrary.list_assets(
            parent_path, recursive=False
        )

        if len(asset_content) == 0:
            unreal.EditorAssetLibrary.delete_directory(parent_path)
