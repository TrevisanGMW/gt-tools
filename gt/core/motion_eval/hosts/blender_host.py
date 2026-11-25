"""
Motion Evaluation Blender Host - Reads and loads scenes with Blender's Python API (bpy).

bpy only exists inside Blender, so scripts using this host run with Blender's Python:

    blender --background --factory-startup --python my_script.py -- [script arguments]

How Blender data maps onto the host conventions (see host_base):
    Joints: every bone of every armature. A bone's path is its armature object's path
        followed by its bone chain, for example "|Armature|Hips|Spine". Name prefixes such
        as "mixamorig:" stay in the bone name, so they work like Maya namespaces.
    Transforms: every object (armature objects included), for example "|Rig|Armature".
    Matrices: object.matrix_world @ pose_bone.matrix, transposed into Maya's row-major layout.
    Up axis: always Z. Units: the scene unit scale (1.0 = meters).
    Ranges: "playback" is the preview range when it is on, otherwise the scene range;
        "animation" is always the scene range.

Supported files: .blend (opened), .fbx, .usd/.usda/.usdc, and .bvh (imported into an
empty scene). Maya scenes (.ma, .mb) need Maya.

Known importer differences from Maya: Blender's USD importer replaces NaN values with 0
(a NaN scale becomes a zero scale), so Invalid Values cannot see NaNs authored in USD files.
"""

from .host_base import SceneHost
import contextlib
import os

BLEND_EXTENSIONS = (".blend",)
FBX_EXTENSIONS = (".fbx",)
USD_EXTENSIONS = (".usd", ".usda", ".usdc")
BVH_EXTENSIONS = (".bvh",)
MAYA_EXTENSIONS = (".ma", ".mb")
OBJECT_TRANSFORM_PATHS = ("location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle", "scale",
                          "delta_location", "delta_rotation_euler", "delta_rotation_quaternion", "delta_scale")
SCORE_HOLDER_TYPE = "EMPTY"


def get_bpy():
    """Imports bpy lazily.

    Returns:
        module: bpy.
    """
    import bpy

    return bpy


def flatten_matrix(matrix):
    """Flattens a Blender (column-vector) 4x4 matrix into Maya's row-major, row-vector layout.

    Args:
        matrix (mathutils.Matrix): 4x4 world matrix.

    Returns:
        list: 16 floats, translation at indices 12, 13, 14.
    """
    return [matrix[column][row] for row in range(4) for column in range(4)]


def get_object_path(blender_object):
    """Builds the "|parent|child" path of an object.

    Args:
        blender_object (bpy.types.Object): Object.

    Returns:
        str: Object path.
    """
    names = []
    current = blender_object
    while current is not None:
        names.append(current.name)
        current = current.parent
    return "|" + "|".join(reversed(names))


def get_bone_path(armature_path, bone):
    """Builds the path of a bone under its armature object.

    Args:
        armature_path (str): Armature object path.
        bone (bpy.types.Bone): Bone.

    Returns:
        str: Bone path such as "|Armature|Hips|Spine".
    """
    chain = [parent.name for parent in reversed(bone.parent_recursive)] + [bone.name]
    return f"{armature_path}|" + "|".join(chain)


def get_bone_name_from_data_path(data_path):
    """Gets the bone name of a pose bone F-Curve data path.

    Args:
        data_path (str): F-Curve data path such as 'pose.bones["Hips"].location'.

    Returns:
        str or None: Bone name, or None when the curve does not drive a pose bone.
    """
    prefix = 'pose.bones["'
    if not data_path.startswith(prefix):
        return None
    end = data_path.find('"]', len(prefix))
    if end < 0:
        return None
    return data_path[len(prefix):end].replace('\\"', '"')


def iter_action_fcurves(blender_object):
    """Lists the F-Curves of an object's active action, for legacy and slotted (Blender 4.4+) actions.

    Args:
        blender_object (bpy.types.Object): Object.

    Returns:
        list: F-Curves (empty without animation).
    """
    animation_data = getattr(blender_object, "animation_data", None)
    action = getattr(animation_data, "action", None) if animation_data else None
    if action is None:
        return []
    layers = getattr(action, "layers", None)
    if not layers:
        return list(getattr(action, "fcurves", None) or [])
    slot = getattr(animation_data, "action_slot", None)
    curves = []
    for layer in layers:
        for strip in layer.strips:
            if slot is not None and hasattr(strip, "channelbag"):
                channelbag = strip.channelbag(slot)
                if channelbag is not None:
                    curves.extend(channelbag.fcurves)
            else:
                for channelbag in getattr(strip, "channelbags", []):
                    curves.extend(channelbag.fcurves)
    return curves


class BlenderHost(SceneHost):
    """Scene host for Blender (background or interactive)."""

    name = "blender"
    label = "Blender"
    scene_extensions = BLEND_EXTENSIONS + FBX_EXTENSIONS + USD_EXTENSIONS + BVH_EXTENSIONS
    copy_extension = ".blend"
    joint_label = "bone"
    supports_selection = True
    supports_score_write = True

    def __init__(self):
        """Starts without a node index or loaded file."""
        self.node_index = None
        self.loaded_path = ""

    # ------------------------------------------------ Session ------------------------------------------------
    def is_available(self):
        """Checks whether bpy can be imported (only inside Blender).

        Returns:
            bool: True inside Blender.
        """
        try:
            bpy = get_bpy()
        except ImportError:
            return False
        return isinstance(getattr(getattr(bpy, "app", None), "version", None), tuple)

    def is_running(self):
        """Checks whether this process is Blender.

        Returns:
            bool: True inside Blender.
        """
        return self.is_available()

    @contextlib.contextmanager
    def session(self, quiet=False):
        """Checks that the code runs inside Blender (Blender cannot be started from another Python).

        Args:
            quiet (bool): Unused; Blender is already running.

        Yields:
            bool: Always False (nothing was started).

        Raises:
            RuntimeError: Outside Blender.
        """
        if not self.is_available():
            raise RuntimeError(self.get_unavailable_message())
        yield False

    def get_unavailable_message(self):
        """Explains how to run Blender evaluations.

        Returns:
            str: Message for the user.
        """
        return ("Blender is not available in this Python. Run the script with Blender, for example: "
                'blender --background --factory-startup --python "script.py"')

    # ------------------------------------------------ Files ------------------------------------------------
    def load_scene(self, file_path, load_mode="open", align_up_axis=True):
        """Opens a .blend file, or imports an FBX, USD, or BVH file into an empty scene.

        Blender's importers convert files into Blender's Z-up space themselves, so align_up_axis
        has no effect here; the evaluation reads the up axis from the host.

        Args:
            file_path (str): Scene path.
            load_mode (str): Unused (.blend files are opened, other files imported).
            align_up_axis (bool): Unused (see above).

        Returns:
            dict: "frame_range" (start, end) and "fps" after loading.

        Raises:
            ValueError: If the file type cannot be loaded in Blender.
            RuntimeError: If the importer fails.
        """
        bpy = get_bpy()
        lower_path = str(file_path).lower()
        if lower_path.endswith(MAYA_EXTENSIONS):
            raise ValueError("Maya scenes (.ma, .mb) need Maya. Export them as FBX or USD to evaluate them in Blender.")
        if not lower_path.endswith(self.scene_extensions):
            raise ValueError(f"Blender cannot load {os.path.basename(file_path)}. "
                             f"Supported: {', '.join(self.scene_extensions)}")
        self.node_index = None
        self.loaded_path = ""
        if lower_path.endswith(BLEND_EXTENSIONS):
            bpy.ops.wm.open_mainfile(filepath=str(file_path), load_ui=False)
        else:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            if lower_path.endswith(FBX_EXTENSIONS):
                result = bpy.ops.import_scene.fbx(filepath=str(file_path), use_anim=True, anim_offset=0.0,
                                                  ignore_leaf_bones=False, automatic_bone_orientation=False)
            elif lower_path.endswith(USD_EXTENSIONS):
                self.apply_usd_frame_rate(file_path)
                result = bpy.ops.wm.usd_import(filepath=str(file_path), set_frame_range=True)
            else:
                result = bpy.ops.import_anim.bvh(filepath=str(file_path), update_scene_fps=True,
                                                 update_scene_duration=True)
            if "FINISHED" not in result:
                raise RuntimeError(f"Blender could not import {os.path.basename(file_path)}.")
            if lower_path.endswith(FBX_EXTENSIONS):
                self.fit_scene_range_to_actions()
        self.loaded_path = str(file_path)
        return {"frame_range": self.get_time_range("animation"), "fps": self.get_fps()}

    def apply_usd_frame_rate(self, file_path):
        """Sets the scene frame rate to the USD file's time codes per second (Blender's importer keeps 24).

        Args:
            file_path (str): USD path.
        """
        from .. import usd_scene

        try:
            frames_per_second = float(usd_scene.read_stage_info(file_path)["fps"] or 0.0)
        except Exception:
            return
        if frames_per_second <= 0.0:
            return
        render = get_bpy().context.scene.render
        rounded = int(round(frames_per_second))
        render.fps = max(1, rounded)
        render.fps_base = float(render.fps) / frames_per_second

    def fit_scene_range_to_actions(self):
        """Sets the scene range to the keyed range of the imported animation, when it has keys."""
        bpy = get_bpy()
        key_range = self.get_key_range(self.list_animated_nodes())
        if key_range is None:
            return
        scene = bpy.context.scene
        scene.frame_start = int(round(key_range[0]))
        scene.frame_end = int(round(key_range[1]))
        scene.use_preview_range = False

    def save_scene_copy(self, target_path):
        """Saves the open scene as a copy (the open file keeps its path).

        Args:
            target_path (str): Destination .blend path.
        """
        get_bpy().ops.wm.save_as_mainfile(filepath=str(target_path), copy=True, check_existing=False)

    def get_scene_path(self):
        """Gets the path of the open .blend file, or of the imported file.

        Returns:
            str: Scene path, or "" for a new scene.
        """
        return get_bpy().data.filepath or self.loaded_path

    # ------------------------------------------------ Scene Info ------------------------------------------------
    def get_fps(self):
        """Gets the scene frame rate.

        Returns:
            float: Frames per second.
        """
        render = get_bpy().context.scene.render
        return float(render.fps) / float(render.fps_base or 1.0)

    def get_meters_per_unit(self):
        """Gets the scene unit scale.

        Returns:
            float: Meters per Blender unit (1.0 by default).
        """
        return float(get_bpy().context.scene.unit_settings.scale_length or 1.0)

    def get_up_axis(self):
        """Gets the up axis.

        Returns:
            str: Always "z".
        """
        return "z"

    def get_time_range(self, kind):
        """Gets the preview (playback) or scene (animation) frame range.

        Args:
            kind (str): "playback" or "animation".

        Returns:
            tuple: (start, end) frames.
        """
        scene = get_bpy().context.scene
        if kind != "animation" and scene.use_preview_range:
            return float(scene.frame_preview_start), float(scene.frame_preview_end)
        return float(scene.frame_start), float(scene.frame_end)

    def get_key_range(self, node_paths):
        """Gets the first and last keyframe driving some objects or bones.

        Args:
            node_paths (list): Node paths.

        Returns:
            tuple or None: (start, end) frames, or None without keys.
        """
        wanted = set(node_paths)
        times = []
        for curve, node_path in self.iter_node_curves():
            if node_path in wanted:
                times.extend(point.co[0] for point in curve.keyframe_points)
        if not times:
            return None
        return min(times), max(times)

    # ------------------------------------------------ Nodes ------------------------------------------------
    def get_node_index(self):
        """Builds (once per scene) the lookup from node path to object and bone.

        Returns:
            dict: Node path to (object name, bone name or None, parent path or None).
        """
        if self.node_index is not None:
            return self.node_index
        bpy = get_bpy()
        index = {}
        for blender_object in bpy.context.scene.objects:
            object_path = get_object_path(blender_object)
            parent_path = get_object_path(blender_object.parent) if blender_object.parent else None
            index[object_path] = (blender_object.name, None, parent_path)
            if blender_object.type != "ARMATURE":
                continue
            for bone in blender_object.data.bones:
                bone_parent = get_bone_path(object_path, bone.parent) if bone.parent else object_path
                index[get_bone_path(object_path, bone)] = (blender_object.name, bone.name, bone_parent)
        self.node_index = index
        return index

    def resolve_node(self, node_path):
        """Finds the object and pose bone of a node path.

        Args:
            node_path (str): Node path.

        Returns:
            tuple: (object, pose bone or None).

        Raises:
            ValueError: If the node does not exist.
        """
        entry = self.get_node_index().get(node_path)
        if entry is None:
            self.node_index = None
            entry = self.get_node_index().get(node_path)
        if entry is None:
            raise ValueError(f'Node "{node_path}" does not exist in the Blender scene.')
        blender_object = get_bpy().data.objects[entry[0]]
        pose_bone = blender_object.pose.bones[entry[1]] if entry[1] else None
        return blender_object, pose_bone

    def list_joints(self):
        """Lists every bone of every armature.

        Returns:
            list: Bone paths, in armature then hierarchy order.
        """
        return [path for path, entry in self.get_node_index().items() if entry[1]]

    def list_transforms(self):
        """Lists every object (armature objects included).

        Returns:
            list: Object paths.
        """
        return [path for path, entry in self.get_node_index().items() if not entry[1]]

    def iter_node_curves(self):
        """Lists every transform F-Curve with the node it drives.

        Returns:
            list: (F-Curve, node path) pairs.
        """
        bpy = get_bpy()
        pairs = []
        for blender_object in bpy.context.scene.objects:
            object_path = get_object_path(blender_object)
            for curve in iter_action_fcurves(blender_object):
                bone_name = get_bone_name_from_data_path(curve.data_path)
                if bone_name is not None and blender_object.type == "ARMATURE":
                    bone = blender_object.data.bones.get(bone_name)
                    if bone is not None:
                        pairs.append((curve, get_bone_path(object_path, bone)))
                elif curve.data_path in OBJECT_TRANSFORM_PATHS:
                    pairs.append((curve, object_path))
        return pairs

    def list_animated_nodes(self):
        """Lists objects and bones with transform F-Curves.

        Returns:
            list: Sorted node paths.
        """
        return sorted({node_path for _curve, node_path in self.iter_node_curves()})

    def get_selected_nodes(self):
        """Gets the selected objects and pose bones.

        Returns:
            list: Node paths.
        """
        selected = []
        for path, entry in self.get_node_index().items():
            blender_object, pose_bone = self.resolve_node(path)
            if pose_bone is None:
                if blender_object.select_get():
                    selected.append(path)
            elif getattr(pose_bone, "select", getattr(pose_bone.bone, "select", False)):
                selected.append(path)
        return selected

    def get_parents(self, node_paths):
        """Gets the parent of each node (a root bone's parent is its armature object).

        Args:
            node_paths (list): Node paths.

        Returns:
            dict: Node path to parent path (or None).
        """
        index = self.get_node_index()
        return {node_path: (index.get(node_path) or (None, None, None))[2] for node_path in node_paths}

    def sample_world_matrices(self, node_paths, start_frame, end_frame):
        """Samples the evaluated world matrix of every node at every frame.

        Args:
            node_paths (list): Node paths.
            start_frame (int): First frame.
            end_frame (int): Last frame.

        Returns:
            dict: Node path to a list of flat 16-value matrices.
        """
        bpy = get_bpy()
        scene = bpy.context.scene
        resolved = [(node_path,) + self.resolve_node(node_path) for node_path in node_paths]
        matrices = {node_path: [] for node_path in node_paths}
        original_frame = scene.frame_current
        try:
            for frame in range(int(start_frame), int(end_frame) + 1):
                scene.frame_set(frame)
                depsgraph = bpy.context.evaluated_depsgraph_get()
                for node_path, blender_object, pose_bone in resolved:
                    evaluated = blender_object.evaluated_get(depsgraph)
                    if pose_bone is None:
                        matrix = evaluated.matrix_world
                    else:
                        matrix = evaluated.matrix_world @ evaluated.pose.bones[pose_bone.name].matrix
                    matrices[node_path].append(flatten_matrix(matrix))
        finally:
            scene.frame_set(original_frame)
        return matrices

    # ------------------------------------------------ Score Storage ------------------------------------------
    def find_score_holder(self, target_mode, node_name, roles=None, create=True):
        """Finds (and optionally creates) the object or bone that stores the score as custom properties.

        The dedicated holder is an empty object (the Blender counterpart of Maya's network node).

        Args:
            target_mode (str): "dedicated_node", "role", or "named_node".
            node_name (str): Empty object name, role key, or node name depending on the mode.
            roles (dict, optional): Resolved role to node path mapping (role mode).
            create (bool): Create the dedicated empty when missing.

        Returns:
            str or None: Node path, or None when missing and not created.

        Raises:
            ValueError: If the target cannot be used.
        """
        bpy = get_bpy()
        if target_mode == "role":
            role_path = (roles or {}).get(node_name)
            if not role_path or role_path not in self.get_node_index():
                raise ValueError(f'Score target role "{node_name}" was not resolved in this scene.')
            return role_path
        if target_mode == "named_node":
            matches = self.find_nodes(node_name)
            if not matches:
                raise ValueError(f'Score target node "{node_name}" does not exist.')
            if len(matches) > 1:
                raise ValueError(f'Score target name "{node_name}" matches {len(matches)} nodes. Use a unique name.')
            return matches[0]
        existing = bpy.data.objects.get(node_name)
        if existing is not None:
            if existing.type != SCORE_HOLDER_TYPE:
                raise ValueError(f'Score object "{node_name}" exists but is a {existing.type.lower()} object.')
            return get_object_path(existing)
        if not create:
            return None
        holder = bpy.data.objects.new(node_name, None)
        bpy.context.scene.collection.objects.link(holder)
        self.node_index = None
        return get_object_path(holder)

    def get_property_owner(self, holder):
        """Gets the object or pose bone that carries a holder's custom properties.

        Args:
            holder (str): Node path.

        Returns:
            bpy.types.ID or bpy.types.PoseBone: Property owner.
        """
        blender_object, pose_bone = self.resolve_node(holder)
        return pose_bone if pose_bone is not None else blender_object

    def read_score_value(self, holder, attribute_name):
        """Reads an integer custom property.

        Args:
            holder (str): Node path.
            attribute_name (str): Property name.

        Returns:
            int or None: Stored score, or None when missing.
        """
        if not holder:
            return None
        owner = self.get_property_owner(holder)
        if attribute_name not in owner.keys():
            return None
        return int(owner[attribute_name])

    def write_score_values(self, holder, score_attribute, score, report_attribute="", report_text=""):
        """Writes the score (and optionally the report) as custom properties.

        Args:
            holder (str): Node path.
            score_attribute (str): Integer property name.
            score (int): Score 0-100.
            report_attribute (str, optional): String property name; empty skips the report.
            report_text (str, optional): Compact report JSON.
        """
        owner = self.get_property_owner(holder)
        owner[score_attribute] = int(score)
        if report_attribute:
            owner[report_attribute] = str(report_text)

    # ------------------------------------------------ Optional Dependencies ------------------------------------
    def get_dependency_target(self):
        """Gets Blender's user module folder, which Blender always puts on sys.path.

        Blender ignores Python's user site-packages, so "pip install --user" is not seen;
        packages installed here are (for every Blender script, including background runs).

        Returns:
            str: Folder path (created by pip when missing).
        """
        return get_bpy().utils.user_resource("SCRIPTS", path=os.path.join("addons", "modules"))
