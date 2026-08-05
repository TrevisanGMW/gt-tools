"""
Renamer Model
"""

import copy
import logging
import random
import sys


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


SCRIPT_NAME = "Renamer"
ERROR_MESSAGE = "Some objects were not renamed. Open the script editor to see why."

SELECTION_SELECTED = "Selected"
SELECTION_HIERARCHY = "Hierarchy"
SELECTION_ALL = "All"
SELECTION_OPTIONS = [SELECTION_SELECTED, SELECTION_HIERARCHY, SELECTION_ALL]

OP_REMOVE_FIRST = "remove_first_letter"
OP_REMOVE_LAST = "remove_last_letter"
OP_UPPERCASE = "uppercase_names"
OP_CAPITALIZE = "capitalize_names"
OP_LOWERCASE = "lowercase_names"
OP_RENAME_NUMBER = "rename_and_number"
OP_RENAME_LETTER = "rename_and_letter"
OP_ADD_PREFIX = "add_prefix"
OP_ADD_SUFFIX = "add_suffix"
OP_SEARCH_REPLACE = "search_and_replace"

DEFAULT_SETTINGS = {
    "transform_suffix": "_grp",
    "mesh_suffix": "_geo",
    "nurbs_crv_suffix": "_crv",
    "joint_suffix": "_jnt",
    "locator_suffix": "_loc",
    "surface_suffix": "_sur",
    "left_prefix": "left_",
    "right_prefix": "right_",
    "center_prefix": "center_",
    "def_starting_number": "1",
    "def_padding_number": "2",
    "def_uppercase_letter": "1",
    "selection_type": SELECTION_SELECTED,
}

OPTION_VAR_MAP = {
    "transform_suffix": "gt_renamer_transform_suffix",
    "mesh_suffix": "gt_renamer_mesh_suffix",
    "nurbs_crv_suffix": "gt_renamer_nurbs_curve_suffix",
    "joint_suffix": "gt_renamer_joint_suffix",
    "locator_suffix": "gt_renamer_locator_suffix",
    "surface_suffix": "gt_renamer_surface_suffix",
    "left_prefix": "gt_renamer_left_prefix",
    "right_prefix": "gt_renamer_right_prefix",
    "center_prefix": "gt_renamer_center_prefix",
    "def_starting_number": "gt_renamer_def_starting_number",
    "def_padding_number": "gt_renamer_def_padding_number",
    "def_uppercase_letter": "gt_renamer_def_uppercase_letter",
    "selection_type": "gt_renamer_selection_type",
}

NODES_TO_IGNORE = [
    "defaultRenderLayer",
    "renderLayerManager",
    "defaultLayer",
    "layerManager",
    "poseInterpolatorManager",
    "shapeEditorManager",
    "side",
    "front",
    "top",
    "persp",
    "lightLinker1",
    "strokeGlobals",
    "globalCacheControl",
    "hyperGraphLayout",
    "hyperGraphInfo",
    "ikSystem",
    "defaultHardwareRenderGlobals",
    "characterPartition",
    "hardwareRenderGlobals",
    "defaultColorMgtGlobals",
    "defaultViewColorManager",
    "defaultObjectSet",
    "defaultLightSet",
    "defaultResolution",
    "defaultRenderQuality",
    "defaultRenderGlobals",
    "dof1",
    "shaderGlow1",
    "initialMaterialInfo",
    "initialParticleSE",
    "initialShadingGroup",
    "particleCloud1",
    "standardSurface1",
    "lambert1",
    "defaultTextureList1",
    "lightList1",
    "defaultRenderingList1",
    "defaultRenderUtilityList1",
    "postProcessList1",
    "defaultShaderList1",
    "defaultLightList1",
    "renderGlobalsList1",
    "renderPartition",
    "hardwareRenderingGlobals",
    "sequenceManager1",
    "time1",
]

NODE_TYPES_TO_IGNORE = [
    "objectRenderFilter",
    "objectTypeFilter",
    "dynController",
    "objectMultiFilter",
    "selectionListOperator",
]


def get_maya_cmds():
    """Imports Maya commands lazily.

    Returns:
        module: Maya commands module.
    """
    try:
        import maya.cmds as cmds
    except ImportError:
        raise RuntimeError("Maya commands are not available.")
    return cmds


def string_replace(string, search, replace):
    """Replaces a substring inside a string.

    Args:
        string (str): String to process.
        search (str): Text to search for.
        replace (str): Replacement text.

    Returns:
        str: Processed string.
    """
    if string == "":
        return ""
    return string.replace(search, replace)


def get_short_name(obj):
    """Gets the short object name without a DAG path.

    Args:
        obj (str): Object name.

    Returns:
        str: Short object name.
    """
    if obj == "":
        return ""
    split_path = str(obj).split("|")
    if split_path:
        return split_path[-1]
    return ""


def normalize_selection_type(selection_type):
    """Normalizes a selection type string.

    Args:
        selection_type (str): Selection type.

    Returns:
        str: Normalized selection type.
    """
    if selection_type in SELECTION_OPTIONS:
        return selection_type
    return SELECTION_SELECTED


def increment_letter_suffix(suffix):
    """Increments an alphabetical suffix.

    Args:
        suffix (str): Current suffix.

    Returns:
        str: Next suffix.
    """
    if not suffix:
        return "A"
    left_part = suffix.rstrip("Z")
    replacement_count = len(suffix) - len(left_part)
    if left_part:
        next_suffix = left_part[:-1] + chr(ord(left_part[-1]) + 1)
    else:
        next_suffix = "A"
    return next_suffix + ("A" * replacement_count)


class RenamerModel:
    """Stores Renamer settings and executes Maya rename operations."""

    def __init__(self):
        """Initializes the renamer model."""
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        self.nodes_to_ignore = list(NODES_TO_IGNORE)
        self.node_types_to_ignore = list(NODE_TYPES_TO_IGNORE)
        self.load_preferences()

    def load_preferences(self):
        """Loads persistent Maya optionVar preferences."""
        try:
            cmds = get_maya_cmds()
        except RuntimeError:
            return
        for setting_key, option_var in OPTION_VAR_MAP.items():
            if not cmds.optionVar(exists=option_var):
                continue
            value = str(cmds.optionVar(q=option_var))
            if setting_key == "def_uppercase_letter":
                value = "0" if "False" in value or value == "0" else "1"
            if setting_key == "selection_type":
                value = normalize_selection_type(value)
            self.settings[setting_key] = value

    def save_setting(self, setting_key, setting_value):
        """Saves one persistent Maya optionVar preference.

        Args:
            setting_key (str): Settings dictionary key.
            setting_value (str): Value to save.
        """
        self.settings[setting_key] = str(setting_value)
        option_var = OPTION_VAR_MAP.get(setting_key)
        if not option_var:
            return
        try:
            cmds = get_maya_cmds()
        except RuntimeError:
            return
        cmds.optionVar(sv=(str(option_var), str(setting_value)))

    def reset_preferences(self):
        """Clears persistent Maya optionVars and restores defaults."""
        try:
            cmds = get_maya_cmds()
        except RuntimeError:
            self.settings = copy.deepcopy(DEFAULT_SETTINGS)
            return
        for option_var in OPTION_VAR_MAP.values():
            if cmds.optionVar(exists=option_var):
                cmds.optionVar(remove=option_var)
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        sys.stdout.write("Persistent settings for {0} were cleared.\n".format(SCRIPT_NAME))

    def set_selection_type(self, selection_type):
        """Sets and saves the active selection type.

        Args:
            selection_type (str): Selection type.
        """
        self.save_setting("selection_type", normalize_selection_type(selection_type))

    def get_target_objects(self):
        """Gets the objects affected by the current selection type.

        Returns:
            list: Target object names.
        """
        cmds = get_maya_cmds()
        selection_type = normalize_selection_type(self.settings.get("selection_type"))
        current_selection = cmds.ls(selection=True) or []
        if selection_type == SELECTION_SELECTED:
            return current_selection
        if selection_type == SELECTION_HIERARCHY:
            if current_selection:
                cmds.select(current_selection, replace=True)
                cmds.select(hierarchy=True)
            target_objects = cmds.ls(selection=True) or []
            cmds.select(current_selection, replace=True)
            return target_objects
        target_objects = cmds.ls() or []
        return self.filter_scene_objects(target_objects)

    def filter_scene_objects(self, objects):
        """Filters scene objects for the All selection mode.

        Args:
            objects (list): Object names.

        Returns:
            list: Filtered object names.
        """
        cmds = get_maya_cmds()
        filtered_objects = list(objects or [])
        for node in self.nodes_to_ignore:
            if node in filtered_objects and cmds.objExists(node):
                filtered_objects.remove(node)
        for node_type in self.node_types_to_ignore:
            for undesired_node in cmds.ls(type=node_type) or []:
                if undesired_node in filtered_objects:
                    filtered_objects.remove(undesired_node)
        return filtered_objects

    def is_renamable_node(self, obj):
        """Checks whether an object should be renamed.

        Args:
            obj (str): Object name.

        Returns:
            bool: True if the object can be renamed by this tool.
        """
        cmds = get_maya_cmds()
        if not cmds.objExists(obj):
            return False
        inherited_types = cmds.nodeType(obj, inherited=True) or []
        return "shape" not in inherited_types

    def run_operation(self, operation, **kwargs):
        """Runs one renaming operation on the configured target objects.

        Args:
            operation (str): Operation name.
            **kwargs: Operation arguments.

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        selection = self.get_target_objects()
        if not selection:
            cmds.warning("Nothing is selected!")
            return 0
        cmds.undoInfo(openChunk=True, chunkName=SCRIPT_NAME)
        try:
            return self.run_operation_on_objects(selection, operation, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=SCRIPT_NAME)

    def run_operation_on_objects(self, objects, operation, **kwargs):
        """Runs one renaming operation on explicit objects.

        Args:
            objects (list): Object names.
            operation (str): Operation name.
            **kwargs: Operation arguments.

        Returns:
            int: Number of queued rename operations.
        """
        if operation == OP_SEARCH_REPLACE:
            return self.rename_search_replace(objects, kwargs.get("search", ""), kwargs.get("replace", ""))
        if operation == OP_RENAME_NUMBER:
            return self.rename_and_number(
                objects,
                kwargs.get("new_name", ""),
                kwargs.get("start_number", 1),
                kwargs.get("padding_number", 2),
                keep_name=kwargs.get("keep_name", False),
            )
        if operation == OP_RENAME_LETTER:
            return self.rename_and_letter(
                objects,
                kwargs.get("new_name", ""),
                is_uppercase=kwargs.get("is_uppercase", True),
                keep_name=kwargs.get("keep_name", False),
            )
        if operation == OP_ADD_PREFIX:
            return self.rename_add_prefix(
                objects,
                kwargs.get("prefix_list") or [kwargs.get("prefix", "")],
            )
        if operation == OP_ADD_SUFFIX:
            return self.rename_add_suffix(
                objects,
                kwargs.get("suffix_list") or [kwargs.get("suffix", "")],
            )
        if operation == OP_REMOVE_FIRST:
            return self.remove_first_letter(objects)
        if operation == OP_REMOVE_LAST:
            return self.remove_last_letter(objects)
        if operation == OP_UPPERCASE:
            return self.rename_case(objects, "upper")
        if operation == OP_CAPITALIZE:
            return self.rename_case(objects, "capitalize")
        if operation == OP_LOWERCASE:
            return self.rename_case(objects, "lower")
        return 0

    def rename_case(self, objects, case_mode):
        """Renames objects using a case operation.

        Args:
            objects (list): Object names.
            case_mode (str): Case mode. Supported: upper, lower, capitalize.

        Returns:
            int: Number of queued rename operations.
        """
        rename_pairs = []
        for obj in objects:
            object_short_name = get_short_name(obj)
            if case_mode == "upper":
                new_name = object_short_name.upper()
            elif case_mode == "lower":
                new_name = object_short_name.lower()
            else:
                name_parts = object_short_name.split("_")
                if len(name_parts) > 1:
                    new_name = "_".join([name.capitalize() for name in name_parts])
                else:
                    new_name = object_short_name.capitalize()
            if self.is_renamable_node(obj) and obj != new_name:
                rename_pairs.append([obj, new_name])
        return self.apply_rename_pairs(rename_pairs)

    def remove_first_letter(self, objects):
        """Removes the first letter from object names.

        Args:
            objects (list): Object names.

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        rename_pairs = []
        for obj in objects:
            object_short_name = get_short_name(obj)
            if len(object_short_name) <= 1:
                cmds.warning('"{0}" is just one letter. You can\'t remove it.'.format(object_short_name))
                continue
            if self.is_renamable_node(obj):
                rename_pairs.append([obj, object_short_name[1:]])
        return self.apply_rename_pairs(rename_pairs)

    def remove_last_letter(self, objects):
        """Removes the last letter from object names.

        Args:
            objects (list): Object names.

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        rename_pairs = []
        for obj in objects:
            object_short_name = get_short_name(obj)
            if len(object_short_name) <= 1:
                cmds.warning('"{0}" is just one letter. You can\'t remove it.'.format(object_short_name))
                continue
            if self.is_renamable_node(obj):
                rename_pairs.append([obj, object_short_name[:-1]])
        return self.apply_rename_pairs(rename_pairs)

    def rename_search_replace(self, objects, search, replace):
        """Renames objects using search and replace.

        Args:
            objects (list): Object names.
            search (str): Search text.
            replace (str): Replacement text.

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        if search == "":
            cmds.warning("The search string must not be empty.")
            return 0
        rename_pairs = []
        for obj in objects:
            object_short_name = get_short_name(obj)
            new_name = string_replace(str(object_short_name), search, replace)
            if self.is_renamable_node(obj) and obj != new_name:
                rename_pairs.append([obj, new_name])
        return self.apply_rename_pairs(rename_pairs)

    def rename_and_number(self, objects, new_name, start_number, padding_number, keep_name=False):
        """Renames objects and adds a padded number.

        Args:
            objects (list): Object names.
            new_name (str): Base name.
            start_number (int): First number.
            padding_number (int): Padding width.
            keep_name (bool, optional): Whether to keep source names as the base.

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        if not new_name and not keep_name:
            cmds.warning("The provided string must not be empty.")
            return 0
        rename_pairs = []
        count = int(start_number)
        padding_number = int(padding_number)
        for obj in objects:
            object_short_name = get_short_name(obj)
            base_name = object_short_name if keep_name else new_name
            new_name_and_number = base_name + str(count).zfill(padding_number)
            if self.is_renamable_node(obj):
                rename_pairs.append([obj, new_name_and_number])
                count += 1
        return self.apply_rename_pairs(rename_pairs)

    def rename_and_letter(self, objects, new_name, is_uppercase=True, keep_name=False):
        """Renames objects and adds an alphabetical suffix.

        Args:
            objects (list): Object names.
            new_name (str): Base name.
            is_uppercase (bool, optional): Whether the suffix is uppercase.
            keep_name (bool, optional): Whether to keep source names as the base.

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        if not new_name and not keep_name:
            cmds.warning("The provided string must not be empty.")
            return 0
        rename_pairs = []
        current_suffix = "A"
        for obj in objects:
            object_short_name = get_short_name(obj)
            base_name = object_short_name if keep_name else new_name
            suffix = current_suffix if is_uppercase else current_suffix.lower()
            if self.is_renamable_node(obj):
                rename_pairs.append([obj, base_name + suffix])
                current_suffix = increment_letter_suffix(current_suffix)
        return self.apply_rename_pairs(rename_pairs)

    def rename_add_prefix(self, objects, prefix_list):
        """Adds a prefix to object names.

        Args:
            objects (list): Object names.
            prefix_list (list): One manual prefix or three auto prefixes.

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        auto_prefix = len(prefix_list) != 1
        manual_prefix = prefix_list[0] if prefix_list else ""
        if not auto_prefix and manual_prefix == "":
            cmds.warning("Prefix Input must not be empty.")
            return 0
        rename_pairs = []
        for obj in objects:
            if auto_prefix and self.is_renamable_node(obj):
                new_prefix = self.get_auto_prefix(obj, prefix_list)
            else:
                new_prefix = manual_prefix if not auto_prefix else ""
            object_short_name = get_short_name(obj)
            if object_short_name.startswith(new_prefix):
                new_name = object_short_name
            else:
                new_name = new_prefix + object_short_name
            if self.is_renamable_node(obj) and obj != new_name:
                rename_pairs.append([obj, new_name])
        return self.apply_rename_pairs(rename_pairs)

    def get_auto_prefix(self, obj, prefix_list):
        """Gets the automatic prefix for an object using its world X position.

        Args:
            obj (str): Object name.
            prefix_list (list): Left, center, and right prefixes.

        Returns:
            str: Prefix string.
        """
        cmds = get_maya_cmds()
        if len(prefix_list) < 3:
            return ""
        try:
            obj_x_pos = cmds.xform(obj, piv=True, q=True, ws=True)[0]
        except Exception as exception:
            logger.debug(str(exception))
            return ""
        if obj_x_pos > 0.0001:
            return prefix_list[0]
        if obj_x_pos < -0.0001:
            return prefix_list[2]
        return prefix_list[1]

    def rename_add_suffix(self, objects, suffix_list):
        """Adds a suffix to object names.

        Args:
            objects (list): Object names.
            suffix_list (list): One manual suffix or six auto suffixes.

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        auto_suffix = len(suffix_list) != 1
        manual_suffix = suffix_list[0] if suffix_list else ""
        if not auto_suffix and manual_suffix == "":
            cmds.warning("Suffix Input must not be empty.")
            return 0
        rename_pairs = []
        for obj in objects:
            if auto_suffix and self.is_renamable_node(obj):
                new_suffix = self.get_auto_suffix(obj, suffix_list)
            else:
                new_suffix = manual_suffix if not auto_suffix else ""
            object_short_name = get_short_name(obj)
            if object_short_name.endswith(new_suffix):
                new_name = object_short_name
            else:
                new_name = object_short_name + new_suffix
            if self.is_renamable_node(obj) and obj != new_name:
                rename_pairs.append([obj, new_name])
        return self.apply_rename_pairs(rename_pairs)

    def get_auto_suffix(self, obj, suffix_list):
        """Gets the automatic suffix for an object using its type.

        Args:
            obj (str): Object name.
            suffix_list (list): Group, mesh, curve, joint, locator, and surface suffixes.

        Returns:
            str: Suffix string.
        """
        cmds = get_maya_cmds()
        if len(suffix_list) < 6:
            return ""
        object_shape = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
        if object_shape:
            object_type = cmds.objectType(object_shape[0])
        else:
            object_type = cmds.objectType(obj)
        type_to_suffix = {
            "transform": suffix_list[0],
            "mesh": suffix_list[1],
            "nurbsCurve": suffix_list[2],
            "joint": suffix_list[3],
            "locator": suffix_list[4],
            "nurbsSurface": suffix_list[5],
        }
        return type_to_suffix.get(object_type, "")

    def apply_rename_pairs(self, rename_pairs):
        """Applies rename pairs in reverse order.

        Args:
            rename_pairs (list): Pairs in the format [old_name, new_name].

        Returns:
            int: Number of queued rename operations.
        """
        cmds = get_maya_cmds()
        errors = ""
        for old_name, new_name in reversed(rename_pairs):
            if not cmds.objExists(old_name):
                continue
            try:
                cmds.rename(old_name, new_name)
            except Exception as exception:
                errors += '"{0}" : "{1}".\n'.format(old_name, str(exception).rstrip("\n"))
        if errors:
            print("#" * 80 + "\n")
            print(errors)
            print("#" * 80)
            cmds.warning(ERROR_MESSAGE)
        self.renaming_inview_feedback(len(rename_pairs))
        return len(rename_pairs)

    @staticmethod
    def renaming_inview_feedback(number_of_renames):
        """Shows an in-view rename count message.

        Args:
            number_of_renames (int): Rename count.
        """
        if number_of_renames == 0:
            return
        cmds = get_maya_cmds()
        message = (
            "<{0}><span style=\"color:#FF0000;text-decoration:underline;\">{1}</span>"
            "<span style=\"color:#FFFFFF;\"> {2} renamed.</span>"
        ).format(
            str(random.random()),
            str(number_of_renames),
            "object was" if number_of_renames == 1 else "objects were",
        )
        cmds.inViewMessage(amg=message, pos="botLeft", fade=True, alpha=0.9)
