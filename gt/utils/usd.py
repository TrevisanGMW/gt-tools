"""
USD Utilities

This module keeps Maya USD operations behind lazy imports so it can be imported
outside Maya during tests and project serialization.
"""

import json
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UsdExportFormat:
    """Known USD output format values."""

    USDA = "usda"
    USDC = "usdc"


DEFAULT_NATIVE_CUSTOM_ATTRIBUTES = [
    "contact_heel_end_l.contactWeight",
    "contact_ball_l.contactWeight",
    "contact_toe_end_l.contactWeight",
    "contact_heel_end_r.contactWeight",
    "contact_ball_r.contactWeight",
    "contact_toe_end_r.contactWeight",
    "trajectory_raw_heading.velocity",
    "trajectory_smooth_heading.velocity",
    "trajectory_raw_heading.headingC",
    "trajectory_raw_heading.headingS",
    "trajectory_raw_heading.position2DX",
    "trajectory_raw_heading.position2DY",
    "trajectory_smooth_heading.headingC",
    "trajectory_smooth_heading.headingS",
    "trajectory_smooth_heading.position2DX",
    "trajectory_smooth_heading.position2DY",
    "trajectory_smooth_spline.admmPosMargin",
    "trajectory_smooth_spline.admmHeadingMargin",
    "trajectory_smooth_spline.admmRho",
    "trajectory_smooth_spline.admmIters",
]

DEFAULT_CUSTOM_DATA_ATTRIBUTES = [
    "SK_Universal_Simplified.collections",
]


def get_maya_cmds():
    """Gets maya.cmds using a lazy import.

    Returns:
        module: maya.cmds module.

    Raises:
        ImportError: If Maya commands are unavailable.
    """
    import maya.cmds as cmds

    return cmds


def get_pxr_usd():
    """Gets the Pixar USD module using a lazy import.

    Returns:
        module: pxr.Usd module.

    Raises:
        RuntimeError: If the pxr USD module is unavailable.
    """
    try:
        from pxr import Usd

        return Usd
    except ImportError as exception:
        raise RuntimeError("Could not import pxr.Usd. Ensure Maya USD is fully installed: {0}".format(exception))


def ensure_maya_usd_plugin_loaded(plugin_name="mayaUsdPlugin"):
    """Ensures the Maya USD plugin is loaded.

    Args:
        plugin_name (str, optional): Maya USD plugin name.

    Returns:
        bool: True when the plugin is loaded.
    """
    cmds = get_maya_cmds()
    if cmds.pluginInfo(plugin_name, query=True, loaded=True):
        return True
    try:
        cmds.loadPlugin(plugin_name, quiet=True)
        return cmds.pluginInfo(plugin_name, query=True, loaded=True)
    except Exception as exception:
        logger.warning("Unable to load Maya USD plugin %s: %s", plugin_name, exception)
        return False


def get_usd_export_command():
    """Finds the available Maya USD export command.

    Returns:
        callable or None: Export command function if available.
    """
    cmds = get_maya_cmds()
    for command_name in ["mayaUSDExport", "usdExport"]:
        command = getattr(cmds, command_name, None)
        if command:
            return command
    return None


def is_usd_export_available(plugin_name="mayaUsdPlugin"):
    """Checks whether USD export is available in this Maya runtime.

    Args:
        plugin_name (str, optional): Maya USD plugin name.

    Returns:
        bool: True when a USD export command is available.
    """
    try:
        if not ensure_maya_usd_plugin_loaded(plugin_name=plugin_name):
            return False
        return bool(get_usd_export_command())
    except ImportError:
        return False


def normalize_usd_extension(extension):
    """Normalizes a USD file extension.

    Args:
        extension (str): Extension with or without a leading dot.

    Returns:
        str: Normalized extension with a leading dot.
    """
    extension = str(extension or ".usd").lower()
    if not extension.startswith("."):
        extension = "." + extension
    return extension


def normalize_usd_format(usd_format, output_path=None):
    """Normalizes a USD format value.

    Args:
        usd_format (str): USD format value.
        output_path (str, optional): Output path used when format is auto.

    Returns:
        str: `usda` or `usdc`.
    """
    usd_format = str(usd_format or "auto").lower()
    if usd_format in [UsdExportFormat.USDA, UsdExportFormat.USDC]:
        return usd_format
    extension = normalize_usd_extension(os.path.splitext(output_path)[1]) if output_path else ".usd"
    if extension == ".usda":
        return UsdExportFormat.USDA
    return UsdExportFormat.USDC


def get_timeline_frame_range():
    """Gets the current Maya playback frame range.

    Returns:
        tuple: Start and end frames.
    """
    cmds = get_maya_cmds()
    start_frame = cmds.playbackOptions(query=True, minTime=True)
    end_frame = cmds.playbackOptions(query=True, maxTime=True)
    return start_frame, end_frame


def split_attribute_paths(attribute_paths):
    """Normalizes attribute path input into a list.

    Args:
        attribute_paths (list or str): Attribute paths in `node.attribute` form.

    Returns:
        list: Normalized attribute path strings.
    """
    if not attribute_paths:
        return []
    if isinstance(attribute_paths, str):
        attribute_paths = attribute_paths.replace(",", "\n").splitlines()
    return [str(item).strip() for item in attribute_paths if str(item).strip()]


def get_short_name(node):
    """Gets a namespace-free node short name.

    Args:
        node (str): Maya DAG or dependency node name.

    Returns:
        str: Namespace-free short node name.
    """
    return str(node or "").split("|")[-1].split(":")[-1]


def find_node(node_name):
    """Finds a Maya node and returns its long DAG path when available.

    Args:
        node_name (str): Node name to find.

    Returns:
        str or None: Matching node name.
    """
    cmds = get_maya_cmds()
    if cmds.objExists(node_name):
        matches = cmds.ls(node_name, long=True) or [node_name]
        return matches[0]
    short_name = get_short_name(node_name)
    matches = cmds.ls(short_name, long=True) or cmds.ls("*:{0}".format(short_name), long=True) or []
    return matches[0] if matches else None


class UsdExporter:
    """Maya USD exporter with reusable preferences and post-processing helpers."""

    def __init__(self, **kwargs):
        """Initializes the USD exporter.

        Args:
            **kwargs: Export preferences.
        """
        self.selection = bool(kwargs.get("selection", True))
        self.output_format = kwargs.get("output_format", "usdc")
        self.static_export = bool(kwargs.get("static_export", False))
        self.animation = bool(kwargs.get("animation", True))
        self.auto_frame_range = bool(kwargs.get("auto_frame_range", True))
        self.frame_start = kwargs.get("frame_start")
        self.frame_end = kwargs.get("frame_end")
        self.auto_detect_roots = bool(kwargs.get("auto_detect_roots", True))
        self.target_roots = split_attribute_paths(kwargs.get("target_roots") or [])
        self.target_node = kwargs.get("target_node") or ""
        self.include_joints = bool(kwargs.get("include_joints", True))
        self.include_locators = bool(kwargs.get("include_locators", True))
        self.include_curves = bool(kwargs.get("include_curves", True))
        self.force_z_up = bool(kwargs.get("force_z_up", False))
        self.zero_root_rotation = bool(kwargs.get("zero_root_rotation", False))
        self.export_materials = bool(kwargs.get("export_materials", False))
        self.export_skeletons = bool(kwargs.get("export_skeletons", True))
        self.export_skin = bool(kwargs.get("export_skin", True))
        self.export_blend_shapes = bool(kwargs.get("export_blend_shapes", True))
        self.export_color_sets = bool(kwargs.get("export_color_sets", False))
        self.export_uvs = bool(kwargs.get("export_uvs", False))
        self.export_visibility = bool(kwargs.get("export_visibility", True))
        self.strip_namespaces = bool(kwargs.get("strip_namespaces", False))
        self.merge_transform_and_shape = bool(kwargs.get("merge_transform_and_shape", False))
        self.write_defaults = bool(kwargs.get("write_defaults", True))
        self.ignore_warnings = bool(kwargs.get("ignore_warnings", True))
        self.default_prim = kwargs.get("default_prim") or ""
        self.root_prim = kwargs.get("root_prim") or ""
        self.root_prim_type = kwargs.get("root_prim_type") or "Scope"
        self.parent_scope = kwargs.get("parent_scope") or ""
        native_custom_attributes = kwargs.get("native_custom_attributes")
        if native_custom_attributes is None:
            native_custom_attributes = []
        custom_data_attributes = kwargs.get("custom_data_attributes")
        if custom_data_attributes is None:
            custom_data_attributes = []
        self.native_custom_attributes = split_attribute_paths(native_custom_attributes)
        self.custom_data_attributes = split_attribute_paths(custom_data_attributes)

    def __enter__(self, *args, **kwargs):
        """Enters the context manager and validates USD runtime availability.

        Args:
            *args: Unused positional arguments.
            **kwargs: Unused keyword arguments.

        Returns:
            UsdExporter: This exporter.
        """
        if not is_usd_export_available():
            raise RuntimeError("Maya USD export is unavailable in the current runtime.")
        return self

    def __exit__(self, *args, **kwargs):
        """Exits the context manager.

        Args:
            *args: Unused positional arguments.
            **kwargs: Unused keyword arguments.
        """
        return None

    def export_file(self, path):
        """Exports the current Maya scene to a USD file.

        Args:
            path (str): Destination USD file path.

        Returns:
            str: Exported USD file path.

        Raises:
            RuntimeError: If no export roots are available for root-based export.
        """
        cmds = get_maya_cmds()
        export_command = get_usd_export_command()
        if not export_command:
            raise RuntimeError("Maya USD export command was not found.")

        output_path = os.path.normpath(path)
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        current_selection = cmds.ls(selection=True, long=True) or []
        current_up_axis = cmds.upAxis(query=True, ax=True)
        warning_state = self.get_warning_suppression_state()
        undo_chunk_open = False
        export_roots = self.get_export_roots()

        if self.auto_detect_roots and not export_roots:
            raise RuntimeError("No USD export roots found in the current scene.")

        try:
            cmds.undoInfo(state=True)
            cmds.undoInfo(openChunk=True)
            undo_chunk_open = True
            if self.force_z_up and str(current_up_axis).lower() != "z":
                cmds.upAxis(ax="z", rv=False)
            if self.zero_root_rotation and export_roots:
                self.zero_root_rotations(export_roots)
            self.apply_native_custom_attribute_tags()
            if export_roots:
                cmds.select(export_roots, replace=True)
            if self.ignore_warnings:
                self.set_warning_suppression_state(True)
            self.run_export_command(
                export_command=export_command,
                export_kwargs=self.build_export_kwargs(output_path, export_roots),
            )
            self.apply_post_custom_data(output_path)
            logger.info("USD file exported: %s", output_path)
        finally:
            self.set_warning_suppression_state(warning_state)
            if self.force_z_up and str(current_up_axis).lower() != "z":
                try:
                    cmds.upAxis(ax=current_up_axis, rv=False)
                except Exception:
                    pass
            if undo_chunk_open:
                try:
                    cmds.undoInfo(closeChunk=True)
                    cmds.undo()
                except Exception:
                    pass
            if current_selection:
                cmds.select(current_selection, replace=True)
            else:
                cmds.select(clear=True)
        return output_path

    def build_export_kwargs(self, output_path, export_roots=None):
        """Builds keyword arguments for `mayaUSDExport`.

        Args:
            output_path (str): Destination USD path.
            export_roots (list, optional): Root nodes being exported.

        Returns:
            dict: Keyword arguments for Maya USD export.
        """
        kwargs = {
            "file": output_path.replace("\\", "/"),
            "defaultUSDFormat": normalize_usd_format(self.output_format, output_path=output_path),
            "exportSkels": "auto" if self.export_skeletons else "none",
            "exportSkin": "auto" if self.export_skin else "none",
            "exportBlendShapes": self.export_blend_shapes,
            "exportColorSets": self.export_color_sets,
            "exportUVs": self.export_uvs,
            "exportVisibility": self.export_visibility,
            "exportMaterials": self.export_materials,
            "stripNamespaces": self.strip_namespaces,
            "mergeTransformAndShape": self.merge_transform_and_shape,
            "writeDefaults": self.write_defaults,
            "ignoreWarnings": self.ignore_warnings,
            "staticSingleSample": self.static_export,
        }
        if export_roots or self.selection:
            kwargs["selection"] = True
        if self.force_z_up:
            kwargs["upAxis"] = "z"
        if self.animation and not self.static_export:
            kwargs["frameRange"] = self.get_frame_range()
        if not self.export_materials:
            kwargs["shadingMode"] = "none"
        if self.default_prim:
            kwargs["defaultPrim"] = self.default_prim
        if self.root_prim:
            kwargs["rootPrim"] = self.root_prim
            kwargs["rootPrimType"] = self.root_prim_type
        if self.parent_scope:
            kwargs["parentScope"] = self.parent_scope
        return kwargs

    def run_export_command(self, export_command, export_kwargs):
        """Runs the USD export command and removes unsupported flags on retry.

        Args:
            export_command (callable): Maya USD export command.
            export_kwargs (dict): Keyword arguments for the export command.

        Raises:
            Exception: If export fails for a reason other than an unsupported flag.
        """
        export_kwargs = dict(export_kwargs or {})
        removed_flags = []
        while True:
            try:
                export_command(**export_kwargs)
                return
            except (RuntimeError, TypeError) as exception:
                invalid_flag = self.get_invalid_export_flag(exception)
                if not invalid_flag or invalid_flag not in export_kwargs or invalid_flag in removed_flags:
                    raise
                removed_flags.append(invalid_flag)
                export_kwargs.pop(invalid_flag, None)
                logger.warning(
                    'Maya USD export command rejected unsupported flag "%s"; retrying without it.',
                    invalid_flag,
                )

    @staticmethod
    def get_invalid_export_flag(exception):
        """Gets an invalid Maya command flag name from an exception.

        Args:
            exception (Exception): Maya command exception.

        Returns:
            str: Invalid flag name, or empty string when not found.
        """
        message = str(exception)
        marker = "Invalid flag '"
        if marker not in message:
            return ""
        trailing_message = message.split(marker, 1)[-1]
        return trailing_message.split("'", 1)[0]

    def get_frame_range(self):
        """Gets the export frame range.

        Returns:
            list: Start and end frames.
        """
        if self.auto_frame_range:
            start_frame, end_frame = get_timeline_frame_range()
            return [start_frame, end_frame]
        start_frame = self.frame_start if self.frame_start not in [None, ""] else get_timeline_frame_range()[0]
        end_frame = self.frame_end if self.frame_end not in [None, ""] else get_timeline_frame_range()[1]
        return [float(start_frame), float(end_frame)]

    def get_export_roots(self):
        """Gets cleaned root nodes to export.

        Returns:
            list: Long DAG paths for root nodes.
        """
        cmds = get_maya_cmds()
        export_roots = []
        for root in self.target_roots:
            node = find_node(root)
            if node and node not in export_roots:
                export_roots.append(node)
        if not self.auto_detect_roots:
            return self.clean_nested_roots(export_roots)

        target_node = find_node(self.target_node)
        if target_node and target_node not in export_roots:
            export_roots.append(target_node)

        if self.include_joints:
            all_joints = cmds.ls(type="joint", long=True) or []
            for joint in all_joints:
                parent = cmds.listRelatives(joint, parent=True, fullPath=True)
                if parent and cmds.nodeType(parent[0]) != "joint":
                    if parent[0] not in export_roots:
                        export_roots.append(parent[0])
                elif not parent and joint not in export_roots:
                    export_roots.append(joint)

        if self.include_locators:
            for shape in cmds.ls(type="locator", long=True) or []:
                parent = cmds.listRelatives(shape, parent=True, fullPath=True)
                if parent and parent[0] not in export_roots:
                    export_roots.append(parent[0])

        if self.include_curves:
            for shape in cmds.ls(type="nurbsCurve", long=True) or []:
                parent = cmds.listRelatives(shape, parent=True, fullPath=True)
                if parent and parent[0] not in export_roots:
                    export_roots.append(parent[0])

        return self.clean_nested_roots(export_roots)

    @staticmethod
    def clean_nested_roots(root_nodes):
        """Removes roots that are children of other selected roots.

        Args:
            root_nodes (list): Root node paths.

        Returns:
            list: Cleaned root node paths.
        """
        cleaned = []
        for root_node in root_nodes:
            is_child = any(root_node.startswith(other + "|") for other in root_nodes if other != root_node)
            if not is_child and root_node not in cleaned:
                cleaned.append(root_node)
        return cleaned

    @staticmethod
    def zero_root_rotations(root_nodes):
        """Unlocks, disconnects, and zeros root rotation channels.

        Args:
            root_nodes (list): Root node paths.
        """
        cmds = get_maya_cmds()
        for root_node in root_nodes:
            for axis in ["rotateX", "rotateY", "rotateZ"]:
                if not cmds.attributeQuery(axis, node=root_node, exists=True):
                    continue
                attr_path = "{0}.{1}".format(root_node, axis)
                try:
                    cmds.setAttr(attr_path, lock=False)
                    incoming = cmds.listConnections(attr_path, source=True, destination=False, plugs=True) or []
                    for source_plug in incoming:
                        cmds.disconnectAttr(source_plug, attr_path)
                    cmds.setAttr(attr_path, 0)
                except Exception as exception:
                    logger.debug("Unable to zero root rotation %s: %s", attr_path, exception)

    def apply_native_custom_attribute_tags(self):
        """Adds MayaUSD user-exported-attribute tags to configured nodes."""
        cmds = get_maya_cmds()
        config_attr_name = "USD_UserExportedAttributesJson"
        attr_map = {}
        for item in self.native_custom_attributes:
            if "." not in item:
                continue
            node_name, attr_name = item.split(".", 1)
            attr_map.setdefault(node_name, []).append(attr_name)

        for node_name, attr_names in attr_map.items():
            node = find_node(node_name)
            if not node:
                continue
            export_config = {}
            for attr_name in attr_names:
                if cmds.attributeQuery(attr_name, node=node, exists=True):
                    export_config[attr_name] = {"usdAttrName": attr_name}
            if not export_config:
                continue
            if not cmds.attributeQuery(config_attr_name, node=node, exists=True):
                cmds.addAttr(node, longName=config_attr_name, dataType="string")
            cmds.setAttr("{0}.{1}".format(node, config_attr_name), json.dumps(export_config), type="string")

    def apply_post_custom_data(self, output_path):
        """Injects configured Maya attribute values into USD prim custom data.

        Args:
            output_path (str): Exported USD file path.
        """
        post_data = self.collect_post_custom_data()
        if not post_data:
            return
        Usd = get_pxr_usd()
        stage = Usd.Stage.Open(output_path)
        if not stage:
            raise RuntimeError("Unable to open exported USD stage for post-processing: {0}".format(output_path))
        for prim in stage.Traverse():
            prim_name = prim.GetName()
            if prim_name not in post_data:
                continue
            current_custom_data = prim.GetCustomData()
            current_custom_data.update(post_data[prim_name])
            prim.SetCustomData(current_custom_data)
        stage.Save()

    def collect_post_custom_data(self):
        """Collects configured Maya attribute values for USD custom data injection.

        Returns:
            dict: Prim short name to custom data mapping.
        """
        cmds = get_maya_cmds()
        post_data = {}
        for item in self.custom_data_attributes:
            if "." not in item:
                continue
            node_name, attr_name = item.split(".", 1)
            node = find_node(node_name)
            if not node or not cmds.attributeQuery(attr_name, node=node, exists=True):
                continue
            value = cmds.getAttr("{0}.{1}".format(node, attr_name))
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except (ValueError, TypeError):
                    pass
            post_data.setdefault(get_short_name(node), {})[attr_name] = value
        return post_data

    @staticmethod
    def get_warning_suppression_state():
        """Gets the current script-editor warning suppression state.

        Returns:
            bool: Current warning suppression state.
        """
        cmds = get_maya_cmds()
        try:
            return cmds.scriptEditorInfo(query=True, suppressWarnings=True)
        except Exception:
            return False

    @staticmethod
    def set_warning_suppression_state(state):
        """Sets script-editor warning suppression.

        Args:
            state (bool): New warning suppression state.
        """
        cmds = get_maya_cmds()
        try:
            cmds.scriptEditorInfo(suppressWarnings=bool(state))
        except Exception:
            pass


def build_export_options(settings):
    """Builds a USD exporter settings dictionary from serialized settings.

    Args:
        settings (dict): Task export settings.

    Returns:
        dict: Keyword arguments accepted by UsdExporter.
    """
    settings = settings or {}
    return {
        "selection": settings.get("export_selection", True),
        "output_format": settings.get("usd_format", "usdc"),
        "static_export": settings.get("static_export", False),
        "animation": settings.get("animation", True),
        "auto_frame_range": settings.get("auto_frame_range", True),
        "frame_start": settings.get("frame_start"),
        "frame_end": settings.get("frame_end"),
        "auto_detect_roots": settings.get("auto_detect_roots", True),
        "target_roots": settings.get("target_roots") or [],
        "target_node": settings.get("target_node") or "",
        "include_joints": settings.get("include_joints", True),
        "include_locators": settings.get("include_locators", True),
        "include_curves": settings.get("include_curves", True),
        "force_z_up": settings.get("force_z_up", False),
        "zero_root_rotation": settings.get("zero_root_rotation", False),
        "export_materials": settings.get("materials", settings.get("export_materials", False)),
        "export_skeletons": settings.get("skeletons", settings.get("export_skeletons", True)),
        "export_skin": settings.get("skin", settings.get("export_skin", True)),
        "export_blend_shapes": settings.get("blend_shapes", settings.get("export_blend_shapes", True)),
        "export_color_sets": settings.get("color_sets", False),
        "export_uvs": settings.get("uvs", False),
        "export_visibility": settings.get("visibility", True),
        "strip_namespaces": settings.get("strip_namespaces", False),
        "merge_transform_and_shape": settings.get("merge_transform_and_shape", False),
        "write_defaults": settings.get("write_defaults", True),
        "ignore_warnings": settings.get("ignore_warnings", True),
        "default_prim": settings.get("default_prim") or "",
        "root_prim": settings.get("root_prim") or "",
        "root_prim_type": settings.get("root_prim_type") or "Scope",
        "parent_scope": settings.get("parent_scope") or "",
        "native_custom_attributes": settings.get("native_custom_attributes", []),
        "custom_data_attributes": settings.get("custom_data_attributes", []),
    }


def export_scene_to_usd(output_path, settings=None):
    """Exports the current Maya scene to USD.

    Args:
        output_path (str): Destination USD file path.
        settings (dict, optional): Export settings.

    Returns:
        str: Exported USD file path.
    """
    with UsdExporter(**build_export_options(settings)) as exporter:
        return exporter.export_file(path=output_path)
