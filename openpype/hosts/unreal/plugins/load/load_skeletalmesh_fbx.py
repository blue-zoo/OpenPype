# -*- coding: utf-8 -*-
"""Load Skeletal Meshes form FBX."""
import os

from openpype.pipeline import (
    get_representation_path,
    AYON_CONTAINER_ID
)
from openpype.hosts.unreal.api import plugin
from openpype.hosts.unreal.api import pipeline as unreal_pipeline
import unreal  # noqa


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
                blueprints_to_copy = unreal.AssetRegistryHelpers.\
                    get_blueprint_assets(unreal.ARFilter(
                        package_paths=[latest_version_folder]))

                for bp_asset_data in blueprints_to_copy:
                    bp_name = unreal.Paths.get_clean_filename(bp_asset_data.package_name)
                    unreal.EditorAssetLibrary.duplicate_asset(
                        str(bp_asset_data.package_name),
                        unreal.Paths.combine([asset_dir, bp_name]))

            # Create Asset Container
            if not unreal.EditorAssetLibrary.does_asset_exist(
                    asset_dir + '/' + container_name):
                unreal_pipeline.create_container(
                    container=container_name, path=asset_dir)


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
