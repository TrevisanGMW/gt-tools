"""
Motion Evaluation Maya Host - Reads and loads scenes with maya.cmds and OpenMaya.

Maya is imported lazily, so this module imports anywhere; its methods need Maya
(inside Maya, or mayapy with session()).
"""

from .host_base import SceneHost
from .. import console
import contextlib
import os

METERS_PER_LINEAR_UNIT = {
    "mm": 0.001,
    "millimeter": 0.001,
    "cm": 0.01,
    "centimeter": 0.01,
    "m": 1.0,
    "meter": 1.0,
    "km": 1000.0,
    "kilometer": 1000.0,
    "in": 0.0254,
    "inch": 0.0254,
    "ft": 0.3048,
    "foot": 0.3048,
    "yd": 0.9144,
    "yard": 0.9144,
    "mi": 1609.344,
    "mile": 1609.344,
}
SCORE_NODE_TYPE = "network"


def get_maya_cmds():
    """Imports maya.cmds lazily.

    Returns:
        module: maya.cmds.
    """
    import maya.cmds as cmds

    return cmds


class MayaHost(SceneHost):
    """Scene host for Autodesk Maya (GUI, mayapy, or maya.standalone)."""

    name = "maya"
    label = "Maya"
    scene_extensions = (".ma", ".mb", ".fbx", ".usd", ".usda", ".usdc")
    copy_extension = ".ma"
    joint_label = "joint"
    supports_selection = True
    supports_score_write = True

    # ------------------------------------------------ Session ------------------------------------------------
    def is_available(self):
        """Checks whether Maya's Python modules can be imported.

        Returns:
            bool: True inside Maya or mayapy.
        """
        import importlib.util

        try:
            return importlib.util.find_spec("maya") is not None
        except (ImportError, ValueError):
            return False

    def is_running(self):
        """Checks whether Maya is already running in this process (GUI or maya.standalone).

        Returns:
            bool: True when maya.cmds is usable.
        """
        try:
            cmds = get_maya_cmds()
            return hasattr(cmds, "about") and bool(cmds.about(version=True))
        except Exception:
            return False

    @contextlib.contextmanager
    def session(self, quiet=False):
        """Initializes maya.standalone when not already inside Maya, and uninitializes it afterwards.

        Args:
            quiet (bool): Hide Maya's startup and shutdown messages.

        Yields:
            bool: True when this context started maya.standalone.
        """
        started = False
        if not self.is_running():
            import maya.standalone

            with console.quiet_output(quiet):
                maya.standalone.initialize(name="python")
            started = True
        try:
            yield started
        finally:
            if started:
                import maya.standalone

                with console.quiet_output(quiet):
                    maya.standalone.uninitialize()

    def get_unavailable_message(self):
        """Explains how to run Maya evaluations.

        Returns:
            str: Message for the user.
        """
        return "Maya is not available in this Python. Run the script with Maya's Python (mayapy)."

    # ------------------------------------------------ Files ------------------------------------------------
    def load_scene(self, file_path, load_mode="open", align_up_axis=True):
        """Opens or imports a scene file, discarding the current scene.

        Args:
            file_path (str): Scene path (.ma, .mb, .fbx, .usd, .usda, .usdc, ...).
            load_mode (str): "open" or "import" (into a new empty scene). USD files are always imported.
            align_up_axis (bool): USD only: rotate and scale the file into the scene's up axis and unit
                (see usd_scene.load_usd_scene).

        Returns:
            dict: USD stage info for USD files, otherwise an empty dictionary.
        """
        from .. import usd_scene

        cmds = get_maya_cmds()
        if usd_scene.is_usd_file(file_path):
            return usd_scene.load_usd_scene(file_path, align_up_axis=align_up_axis)
        if file_path.lower().endswith(".fbx") and not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            cmds.loadPlugin("fbxmaya", quiet=True)
        if load_mode == "import" or not file_path.lower().endswith((".ma", ".mb")):
            cmds.file(new=True, force=True)
            cmds.file(file_path, i=True, force=True)
        else:
            cmds.file(file_path, open=True, force=True, prompt=False)
        return {}

    def save_scene_copy(self, target_path):
        """Saves the open scene as Maya ASCII under a new name.

        Args:
            target_path (str): Destination .ma path.
        """
        cmds = get_maya_cmds()
        cmds.file(rename=target_path)
        cmds.file(save=True, force=True, type="mayaAscii")

    def get_scene_path(self):
        """Gets the path of the open scene.

        Returns:
            str: Scene path, or "" for unsaved scenes.
        """
        return get_maya_cmds().file(query=True, sceneName=True) or ""

    # ------------------------------------------------ Scene Info ------------------------------------------------
    def get_fps(self):
        """Gets the scene frame rate.

        Returns:
            float: Frames per second.
        """
        import maya.api.OpenMaya as om2

        return float(om2.MTime(1.0, om2.MTime.kSeconds).asUnits(om2.MTime.uiUnit()))

    def get_meters_per_unit(self):
        """Gets the size of one scene linear unit in meters.

        Returns:
            float: Meters per scene unit.
        """
        unit = str(get_maya_cmds().currentUnit(query=True, linear=True) or "cm").lower()
        return METERS_PER_LINEAR_UNIT.get(unit, 0.01)

    def get_up_axis(self):
        """Gets the scene up axis.

        Returns:
            str: "y" or "z".
        """
        return str(get_maya_cmds().upAxis(query=True, axis=True) or "y").lower()

    def get_time_range(self, kind):
        """Gets the playback (inner) or animation (outer) time slider range.

        Args:
            kind (str): "playback" or "animation".

        Returns:
            tuple: (start, end) frames.
        """
        cmds = get_maya_cmds()
        if kind == "animation":
            return (cmds.playbackOptions(query=True, animationStartTime=True),
                    cmds.playbackOptions(query=True, animationEndTime=True))
        return cmds.playbackOptions(query=True, minTime=True), cmds.playbackOptions(query=True, maxTime=True)

    def get_key_range(self, node_paths):
        """Gets the first and last keyframe on some nodes.

        Args:
            node_paths (list): Node paths.

        Returns:
            tuple or None: (start, end) frames, or None without keys.
        """
        key_times = get_maya_cmds().keyframe(list(node_paths), query=True, timeChange=True) or []
        if not key_times:
            return None
        return min(key_times), max(key_times)

    # ------------------------------------------------ Nodes ------------------------------------------------
    def list_joints(self):
        """Lists every joint.

        Returns:
            list: Long joint paths.
        """
        return get_maya_cmds().ls(type="joint", long=True) or []

    def list_transforms(self):
        """Lists transforms that are not joints.

        Returns:
            list: Long transform paths.
        """
        cmds = get_maya_cmds()
        joint_set = set(self.list_joints())
        return [path for path in (cmds.ls(type="transform", long=True) or []) if path not in joint_set]

    def list_animated_nodes(self):
        """Lists transforms driven directly by animation curves.

        Returns:
            list: Sorted long transform paths.
        """
        cmds = get_maya_cmds()
        curves = cmds.ls(type=["animCurveTL", "animCurveTA", "animCurveTU"]) or []
        if not curves:
            return []
        connected = cmds.listConnections(curves, source=False, destination=True, type="transform") or []
        return sorted(set(cmds.ls(connected, long=True) or []))

    def find_nodes(self, pattern):
        """Finds transforms (joints included) matching a name or wildcard, with Maya's ls.

        Args:
            pattern (str): Name or wildcard such as "*:root".

        Returns:
            list: Long node paths.
        """
        return get_maya_cmds().ls(str(pattern).strip(), long=True, type="transform") or []

    def get_selected_nodes(self):
        """Gets the selected transforms (joints included).

        Returns:
            list: Long node paths.
        """
        return get_maya_cmds().ls(selection=True, long=True, type="transform") or []

    def get_parents(self, node_paths):
        """Gets the DAG parent of each node.

        Args:
            node_paths (list): Long node paths.

        Returns:
            dict: Node path to parent path (or None).
        """
        cmds = get_maya_cmds()
        parents = {}
        for node_path in node_paths:
            parent = cmds.listRelatives(node_path, parent=True, fullPath=True) or []
            parents[node_path] = parent[0] if parent else None
        return parents

    def sample_world_matrices(self, node_paths, start_frame, end_frame):
        """Samples world matrices for every node at every frame.

        The current time is restored afterwards and viewport refresh is suspended while sampling.

        Args:
            node_paths (list): Long node paths.
            start_frame (int): First frame.
            end_frame (int): Last frame.

        Returns:
            dict: Node path to a list of flat 16-value matrices.
        """
        import maya.api.OpenMaya as om2

        cmds = get_maya_cmds()
        selection = om2.MSelectionList()
        for node_path in node_paths:
            selection.add(node_path)
        dag_paths = [selection.getDagPath(index) for index in range(selection.length())]
        matrices = {node_path: [] for node_path in node_paths}
        original_time = cmds.currentTime(query=True)
        is_batch = cmds.about(batch=True)
        if not is_batch:
            cmds.refresh(suspend=True)
        try:
            for frame in range(int(start_frame), int(end_frame) + 1):
                cmds.currentTime(frame, update=True)
                for node_path, dag_path in zip(node_paths, dag_paths):
                    matrix = dag_path.inclusiveMatrix()
                    matrices[node_path].append([matrix[index] for index in range(16)])
        finally:
            cmds.currentTime(original_time, update=True)
            if not is_batch:
                cmds.refresh(suspend=False)
        return matrices

    # ------------------------------------------------ Score Storage ------------------------------------------
    def find_score_holder(self, target_mode, node_name, roles=None, create=True):
        """Resolves (and optionally creates) the node that stores the score.

        Args:
            target_mode (str): "dedicated_node", "role", or "named_node".
            node_name (str): Network node name, role key, or node name depending on the mode.
            roles (dict, optional): Resolved role to node path mapping (role mode).
            create (bool): Create the dedicated network node when missing.

        Returns:
            str or None: Node name, or None when it does not exist and was not created.

        Raises:
            ValueError: If the target cannot be used.
        """
        cmds = get_maya_cmds()
        if target_mode == "role":
            role_path = (roles or {}).get(node_name)
            if not role_path or not cmds.objExists(role_path):
                raise ValueError(f'Score target role "{node_name}" was not resolved in this scene.')
            return role_path
        if target_mode == "named_node":
            matches = cmds.ls(node_name, long=True) or []
            if not matches:
                raise ValueError(f'Score target node "{node_name}" does not exist.')
            if len(matches) > 1:
                raise ValueError(f'Score target name "{node_name}" matches {len(matches)} nodes. Use a unique name.')
            return matches[0]
        if cmds.objExists(node_name):
            if cmds.nodeType(node_name) != SCORE_NODE_TYPE:
                raise ValueError(f'Score node "{node_name}" exists but is a {cmds.nodeType(node_name)} node.')
            return node_name
        if not create:
            return None
        return cmds.createNode(SCORE_NODE_TYPE, name=node_name, skipSelect=True)

    def ensure_attribute(self, node, attribute_name, is_string):
        """Adds an integer (0-100) or string attribute when missing.

        Args:
            node (str): Node name.
            attribute_name (str): Attribute name.
            is_string (bool): Create a string attribute instead of an integer.

        Raises:
            ValueError: If the attribute is locked.
        """
        cmds = get_maya_cmds()
        if not cmds.attributeQuery(attribute_name, node=node, exists=True):
            if is_string:
                cmds.addAttr(node, longName=attribute_name, dataType="string")
            else:
                cmds.addAttr(node, longName=attribute_name, attributeType="long", minValue=0, maxValue=100)
            cmds.setAttr(f"{node}.{attribute_name}", channelBox=False)
        if cmds.getAttr(f"{node}.{attribute_name}", lock=True):
            raise ValueError(f'Attribute "{node}.{attribute_name}" is locked.')

    def read_score_value(self, holder, attribute_name):
        """Reads an integer score attribute.

        Args:
            holder (str): Node name.
            attribute_name (str): Attribute name.

        Returns:
            int or None: Stored score, or None when missing.
        """
        cmds = get_maya_cmds()
        if not holder or not cmds.attributeQuery(attribute_name, node=holder, exists=True):
            return None
        return int(cmds.getAttr(f"{holder}.{attribute_name}"))

    def write_score_values(self, holder, score_attribute, score, report_attribute="", report_text=""):
        """Writes the score attribute and optionally the report attribute.

        Args:
            holder (str): Node name.
            score_attribute (str): Integer attribute name.
            score (int): Score 0-100.
            report_attribute (str, optional): String attribute name; empty skips the report.
            report_text (str, optional): Compact report JSON.

        Raises:
            ValueError: If an attribute is locked.
        """
        cmds = get_maya_cmds()
        self.ensure_attribute(holder, score_attribute, is_string=False)
        cmds.setAttr(f"{holder}.{score_attribute}", int(score))
        if report_attribute:
            self.ensure_attribute(holder, report_attribute, is_string=True)
            cmds.setAttr(f"{holder}.{report_attribute}", report_text, type="string")

    # ------------------------------------------------ Optional Dependencies ------------------------------------
    def get_python_executable(self):
        """Gets mayapy (next to maya.exe when running inside the Maya GUI).

        Returns:
            str: Python executable path.
        """
        import sys

        executable = sys.executable
        if os.path.basename(executable).lower().startswith("maya") and "mayapy" not in executable.lower():
            candidate = os.path.join(os.path.dirname(executable), "mayapy.exe" if os.name == "nt" else "mayapy")
            if os.path.isfile(candidate):
                return candidate
        return executable
