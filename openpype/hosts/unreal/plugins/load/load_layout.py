# -*- coding: utf-8 -*-
"""Loader for layouts."""
import json
import collections
from pathlib import Path
import inspect,os
import importlib

import unreal
from unreal import (
    EditorAssetLibrary,
    EditorLevelLibrary,
    EditorLevelUtils,
    AssetToolsHelpers,
    FBXImportType,
    MovieSceneLevelVisibilityTrack,
    MovieSceneSubTrack,
    LevelSequenceEditorBlueprintLibrary as LevelSequenceLib,
)

from openpype.client import get_asset_by_name, get_representations
from openpype.pipeline import (
    discover_loader_plugins,
    loaders_from_representation,
    load_container,
    get_representation_path,
    AYON_CONTAINER_ID,
    get_current_project_name,
)
from openpype.pipeline.context_tools import get_current_project_asset
from openpype.settings import get_current_project_settings
from openpype.hosts.unreal.api import plugin

from openpype.hosts.unreal.api import pipeline
importlib.reload(pipeline)
from openpype.hosts.unreal.api.pipeline import (
    generate_sequence,
    set_sequence_hierarchy,
    create_container,
    imprint,
    ls,
)

# A global switch to make more obvious and easily reversible the
# decision to replace AYONs default level hierarchy, which forces
# the episode level to be loaded every time a layout for a shot is
# loaded, as that becomes painfully slow and potentially will
# be impossible as soon as the production hits its full scale
replacing_AYONs_level_hierarchy = True


class LayoutLoader(plugin.Loader):
    """Load Layout from a JSON file"""

    families = ["layout","layout_multi"]
    representations = ["json"]

    label = "Load Layout"
    icon = "code-fork"
    color = "orange"
    ASSET_ROOT = "/Game/Ayon"

    def _get_asset_containers(self, path):
        ar = unreal.AssetRegistryHelpers.get_asset_registry()

        asset_content = EditorAssetLibrary.list_assets(
            path, recursive=True)

        asset_containers = []

        # Get all the asset containers
        for a in asset_content:
            obj = ar.get_asset_by_object_path(a)
            if obj.get_asset().get_class().get_name() == 'AyonAssetContainer':
                asset_containers.append(obj)

        return asset_containers

    @staticmethod
    def _get_fbx_loader(loaders, family):
        name = ""
        if family == 'rig':
            name = "SkeletalMeshFBXLoader"
        elif family == 'model':
            name = "StaticMeshFBXLoader"
        elif family == 'camera':
            name = "CameraLoader"
        elif family == 'staticMesh':
            name = "StaticMeshFBXLoader"

        if name == "":
            return None

        for loader in loaders:
            if loader.__name__ == name:
                return loader

        return None

    @staticmethod
    def _get_abc_loader(loaders, family):
        name = ""

        if family == 'rig':
            name = "SkeletalMeshAlembicLoader"
        elif family == 'model':
            name = "StaticMeshAlembicLoader"
        elif family == 'placeholder':
            name = "PlaceHolderAbcLoader"
        else:
            return None
        for loader in loaders:
            if loader.__name__ == name:
                return loader

        return None

    def _transform_from_basis(self, transform, basis, swap_axis = False):
        """Transform a transform from a basis to a new basis."""
        # Get the basis matrix
        # change matrix exported from maya as xyz to
        swap_axis=False
        if swap_axis:
            s = 2
            t = 1
        else:
            s = 1
            t = 2



        basis[0] = [basis[0][0],basis[0][s],basis[0][t]]
        basis[1] = [basis[1][0],basis[1][s],basis[1][t]]
        basis[2] = [basis[2][0],basis[2][s],basis[2][t]]
        basis[3] = [basis[3][0],basis[3][s],basis[3][t]]

        transform[0] = [transform[0][0],transform[0][s],transform[0][t]]
        transform[1] = [transform[1][0],transform[1][s],transform[1][t]]
        transform[2] = [transform[2][0],transform[2][s],transform[2][t]]
        transform[3] = [transform[3][0],transform[3][s],transform[3][t]]

        basis_matrix = unreal.Matrix(
            basis[0],
            basis[1],
            basis[2],
            basis[3]
        )
        transform_matrix = unreal.Matrix(
            transform[0],
            transform[1],
            transform[2],
            transform[3]
        )

        MAYA_TO_UNREAL = [[],[],[],[]]
        MAYA_TO_UNREAL[0] = [ 1, 0, 0, 0]
        MAYA_TO_UNREAL[1] = [ 0, 0,-1, 0]
        MAYA_TO_UNREAL[2] = [ 0, 1, 0, 0]
        MAYA_TO_UNREAL[3] = [ 0, 0, 0, 1]

        MAYA_TO_UNREAL_MATRIX = unreal.Matrix(
        MAYA_TO_UNREAL[0],
        MAYA_TO_UNREAL[1],
        MAYA_TO_UNREAL[2],
        MAYA_TO_UNREAL[3] )

        bob = unreal.Rotator(0,270,0)
        t = bob.transform()
        MAYA_TO_UNREAL_X_MATRIX = t.to_matrix()
        MAYA_TO_UNREAL__X = [[],[],[],[]]
        MAYA_TO_UNREAL__X[0] = [ 0, 0, -1, 0]
        MAYA_TO_UNREAL__X[1] = [ 0, 1, 0, 0]
        MAYA_TO_UNREAL__X[2] = [ 1, 0, 0, 0]
        MAYA_TO_UNREAL__X[3] = [ 0, 0, 0, 0]

        MAYA_TO_UNREAL_MATRIX_XXX = unreal.Matrix(
        MAYA_TO_UNREAL__X[0],
        MAYA_TO_UNREAL__X[1],
        MAYA_TO_UNREAL__X[2],
        MAYA_TO_UNREAL__X[3] )

        new_transform = (
            MAYA_TO_UNREAL_MATRIX * basis_matrix.get_inverse() *  transform_matrix * basis_matrix )

        return new_transform.transform()

    def _process_family(
        self, assets, class_name, transform, basis, sequence, inst_name=None
    ):
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        actors = []
        bindings = []
        skeletal_mesh = None
        for asset in assets:
            obj = ar.get_asset_by_object_path(asset).get_asset()
            if obj.get_class().get_name() == class_name:

                t = self._transform_from_basis(transform, basis,swap_axis=True)
                actor = None
                for _a in EditorLevelLibrary.get_all_level_actors():
                    if _a.get_actor_label() == inst_name:
                        actor = _a
                        actor.set_actor_location(t.translation,False,False)
                        break
                if not actor:
                    actor = EditorLevelLibrary.spawn_actor_from_object(
                        obj, t.translation
                    )
                    actor.set_actor_label(inst_name)
                elif actor.static_class().get_name() == 'SkeletalMeshActor':
                    # Ensure the actor is using the skeletal mesh specified
                    # by the provided `asset`, as a rig swap in Maya
                    # only changes the representation and nothing else
                    # so we can't just rely on the name
                    skeletal_mesh_component = actor.skeletal_mesh_component
                    actor_skeletal_mesh = None
                    if skeletal_mesh_component.skeletal_mesh_asset is not None:
                        actor_skeletal_mesh = skeletal_mesh_component\
                            .skeletal_mesh_asset.get_full_name().split(' ')[1]
                    if actor_skeletal_mesh != asset:
                        skeletal_mesh_component.set_skeletal_mesh(
                            unreal.EditorAssetLibrary.load_asset(asset))


                actor.set_actor_rotation(t.rotation.rotator(), False)
                actor.set_actor_scale3d(t.scale3d)



                if class_name == 'SkeletalMesh':
                    skm_comp = actor.get_editor_property(
                        'skeletal_mesh_component')
                    skm_comp.set_bounds_scale(10.0)
                    skeletal_mesh = actor
                actors.append(actor)

                if sequence:
                    binding = None
                    for p in sequence.get_possessables():
                        if p.get_name() == actor.get_name():
                            # NOTE: this does nothing, as the binding name is never that of the actor?
                            binding = p
                            break

                    if not binding:
                        binding = sequence.add_possessable(actor)

                    bindings.append(binding)

        if skeletal_mesh:
            # Check if there are any blueprints in the Asset version folder
            skeleton_path = unreal.Paths.get_path(asset)
            blueprints_in_skeleton_path = unreal.AssetRegistryHelpers.\
                get_blueprint_assets(unreal.ARFilter(
                    package_paths=[skeleton_path]))

            # NOTE: worth considering whether we should do anything if there's
            # not blueprints in the path, as if that's the case, but there's
            # some attached actors, there's an argument to be made to
            # unattach and destroy those actors, as they are _likely_ coming
            # from blueprints that have been moved outside of the correct path,
            # but there is a chance that those are legitimate actors that
            # have been attached to the skeletal mesh.
            #
            # If there are blueprints we want to attach them to the skeletal mesh
            for bp_asset_data in blueprints_in_skeleton_path:
                # Check if a blueprint of this type is already attached as
                # rebuilding the layout doesn't remove existing assets and
                # readd them, but it uses the existing instances
                bp_asset_data_split_path = str(bp_asset_data.package_name).split('/')
                found_actor = None
                for child in skeletal_mesh.get_attached_actors():
                    child_path = child.get_class().get_class_path_name().package_name
                    child_split_path = str(child_path).split('/')

                    if len(child_split_path) != len(bp_asset_data_split_path):
                        continue

                    # Check if this is the same blueprint, but from different
                    # versions of the asset, where only the second to last
                    # token in the path will be different
                    differences = [(a != b) for a,b in zip(bp_asset_data_split_path,
                                                           child_split_path)]
                    if sum(differences) == 1 and differences[-2]:
                        # Delete the existing blueprint, as we should replace it with
                        # the one from the new version of the asset
                        if sequence:
                            binding = sequence.find_binding_by_name(
                                child.get_actor_label())
                            if binding.is_valid():
                                binding.remove()

                        self.log.warning(
                            f'{child.get_actor_label()} is from an older version.'
                             ' of the asset, so it is being deleted to be replaced'
                             ' with its new version.')

                        child.detach_from_actor()
                        child.destroy_actor()

                        continue

                    # Otherwise let's just check if this is the same blueprint, in
                    # which case we have found a match (NOTE: this does not support
                    # multiples of the same BP being attached, but that is not to spec)
                    if child_path == bp_asset_data.package_name:
                        found_actor = child

                if found_actor is not None:
                    onLayoutInit_ran = False
                    try:
                        found_actor.call_method('onLayoutInit')
                        onLayoutInit_ran = True
                    except Exception as e:
                        if 'Failed to find function \'onLayoutInit\'' in str(e):
                            # If an attached bp doesn't have the `onLayoutInit`
                            # method defined, it means it has been removed
                            # after the bp has been attached and since it is
                            # now unclear where that bp should be attached,
                            # we remove it from the level
                            if sequence:
                                binding = sequence.find_binding_by_name(
                                    found_actor.get_actor_label())
                                if binding.is_valid():
                                    binding.remove()

                            self.log.warning(
                                f'{found_actor.get_actor_label()} no longer implements '
                                 'the `onLayoutInit` method, so it is removed.')

                            found_actor.detach_from_actor()
                            found_actor.destroy_actor()
                            continue
                        else:
                            raise e

                    if onLayoutInit_ran:
                        # onLayoutInit uses snap to target, but since the sockets
                        # coming from Maya are flipped in X, let's solve that by
                        # flipping here.
                        # NOTE: it would be way better to do this in the rigs,
                        #       but there's a lot of published ones already, so
                        #       we solve it on loading
                        child.add_actor_local_transform(
                            unreal.Transform(scale=[-1,1,1]),
                            False, False)
                        unreal.log_warning('layout loading: flipping BP -1 in X after '
                                           '`onLayoutInit` to account for socket '
                                           'transform on ' + str(child))

                    # Then ensure it's added to the sequence
                    if sequence:
                        bindings.append(sequence.add_possessable(child))

                    actors.append(child)

                    # Carry on without creating a new blueprint instance
                    continue

                # Create actor of the specified blueprint type
                skeleton_bp_actor = EditorLevelLibrary.spawn_actor_from_object(
                    bp_asset_data.get_asset(), unreal.Vector())

                # Attach it to our skeletal mesh, where the socket and the
                # rules don't matter, as we then call the `onLayoutInit`
                # method of the blueprint which we expect to handle the
                # attachment properly
                skeleton_bp_actor.attach_to_actor(skeletal_mesh,
                    socket_name='None',
                    location_rule=unreal.AttachmentRule.SNAP_TO_TARGET,
                    rotation_rule=unreal.AttachmentRule.SNAP_TO_TARGET,
                    scale_rule=unreal.AttachmentRule.SNAP_TO_TARGET)

                onLayoutInit_ran = False
                try:
                    skeleton_bp_actor.call_method('onLayoutInit')
                    onLayoutInit_ran = True
                except Exception as e:
                    if 'Failed to find function \'onLayoutInit\'' in str(e):
                        bp_class_path = bp_asset_data.package_name
                        self.log.warning(f'Blueprint {bp_class_path} does not '
                                          'implement the `onLayoutInit` '
                                          'function, so it is not being attached.')
                        skeleton_bp_actor.detach_from_actor()
                        skeleton_bp_actor.destroy_actor()
                        continue
                    else:
                        raise e

                if onLayoutInit_ran:
                    # onLayoutInit uses snap to target, but since the sockets
                    # coming from Maya are flipped in X, let's solve that by
                    # flipping here.
                    # NOTE: it would be way better to do this in the rigs,
                    #       but there's a lot of published ones already, so
                    #       we solve it on loading
                    skeleton_bp_actor.add_actor_local_transform(
                        unreal.Transform(scale=[-1,1,1]),
                        False, False)
                    unreal.log_warning('layout loading: flipping BP -1 in X after '
                                        '`onLayoutInit` to account for socket '
                                        'transform on ' + str(skeleton_bp_actor))

                # Add blueprint to sequence and store it in actors and bindings,
                # even though they are only needed for importing animation
                # which this blueprint will never have
                actors.append(skeleton_bp_actor)
                if sequence:
                    bindings.append(sequence.add_possessable(skeleton_bp_actor))

        return actors, bindings

    def _import_animation(
        self, asset_dir, path, instance_name, skeleton, actors_dict,
        animation_file, bindings_dict, sequence
    ):
        anim_file = Path(animation_file)
        anim_file_name = anim_file.with_suffix('')

        anim_path = f"{asset_dir}/animations/{anim_file_name}"

        asset_doc = get_current_project_asset()
        # Import animation
        task = unreal.AssetImportTask()
        task.options = unreal.FbxImportUI()

        task.set_editor_property(
            'filename', str(path.with_suffix(f".{animation_file}")))
        task.set_editor_property('destination_path', anim_path)
        task.set_editor_property(
            'destination_name', f"{instance_name}_animation")
        task.set_editor_property('replace_existing', False)
        task.set_editor_property('automated', True)
        task.set_editor_property('save', False)

        # set import options here
        task.options.set_editor_property(
            'automated_import_should_detect_type', False)
        task.options.set_editor_property(
            'original_import_type', FBXImportType.FBXIT_SKELETAL_MESH)
        task.options.set_editor_property(
            'mesh_type_to_import', FBXImportType.FBXIT_ANIMATION)
        task.options.set_editor_property('import_mesh', False)
        task.options.set_editor_property('import_animations', True)
        task.options.set_editor_property('override_full_name', True)
        task.options.set_editor_property('skeleton', skeleton)

        task.options.anim_sequence_import_data.set_editor_property(
            'animation_length',
            unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME
        )
        task.options.anim_sequence_import_data.set_editor_property(
            'import_meshes_in_bone_hierarchy', False)
        task.options.anim_sequence_import_data.set_editor_property(
            'use_default_sample_rate', False)
        task.options.anim_sequence_import_data.set_editor_property(
            'custom_sample_rate', asset_doc.get("data", {}).get("fps"))
        task.options.anim_sequence_import_data.set_editor_property(
            'import_custom_attribute', True)
        task.options.anim_sequence_import_data.set_editor_property(
            'import_bone_tracks', True)
        task.options.anim_sequence_import_data.set_editor_property(
            'remove_redundant_keys', False)
        task.options.anim_sequence_import_data.set_editor_property(
            'convert_scene', True)
        task.options.anim_sequence_import_data.set_editor_property(
            'set_material_drive_parameter_on_custom_attribute', True)
        task.options.anim_sequence_import_data.set_editor_property(
            'do_not_import_curve_with_zero', False)

        AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

        asset_content = unreal.EditorAssetLibrary.list_assets(
            anim_path, recursive=False, include_folder=False
        )

        animation = None
        for a in asset_content:
            unreal.EditorAssetLibrary.save_asset(a)
            imported_asset_data = unreal.EditorAssetLibrary.find_asset_data(a)
            imported_asset = unreal.AssetRegistryHelpers.get_asset(
                imported_asset_data)
            if imported_asset.__class__ == unreal.AnimSequence:
                animation = imported_asset
                break

        if animation:
            actor = None
            if actors_dict.get(instance_name):
                for a in actors_dict.get(instance_name):
                    if a.get_class().get_name() == 'SkeletalMeshActor':
                        actor = a
                        break

            animation.set_editor_property('enable_root_motion', True)
            actor.skeletal_mesh_component.set_editor_property(
                'animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            actor.skeletal_mesh_component.animation_data.set_editor_property(
                'anim_to_play', animation)
            if sequence:
                # Add animation to the sequencer
                bindings = bindings_dict.get(instance_name)

                ar = unreal.AssetRegistryHelpers.get_asset_registry()

                for binding in bindings:
                    tracks = binding.get_tracks()
                    track = None
                    track = tracks[0] if tracks else binding.add_track(
                        unreal.MovieSceneSkeletalAnimationTrack)

                    sections = track.get_sections()
                    section = None
                    if not sections:
                        section = track.add_section()
                    else:
                        section = sections[0]

                        sec_params = section.get_editor_property('params')
                        curr_anim = sec_params.get_editor_property('animation')

                        if curr_anim:
                            # Checks if the animation path has a container.
                            # If it does, it means that the animation is
                            # already in the sequencer.
                            anim_path = str(Path(
                                curr_anim.get_path_name()).parent
                            ).replace('\\', '/')

                            _filter = unreal.ARFilter(
                                class_names=["AyonAssetContainer"],
                                package_paths=[anim_path],
                                recursive_paths=False)
                            containers = ar.get_assets(_filter)

                            if len(containers) > 0:
                                return

                    section.set_range(
                        sequence.get_playback_start(),
                        sequence.get_playback_end())
                    sec_params = section.get_editor_property('params')
                    sec_params.set_editor_property('animation', animation)

    def _get_repre_docs_by_version_id(self, data):
        version_ids = {
            element.get("version")
            for element in data
            if element.get("representation")
        }
        version_ids.discard(None)

        output = collections.defaultdict(list)
        if not version_ids:
            return output

        project_name = get_current_project_name()
        repre_docs = get_representations(
            project_name,
            representation_names=["fbx", "abc"],
            version_ids=version_ids,
            fields=["_id", "parent", "name"]
        )
        for repre_doc in repre_docs:
            version_id = str(repre_doc["parent"])
            output[version_id].append(repre_doc)
        return output

    def _process(self, lib_path, asset_dir, sequence, repr_loaded=None):
        ar = unreal.AssetRegistryHelpers.get_asset_registry()

        with open(lib_path, "r") as fp:
            data = json.load(fp)

        all_loaders = discover_loader_plugins()

        if not repr_loaded:
            repr_loaded = []

        path = Path(lib_path)

        skeleton_dict = {}
        actors_dict = {}
        bindings_dict = {}
        loaded_assets = []

        repre_docs_by_version_id = self._get_repre_docs_by_version_id(data)
        for element in data:
            representation = None
            repr_format = None
            if element.get('representation'):
                repre_docs = repre_docs_by_version_id[element.get("version")]
                if not repre_docs:
                    self.log.error(
                        f"No valid representation found for version "
                        f"{element.get('version')}")
                    continue
                repre_doc = repre_docs[0]
                representation = str(repre_doc["_id"])
                repr_format = repre_doc["name"]

            # This is to keep compatibility with old versions of the
            # json format.

            elif element.get('reference_fbx'):
                representation = element.get('reference_fbx')
                repr_format = 'fbx'
            elif element.get('reference_abc'):
                representation = element.get('reference_abc')
                repr_format = 'abc'
            # If reference is None, this element is skipped, as it cannot be
            # imported in Unreal
            if not representation:
                continue

            instance_name = element.get('instance_name')

            if representation not in repr_loaded:

                repr_loaded.append(representation)

                family = element.get('family')

                loaders = loaders_from_representation(
                    all_loaders, representation)

                loader = None
                if repr_format == 'fbx':
                    loader = self._get_fbx_loader(loaders, family)
                elif repr_format == 'abc':
                    loader = self._get_abc_loader(loaders, family)

                if not loader:
                    self.log.error(
                        f"No valid loader found for {representation}")
                    continue

                options = {
                    # "asset_dir": asset_dir
                }
                from openpype.pipeline.load import utils

                assets = load_container(
                    loader,
                    representation,
                    namespace=instance_name,
                    options=options
                )
                container = None
                skeleton = None

                for asset in assets:
                    obj = ar.get_asset_by_object_path(asset).get_asset()
                    if obj.get_class().get_name() == 'AyonAssetContainer':
                        container = obj
                    if obj.get_class().get_name() == 'Skeleton':
                        skeleton = obj


                instances = [
                    item for item in data
                    if ((item.get('version') and
                        item.get('version') == element.get('version')) or
                        item.get('reference_fbx') == representation or
                        item.get('reference_abc') == representation)]

                for instance in instances:
                    transform = instance.get('transform_matrix')
                    basis = instance.get('basis')
                    inst = instance.get('instance_name')

                    actors = []
                    if family == 'model':
                        actors, bindings  = self._process_family(
                            assets, 'StaticMesh', transform, basis,
                            sequence, inst
                        )
                        actors_dict[inst] = actors
                        bindings_dict[inst] = bindings

                    elif family == 'rig':
                        actors, bindings = self._process_family(
                            assets, 'SkeletalMesh', transform, basis,
                            sequence, inst
                        )
                        actors_dict[inst] = actors
                        bindings_dict[inst] = bindings

                    elif family == 'staticMesh':
                        actors, bindings = self._process_family(
                            assets, 'StaticMesh', transform, basis,
                            sequence, inst
                        )
                        print("---PROCESSED",actors,bindings)
                        actors_dict[inst] = actors
                        bindings_dict[inst] = bindings

                    elif family == 'placeholder':
                        actors, bindings = self._process_family(
                            assets, 'World', transform, basis,
                            sequence, inst
                        )

                        actors_dict[inst] = actors
                        bindings_dict[inst] = bindings

                    else:
                        print("oh dear...")
                if skeleton:
                    skeleton_dict[representation] = skeleton
            else:
                skeleton = skeleton_dict.get(representation)
            animation_file = element.get('animation')

            if animation_file and skeleton:
                self._import_animation(
                    asset_dir, path, instance_name, skeleton, actors_dict,
                    animation_file, bindings_dict, sequence)

        return loaded_assets

    @staticmethod
    def _remove_family(assets, components, class_name, prop_name):
        ar = unreal.AssetRegistryHelpers.get_asset_registry()

        objects = []
        for a in assets:
            obj = ar.get_asset_by_object_path(a)
            if obj.get_asset().get_class().get_name() == class_name:
                objects.append(obj)
        for obj in objects:
            for comp in components:
                if comp.get_editor_property(prop_name) == obj.get_asset():
                    comp.get_owner().destroy_actor()

    def _remove_actors(self, path):
        asset_containers = self._get_asset_containers(path)

        # Get all the static and skeletal meshes components in the level
        components = EditorLevelLibrary.get_all_level_actors_components()
        static_meshes_comp = [
            c for c in components
            if c.get_class().get_name() == 'StaticMeshComponent']
        skel_meshes_comp = [
            c for c in components
            if c.get_class().get_name() == 'SkeletalMeshComponent']

        # For all the asset containers, get the static and skeletal meshes.
        # Then, check the components in the level and destroy the matching
        # actors.
        for asset_container in asset_containers:
            package_path = asset_container.get_editor_property('package_path')
            family = EditorAssetLibrary.get_metadata_tag(
                asset_container.get_asset(), 'family')
            assets = EditorAssetLibrary.list_assets(
                str(package_path), recursive=False)
            if family == 'model':
                self._remove_family(
                    assets, static_meshes_comp, 'StaticMesh', 'static_mesh')
            elif family == 'rig':
                self._remove_family(
                    assets, skel_meshes_comp, 'SkeletalMesh', 'skeletal_mesh')

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
        data = get_current_project_settings()
        create_sequences = data["unreal"]["level_sequences_for_layouts"]
        # Create directory for asset and Ayon container
        hierarchy = context.get('asset').get('data').get('parents')
        root = self.ASSET_ROOT
        hierarchy_dir = root
        hierarchy_dir_list = []
        for h in hierarchy:
            hierarchy_dir = f"{hierarchy_dir}/{h}"
            hierarchy_dir_list.append(hierarchy_dir)
        asset = context.get('asset').get('name')
        suffix = "_CON"
        asset_name = f"{asset}_{name}" if asset else name
        tools = unreal.AssetToolsHelpers().get_asset_tools()
        ar = unreal.AssetRegistryHelpers.get_asset_registry()

        asset_dir, container_name = tools.create_unique_asset_name(
            "{}/{}/{}".format(hierarchy_dir, asset, name), suffix="")

        container_name += suffix
        EditorAssetLibrary.make_directory(asset_dir)

        asset_subset = f'{asset}_{container_name[:-4]}'

        master_level = None
        shot = None
        sequences = []
        level = f"{asset_dir}/{asset_subset}_map.{asset_subset}_map"

        if not EditorAssetLibrary.does_asset_exist(level):
            EditorLevelLibrary.new_level(level)
        elif replacing_AYONs_level_hierarchy:
            EditorLevelLibrary.load_level(level)

        level_data = EditorAssetLibrary.find_asset_data(level)
        level_asset = level_data.get_asset()
        if create_sequences:
            # Create map for the shot, and create hierarchy of map. If the
            # maps already exist, we will use them.
            if hierarchy:
                h_dir = hierarchy_dir_list[1]
                h_asset = hierarchy[1]
                master_level = f"{h_dir}/{h_asset}_map.{h_asset}_map"
                if not EditorAssetLibrary.does_asset_exist(master_level):
                    EditorLevelLibrary.new_level(f"{h_dir}/{h_asset}_map")

            # If there is a level sequence of all levels
            if not replacing_AYONs_level_hierarchy and master_level:
                EditorLevelLibrary.load_level(master_level)
                added_levels = EditorLevelUtils.get_levels( EditorLevelLibrary.get_editor_world() )

                # Go through all the master level children and check that that level is added
                obj = ar.get_asset_by_object_path(level)
                level_obj = obj.get_asset()
                level_added = False
                for a in added_levels:

                    if a.get_path_name().split(":")[0] == level_obj.get_path_name():
                        level_added = True

                if not level_added:
                    EditorLevelUtils.add_level_to_world(
                        EditorLevelLibrary.get_editor_world(),
                        level,
                        unreal.LevelStreamingDynamic
                    )

            # Get all the sequences in the hierarchy. It will create them, if
            # they don't exist.
            frame_ranges = []
            for (h_dir, h) in zip(hierarchy_dir_list, hierarchy):
                root_content = EditorAssetLibrary.list_assets(
                    h_dir, recursive=False, include_folder=False)

                existing_sequences = [
                    EditorAssetLibrary.find_asset_data(asset)
                    for asset in root_content
                    if EditorAssetLibrary.find_asset_data(
                        asset).get_class().get_name() == 'LevelSequence'
                ]

                if not existing_sequences:
                    sequence, frame_range = generate_sequence(h, h_dir)

                    sequences.append(sequence)
                    frame_ranges.append(frame_range)
                else:
                    for e in existing_sequences:
                        sequences.append(e.get_asset())
                        frame_ranges.append((
                            e.get_asset().get_playback_start(),
                            e.get_asset().get_playback_end()+1))

            # FIXME -  Get Current LevelSequence objects and check if already present
            # DONE
            asset_children = EditorAssetLibrary.list_assets(
                asset_dir, recursive=False, include_folder=False)
            ar = unreal.AssetRegistryHelpers.get_asset_registry()
            shot = None

            # Get all the asset containers
            for a in asset_children:
                obj = ar.get_asset_by_object_path(a)
                _a = obj.get_asset()
                if _a.get_name() == asset_subset and _a.get_class().get_name() == "LevelSequence":
                    shot = _a

            ## FIXME use existing levels

            # If shot does nt ex
            if not shot:
                shot = tools.create_asset(
                    asset_name=asset_subset,
                    package_path=asset_dir,
                    asset_class=unreal.LevelSequence,
                    factory=unreal.LevelSequenceFactoryNew()
                    )
                self.log.warning("Made new shot :"+str(shot.get_name()))

            else:

                self.log.warning("using existing shot :"+str(shot.get_name()))
            # sequences and frame_ranges have the same length
            for i in range(0, len(sequences) - 1):
                set_sequence_hierarchy(
                    sequences[i], sequences[i + 1],
                    frame_ranges[i][1],
                    frame_ranges[i + 1][0], frame_ranges[i + 1][1],
                    [level])

            project_name = get_current_project_name()
            data = get_asset_by_name(project_name, asset)["data"]
            shot.set_display_rate(
                unreal.FrameRate(data.get("fps"), 1.0))
            shot.set_playback_start(data.get('frameStart'))
            shot.set_playback_end(data.get('frameEnd'))
            if sequences:
                set_sequence_hierarchy(
                    sequences[-1], shot,
                    frame_ranges[-1][1],
                    data.get('clipIn'), data.get('clipOut'),
                    [level])

            EditorLevelLibrary.load_level(level)

        path = self.filepath_from_context(context)
        loaded_assets = self._process(path, asset_dir, shot)

        for s in sequences:
            EditorAssetLibrary.save_asset(s.get_path_name())

        EditorLevelLibrary.save_current_level()


        asset_children = EditorAssetLibrary.list_assets(
            asset_dir, recursive=False, include_folder=False)
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
            create_container(
                container=container_name, path=asset_dir)
        else:
            pass

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
            "family": context["representation"]["context"]["family"],
            "loaded_assets": loaded_assets
        }
        imprint(
            "{}/{}".format(asset_dir, container_name), data)

        save_dir = hierarchy_dir_list[0] if create_sequences else asset_dir

        asset_content = EditorAssetLibrary.list_assets(
            save_dir, recursive=True, include_folder=False)

        for a in asset_content:
            EditorAssetLibrary.save_asset(a)

        #if master_level:
        #
        if not replacing_AYONs_level_hierarchy:
            EditorLevelLibrary.load_level(master_level)

        return asset_content

    def update(self, container, representation):
        raise NotImplementedError(
            'Updating layouts is not supported. Please load it instead.')

        data = get_current_project_settings()
        create_sequences = data["unreal"]["level_sequences_for_layouts"]

        ar = unreal.AssetRegistryHelpers.get_asset_registry()

        curr_level_sequence = LevelSequenceLib.get_current_level_sequence()
        curr_time = LevelSequenceLib.get_current_time()
        is_cam_lock = LevelSequenceLib.is_camera_cut_locked_to_viewport()

        editor_subsystem = unreal.UnrealEditorSubsystem()
        vp_loc, vp_rot = editor_subsystem.get_level_viewport_camera_info()

        root = "/Game/Ayon"

        asset_dir = container.get('namespace')
        context = representation.get("context")

        hierarchy = context.get('hierarchy').split("/")

        sequence = None
        master_level = None

        if create_sequences:
            h_dir = f"{root}/{hierarchy[0]}"
            h_asset = hierarchy[0]
            master_level = f"{h_dir}/{h_asset}_map.{h_asset}_map"

            filter = unreal.ARFilter(
                class_names=["LevelSequence"],
                package_paths=[asset_dir],
                recursive_paths=False)
            sequences = ar.get_assets(filter)
            sequence = sequences[0].get_asset()

        prev_level = None

        if not master_level:
            curr_level = unreal.LevelEditorSubsystem().get_current_level()
            curr_level_path = curr_level.get_outer().get_path_name()
            # If the level path does not start with "/Game/", the current
            # level is a temporary, unsaved level.
            if curr_level_path.startswith("/Game/"):
                prev_level = curr_level_path

        # Get layout level
        filter = unreal.ARFilter(
            class_names=["World"],
            package_paths=[asset_dir],
            recursive_paths=False)
        levels = ar.get_assets(filter)

        layout_level = levels[0].get_asset().get_path_name()

        EditorLevelLibrary.save_all_dirty_levels()
        EditorLevelLibrary.load_level(layout_level)

        # Delete all the actors in the level
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for actor in actors:
            unreal.EditorLevelLibrary.destroy_actor(actor)

        if create_sequences:
            EditorLevelLibrary.save_current_level()

        EditorAssetLibrary.delete_directory(f"{asset_dir}/animations/")

        source_path = get_representation_path(representation)

        loaded_assets = self._process(source_path, asset_dir, sequence)

        data = {
            "representation": str(representation["_id"]),
            "parent": str(representation["parent"]),
            "loaded_assets": loaded_assets
        }
        imprint(
            "{}/{}".format(asset_dir, container.get('container_name')), data)

        EditorLevelLibrary.save_current_level()

        save_dir = f"{root}/{hierarchy[0]}" if create_sequences else asset_dir

        asset_content = EditorAssetLibrary.list_assets(
            save_dir, recursive=True, include_folder=False)

        for a in asset_content:
            EditorAssetLibrary.save_asset(a)

        if master_level:
            EditorLevelLibrary.load_level(master_level)
        elif prev_level:
            EditorLevelLibrary.load_level(prev_level)

        if curr_level_sequence:
            LevelSequenceLib.open_level_sequence(curr_level_sequence)
            LevelSequenceLib.set_current_time(curr_time)
            LevelSequenceLib.set_lock_camera_cut_to_viewport(is_cam_lock)

        editor_subsystem.set_level_viewport_camera_info(vp_loc, vp_rot)

    def remove(self, container):
        """
        Delete the layout. First, check if the assets loaded with the layout
        are used by other layouts. If not, delete the assets.
        """
        data = get_current_project_settings()
        create_sequences = data["unreal"]["level_sequences_for_layouts"]

        root = "/Game/Ayon"
        path = Path(container.get("namespace"))

        containers = ls()
        layout_containers = [
            c for c in containers
            if (c.get('asset_name') != container.get('asset_name') and
                c.get('family') == "layout")]

        # Check if the assets have been loaded by other layouts, and deletes
        # them if they haven't.
        for asset in eval(container.get('loaded_assets')):
            layouts = [
                lc for lc in layout_containers
                if asset in lc.get('loaded_assets')]

            if not layouts:
                EditorAssetLibrary.delete_directory(str(Path(asset).parent))

                # Delete the parent folder if there aren't any more
                # layouts in it.
                asset_content = EditorAssetLibrary.list_assets(
                    str(Path(asset).parent.parent), recursive=False,
                    include_folder=True
                )

                if len(asset_content) == 0:
                    EditorAssetLibrary.delete_directory(
                        str(Path(asset).parent.parent))

        master_sequence = None
        master_level = None
        sequences = []

        if create_sequences:
            # Remove the Level Sequence from the parent.
            # We need to traverse the hierarchy from the master sequence to
            # find the level sequence.
            namespace = container.get('namespace').replace(f"{root}/", "")
            ms_asset = namespace.split('/')[0]
            ar = unreal.AssetRegistryHelpers.get_asset_registry()
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
            master_level = levels[0].get_asset().get_path_name()

            sequences = [master_sequence]

            asset_subset = f"{container.get('asset')}_{container.get('container_name')[:-4]}"
            container_vis_track_name = unreal.Name(f"{asset_subset}_map")

            parent = None
            for s in sequences:
                tracks = s.get_master_tracks()
                subscene_track = None
                visibility_track = None
                for t in tracks:
                    if t.get_class() == MovieSceneSubTrack.static_class():
                        subscene_track = t
                    if (t.get_class() ==
                            MovieSceneLevelVisibilityTrack.static_class()):
                        visibility_track = t
                if subscene_track:
                    sections = subscene_track.get_sections()
                    for ss in sections:
                        if ss.get_sequence().get_name() == asset_subset:
                            parent = s
                            subscene_track.remove_section(ss)
                            break
                        sequences.append(ss.get_sequence())
                    # Update subscenes indexes.
                    i = 0
                    for ss in sections:
                        ss.set_row_index(i)
                        i += 1

                if visibility_track:
                    sections = visibility_track.get_sections()
                    for ss in sections:
                        if container_vis_track_name in ss.get_level_names():
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
        if not replacing_AYONs_level_hierarchy:
            EditorLevelLibrary.save_all_dirty_levels()
            EditorAssetLibrary.make_directory(f"{root}/tmp")
            tmp_level = f"{root}/tmp/temp_map"
            if not EditorAssetLibrary.does_asset_exist(f"{tmp_level}.temp_map"):
                EditorLevelLibrary.new_level(tmp_level)
            else:
                EditorLevelLibrary.load_level(tmp_level)
        else:
            EditorLevelLibrary.new_level('/Game')
            # This will warn that it can't save the new level, but
            # that's perfect for our needs, as we want an ephemeral
            # level, i.e. we just want to load _nothing_

        # Delete the layout directory.
        EditorAssetLibrary.delete_directory(str(path))

        if not replacing_AYONs_level_hierarchy:
            if create_sequences:
                EditorLevelLibrary.load_level(master_level)
                EditorAssetLibrary.delete_directory(f"{root}/tmp")

            # Delete the parent folder if there aren't any more layouts in it.
            asset_content = EditorAssetLibrary.list_assets(
                str(path.parent), recursive=True, include_folder=True
            )

            if len(asset_content) == 0:
                EditorAssetLibrary.delete_directory(str(path.parent))
