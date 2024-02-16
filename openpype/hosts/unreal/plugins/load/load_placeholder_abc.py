# -*- coding: utf-8 -*-
"""Load Static meshes form FBX."""
import os


from openpype.pipeline import (
    get_representation_path,
    AYON_CONTAINER_ID
)
from openpype.hosts.unreal.api import plugin
from openpype.hosts.unreal.api import pipeline as unreal_pipeline
import unreal  # noqa
from unreal import EditorAssetLibrary


class PlaceHolderAbcLoader(plugin.Loader):
    """Load Level from Placeholder"""

    families = ["placeholder"]
    label = "Import FBX Static Mesh"
    representations = ["abc"]
    icon = "cube"
    color = "orange"

    @staticmethod
    def get_task(filename, asset_dir, asset_name, replace):
        task = unreal.AssetImportTask()
        options = unreal.FbxImportUI()
        import_data = unreal.FbxStaticMeshImportData()

        task.set_editor_property('filename', filename)
        task.set_editor_property('destination_path', asset_dir)
        task.set_editor_property('destination_name', asset_name)
        task.set_editor_property('replace_existing', replace)
        task.set_editor_property('automated', True)
        task.set_editor_property('save', True)

        # set import options here
        options.set_editor_property(
            'automated_import_should_detect_type', False)
        options.set_editor_property('import_animations', False)

        import_data.set_editor_property('combine_meshes', True)
        import_data.set_editor_property('remove_degenerates', False)

        options.static_mesh_import_data = import_data
        task.options = options

        return task

    def load(self, context, name, namespace, options):
        """Load and containerise representation into Content Browser.

        This is two step process. First, import FBX to temporary path and
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
        ar = unreal.AssetRegistryHelpers.get_asset_registry()

        if options and options.get("asset_dir"):
            root = options["asset_dir"]
        hier = context.get("representation",{}).get("context").get("hierarchy",None)
        if hier:
            root +="/"+hier

        asset = context.get('asset').get('name')
        subset = context.get('representation').get('context').get('subset')
        variant = subset.split("placeholder")[-1]
        suffix = "_CON"
        if asset:
            asset_name = "{}_{}".format(asset, name)
        else:
            asset_name = "{}".format(name)
        asset_dir = f"{root}/{asset}/{variant}"
        self.log.error('Looking For Blueprint in {a}'.format(a=asset_dir))
        existing_assets = EditorAssetLibrary.list_assets(
            asset_dir, recursive=False, include_folder=False
        )
        # Get all the asset containers
        blueprint = []
        for a in existing_assets:
            obj = ar.get_asset_by_object_path(a)
            _a = obj.get_asset()
            if _a.get_class().get_name() == "Blueprint":
                self.log.error('found blueprint {a}'.format(a=a))

                blueprint.append(a)
                break
        existing_assets = unreal.EditorAssetLibrary.list_assets(
            asset_dir, recursive=True, include_folder=True
        )
        return blueprint


    def update(self, container, representation):
        name = container["asset_name"]
        source_path = get_representation_path(representation)
        destination_path = container["namespace"]

        task = self.get_task(source_path, destination_path, name, True)

        # do import fbx and replace existing data
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

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
