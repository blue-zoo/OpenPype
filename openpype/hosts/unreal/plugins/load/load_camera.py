# -*- coding: utf-8 -*-
"""Load camera from FBX."""
from pathlib import Path
import importlib
import unreal
from unreal import (
    EditorAssetLibrary,
    LevelEditorSubsystem,
    EditorLevelLibrary,
    MovieSceneSequenceExtensions,
    EditorLevelUtils,
    LevelSequenceEditorBlueprintLibrary as LevelSequenceLib,
)
from openpype.client import get_asset_by_name
from openpype.pipeline import (
    AYON_CONTAINER_ID,
    get_current_project_name,
)
from openpype.hosts.unreal.api import plugin
from openpype.hosts.unreal.api import pipeline
importlib.reload(pipeline)
from openpype.hosts.unreal.api.pipeline import (
    generate_sequence,
    set_sequence_hierarchy,
    create_container,
    imprint,
)


class CameraLoader(plugin.Loader):
    """Load Unreal StaticMesh from FBX"""

    families = ["camera"]
    label = "Load Camera"
    representations = ["fbx"]
    icon = "cube"
    color = "orange"

    def _import_camera(
        self, world, sequence, bindings, import_fbx_settings, import_filename
    ):
        ue_version = unreal.SystemLibrary.get_engine_version().split('.')
        ue_major = int(ue_version[0])
        ue_minor = int(ue_version[1])

        if ue_major == 4 and ue_minor <= 26:
            unreal.SequencerTools.import_fbx(
                world,
                sequence,
                bindings,
                import_fbx_settings,
                import_filename
            )
        elif (ue_major == 4 and ue_minor >= 27) or ue_major == 5:

            bob = unreal.SequencerTools.import_level_sequence_fbx(
                world,
                sequence,
                bindings,
                import_fbx_settings,
                import_filename
            )

            tracks = sequence.find_master_tracks_by_exact_type(unreal.MovieSceneCameraCutTrack)
            sections = tracks[0].get_sections()


            for section in sections:
                return section.get_camera_binding_id()


        else:
            raise NotImplementedError(
                f"Unreal version {ue_major} not supported")

    def load(self, context, name, namespace, data):
        """
        Load and containerise representation into Content Browser.

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
            data (dict): Those would be data to be imprinted. This is not used
                         now, data are imprinted by `containerise()`.

        Returns:
            list(str): list of container content
        """

        # Create directory for asset and Ayon container
        hierarchy = context.get('asset').get('data').get('parents')
        root = "/Game/Ayon"
        hierarchy_dir = root
        hierarchy_dir_list = []
        for h in hierarchy:
            hierarchy_dir = f"{hierarchy_dir}/{h}"
            hierarchy_dir_list.append(hierarchy_dir)
        asset = context.get('asset').get('name')
        suffix = "_CON"
        asset_name = f"{asset}_{name}" if asset else f"{name}"

        tools = unreal.AssetToolsHelpers().get_asset_tools()
        ar = unreal.AssetRegistryHelpers.get_asset_registry()

        # Find the existing sequences
        asset_content = EditorAssetLibrary.list_assets(
            f"{hierarchy_dir}/{asset}", recursive=False, include_folder=True
        )


        clipIn = context.get('asset').get("data").get("clipIn")
        clipOut = context.get('asset').get("data").get("clipOut")

        container_name =context.get('subset').get("name")+suffix

        # Create map for the shot, and create hierarchy of map. If the maps
        # already exist, we will use them.
        h_dir = hierarchy_dir_list[0]
        h_asset = hierarchy[0]

        episodeLevelFolder = '{p}/{l}'.format(p=hierarchy_dir_list[1],l=hierarchy[1] )


        episodeLevelContents = EditorAssetLibrary.list_assets(
            episodeLevelFolder, recursive=True, include_folder=False)
        episodeLevels = []
        for s in episodeLevelContents:
            _a = ar.get_asset_by_object_path(s)
            if _a.get_class().get_name() == "LevelSequence":

                episodeLevelPath = '{p}/{n}_map.{n}_map'.format(
                    p=str(_a.package_path),
                    n =str(_a.asset_name)
                )
                if EditorAssetLibrary.does_asset_exist(episodeLevelPath):
                    episodeLevel = ar.get_asset_by_object_path(episodeLevelPath)
                    episodeLevels.append({
                        'level':episodeLevel.get_asset(),
                        'sequence':_a.get_asset()

                    })

        #return
        shotFolder = '{p}/{l}'.format(p=hierarchy_dir_list[1],l=hierarchy[1] )

        # Find the layout levels for the shot
        shotLevels = []
        shotLevelFolder = '{p}/{l}'.format(p=hierarchy_dir_list[-1],l=asset )
        shot_content = EditorAssetLibrary.list_assets(
            shotLevelFolder, recursive=True, include_folder=False)

        for s in shot_content:
            _a = ar.get_asset_by_object_path(s)
            if _a.get_class().get_name() == "LevelSequence":

                # Since the camera is not associated with a layout, we add it
                # to all layouts
                for a_in_package_path in EditorAssetLibrary.list_assets(
                        _a.package_path, recursive=False, include_folder=False):
                    a_in_package = ar.get_asset_by_object_path(a_in_package_path)
                    if a_in_package.get_class().get_name() == 'World':
                        shotLevelPath = f'{a_in_package.package_name}.{a_in_package.asset_name}'

                if EditorAssetLibrary.does_asset_exist(shotLevelPath):
                    shotLevel = ar.get_asset_by_object_path(shotLevelPath)
                    shotLevels.append({
                        'level':shotLevel.get_asset(),
                        'sequence':_a.get_asset(),
                        'shotLevelFolder':shotLevel.package_path
                    })


        sequenceCameraBindingId = None
        for shot in shotLevels:
            frame_ranges = []
            sequences = []
            seq = shot['sequence']
            level = shot['level']
            shotLevelFolder = shot['shotLevelFolder']

            # Look through the shots folder to find a container, raise error if present
            asset_children = EditorAssetLibrary.list_assets(
                shotLevelFolder, recursive=False, include_folder=False)
            ar = unreal.AssetRegistryHelpers.get_asset_registry()
            container = None
            skip = False
            for a in asset_children:
                obj = ar.get_asset_by_object_path(a)
                _a = obj.get_asset()
                if _a.get_name() == container_name and _a.get_class().get_name() == "AyonAssetContainer":
                    container = _a
                    self.log.warning(f"Camera already imported in {shot['level']}, use updater to manage")
                    skip = True
                    break
            if skip:
                continue

            path = self.filepath_from_context(context)
            settings = unreal.MovieSceneUserImportFBXSettings()
            settings.set_editor_property('reduce_keys', False)

            preImportObjects= unreal.SequencerTools().get_bound_objects(level, seq,
                                                                seq.get_bindings(),
                                                                seq.get_playback_range())

            preImportCameras = [obj for bindings in preImportObjects for obj in bindings.bound_objects if obj.get_class().get_name() == "CineCameraActor"]

            bindingId = self._import_camera(
                level,
                seq,
                seq.get_bindings(),
                settings,
                path)
            _id = bindingId.get_editor_property('guid')
            binding = unreal.MovieSceneSequenceExtensions.find_binding_by_id(seq, _id )

            postImportObjects = unreal.SequencerTools().get_bound_objects(level, seq,
                                                                seq.get_bindings(),
                                                                seq.get_playback_range())

            postImportCameras = [obj for bindings in postImportObjects for obj in bindings.bound_objects if obj.get_class().get_name() == "CineCameraActor"]

            newCameras = [camera for camera in postImportCameras if camera not in preImportCameras]
            for camera in newCameras:
                camera.tags = camera.tags + [context["representation"]["_id"]]

            bindingName = binding.get_name()


            asset_children = EditorAssetLibrary.list_assets(
                shotLevelFolder, recursive=False, include_folder=False)
            ar = unreal.AssetRegistryHelpers.get_asset_registry()
            container = None



            # Get all the asset containers
            for a in asset_children:
                obj = ar.get_asset_by_object_path(a)
                _a = obj.get_asset()
                if _a.get_name() == container_name and _a.get_class().get_name() == "AyonAssetContainer":
                    container = _a


            # Create Asset Container
            if not container:

                # Create Asset Container
                create_container(
                    container=container_name, path=shotLevelFolder)

            data = {
                "schema": "ayon:container-2.0",
                "id": AYON_CONTAINER_ID,
                "asset": asset,
                "namespace": shotLevelFolder,
                "container_name": container_name,
                "asset_name": bindingName,
                "loader": str(self.__class__.__name__),
                "representation": context["representation"]["_id"],
                "parent": context["representation"]["parent"],
                "family": context["representation"]["context"]["family"]
            }
            imprint(f"{shotLevelFolder}/{container_name}", data)



        for episodeLevel in episodeLevels:
            sequence = episodeLevel['sequence']

            track = sequence.find_master_tracks_by_exact_type(unreal.MovieSceneCameraCutTrack)[0]
            sections = track.get_sections()
            section = track.add_section()
            section.set_range(clipIn,clipOut+1)
            section.set_end_frame(clipOut+1)

        EditorLevelLibrary.save_all_dirty_levels()

        return asset_content

    def update(self, container, representation):
        ar = unreal.AssetRegistryHelpers.get_asset_registry()

        curr_level_sequence = LevelSequenceLib.get_current_level_sequence()
        curr_time = LevelSequenceLib.get_current_time()
        is_cam_lock = LevelSequenceLib.is_camera_cut_locked_to_viewport()

        editor_subsystem = unreal.UnrealEditorSubsystem()
        vp_loc, vp_rot = editor_subsystem.get_level_viewport_camera_info()

        asset_dir = container.get('namespace')
        previousRepresentationId = container.get('representation')



        EditorLevelLibrary.save_current_level()

        _filter = unreal.ARFilter(
            class_names=["LevelSequence"],
            package_paths=[asset_dir],
            recursive_paths=False)
        sequences = ar.get_assets(_filter)

        _filter = unreal.ARFilter(
            class_names=["World"],
            package_paths=[asset_dir],
            recursive_paths=True)
        maps = ar.get_assets(_filter)


        for _seq in sequences:

            seq = _seq.get_asset()
            for _level in maps:
                level = _level.get_asset()

                # get the old representation camera
                preImportObjects= unreal.SequencerTools().get_bound_objects(level, seq,
                                                                    seq.get_bindings(),
                                                                    seq.get_playback_range())

                preImportCameras = [obj for bindings in preImportObjects for obj in bindings.bound_objects if obj.get_class().get_name() == "CineCameraActor"]

                # Delete the old camera
                for camera in preImportCameras:

                    for bindings in preImportObjects:
                        if not camera in bindings.bound_objects:
                            continue
                        else:
                            tracks= bindings.binding_proxy.get_tracks()
                            for track in tracks:
                                bindings.binding_proxy.remove_track(track)
                            bindings.binding_proxy.remove()

                        if previousRepresentationId in camera.tags:
                            unreal.EditorLevelLibrary.destroy_actor(camera)

                ## Remove Camera Cut
                track = seq.find_master_tracks_by_exact_type(unreal.MovieSceneCameraCutTrack)[0]
                #binding.add_track(track)
                sections = track.get_sections()
                for section in sections:
                    track.remove_section(section)
                    #section.set_camera_binding_id( bindingId)


                settings = unreal.MovieSceneUserImportFBXSettings()
                settings.set_editor_property('reduce_keys', False)
                bindingId = self._import_camera(
                    level,
                    seq,
                    seq.get_bindings(),
                    settings,
                    str(representation["data"]["path"])
                )

                postImportObjects = unreal.SequencerTools().get_bound_objects(level, seq,
                                                                    seq.get_bindings(),
                                                                    seq.get_playback_range())

                postImportCameras = [obj for bindings in postImportObjects for obj in bindings.bound_objects if obj.get_class().get_name() == "CineCameraActor"]

                newCameras = [camera for camera in postImportCameras if camera not in preImportCameras]
                for camera in newCameras:
                    camera.tags = camera.tags + [str(representation["_id"])]


                _id = bindingId.get_editor_property('guid')
                binding = unreal.MovieSceneSequenceExtensions.find_binding_by_id(seq, _id )
                #bindingName = binding.get_name()


                track = seq.find_master_tracks_by_exact_type(unreal.MovieSceneCameraCutTrack)[0]
                #binding.add_track(track)
                sections = track.get_sections()
                for section in sections:
                    #section.set_camera_binding_id( bindingId)
                    #section.set_range(clipIn,clipOut)
                    pass



        data = {
            "representation": str(representation["_id"]),
            "parent": str(representation["parent"])
        }
        imprint(f"{asset_dir}/{container.get('container_name')}", data)
        return


    def remove(self, container):
        asset_dir = container.get('namespace')
        path = Path(asset_dir)

        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        _filter = unreal.ARFilter(
            class_names=["LevelSequence"],
            package_paths=[asset_dir],
            recursive_paths=False)
        sequences = ar.get_assets(_filter)

        if not sequences:
            raise Exception("Could not find sequence.")

        world = ar.get_asset_by_object_path(
            EditorLevelLibrary.get_editor_world().get_path_name())

        _filter = unreal.ARFilter(
            class_names=["World"],
            package_paths=[asset_dir],
            recursive_paths=True)
        maps = ar.get_assets(_filter)

        # There should be only one map in the list
        if not maps:
            raise Exception("Could not find map.")

        map = maps[0]

        EditorLevelLibrary.save_all_dirty_levels()
        EditorLevelLibrary.load_level(map.get_asset().get_path_name())

        # Remove the camera from the level.
        actors = EditorLevelLibrary.get_all_level_actors()

        for a in actors:
            if a.__class__ == unreal.CineCameraActor:
                EditorLevelLibrary.destroy_actor(a)

        EditorLevelLibrary.save_all_dirty_levels()
        EditorLevelLibrary.load_level(world.get_asset().get_path_name())

        # There should be only one sequence in the path.
        sequence_name = sequences[0].asset_name

        # Remove the Level Sequence from the parent.
        # We need to traverse the hierarchy from the master sequence to find
        # the level sequence.
        root = "/Game/Ayon"
        namespace = container.get('namespace').replace(f"{root}/", "")
        ms_asset = namespace.split('/')[0]
        _filter = unreal.ARFilter(
            class_names=["LevelSequence"],
            package_paths=[f"{root}/{ms_asset}"],
            recursive_paths=False)
        sequences = ar.get_assets(_filter)
        master_sequence = sequences[0].get_asset()
        _filter = unreal.ARFilter(
            class_names=["World"],
            package_paths=[f"{root}/{ms_asset}"],
            recursive_paths=False)
        levels = ar.get_assets(_filter)
        master_level = levels[0].get_full_name()

        sequences = [master_sequence]

        parent = None
        for s in sequences:
            tracks = s.get_master_tracks()
            subscene_track = None
            visibility_track = None
            for t in tracks:
                if t.get_class() == unreal.MovieSceneSubTrack.static_class():
                    subscene_track = t
                if (t.get_class() ==
                        unreal.MovieSceneLevelVisibilityTrack.static_class()):
                    visibility_track = t
            if subscene_track:
                sections = subscene_track.get_sections()
                for ss in sections:
                    if ss.get_sequence().get_name() == sequence_name:
                        parent = s
                        subscene_track.remove_section(ss)
                        break
                    sequences.append(ss.get_sequence())
                # Update subscenes indexes.
                for i, ss in enumerate(sections):
                    ss.set_row_index(i)

            if visibility_track:
                sections = visibility_track.get_sections()
                for ss in sections:
                    if (unreal.Name(f"{container.get('asset')}_map_camera")
                            in ss.get_level_names()):
                        visibility_track.remove_section(ss)
                # Update visibility sections indexes.
                i = -1
                prev_name = []
                for ss in sections:
                    if prev_name != ss.get_level_names():
                        i += 1
                    ss.set_row_index(i)
                    prev_name = ss.get_level_names()
            if parent:
                break

        assert parent, "Could not find the parent sequence"

        # Create a temporary level to delete the layout level.
        EditorLevelLibrary.save_all_dirty_levels()
        EditorAssetLibrary.make_directory(f"{root}/tmp")
        tmp_level = f"{root}/tmp/temp_map"
        if not EditorAssetLibrary.does_asset_exist(f"{tmp_level}.temp_map"):
            EditorLevelLibrary.new_level(tmp_level)
        else:
            EditorLevelLibrary.load_level(tmp_level)

        # Delete the layout directory.
        EditorAssetLibrary.delete_directory(asset_dir)

        EditorLevelLibrary.load_level(master_level)
        EditorAssetLibrary.delete_directory(f"{root}/tmp")

        # Check if there isn't any more assets in the parent folder, and
        # delete it if not.
        asset_content = EditorAssetLibrary.list_assets(
            path.parent.as_posix(), recursive=False, include_folder=True
        )

        if len(asset_content) == 0:
            EditorAssetLibrary.delete_directory(path.parent.as_posix())
