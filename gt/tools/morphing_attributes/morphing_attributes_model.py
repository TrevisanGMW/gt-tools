"""
Morphing Attributes Model

Holds tool state, pure filtering helpers, and the Maya runtime logic used to
create or delete morphing (blend shape) driver attributes on a control object.

Maya imports are kept lazy so this module remains importable outside of Maya.
"""

import copy
import logging
import random
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Identity
SCRIPT_NAME = "Add Morphing Attributes"

# Filter Methods
METHOD_INCLUDES = "includes"
METHOD_STARTS_WITH = "startswith"
METHOD_ENDS_WITH = "endswith"

# Filter Method Labels (user-facing, mapped back to methods above)
FILTER_METHOD_LABELS = ["Includes", "Starts With", "Ends With"]

# Node naming used to identify/remove remap nodes created by this tool
REMAP_MORPHING_PREFIX = "remap_morphing_"
SEPARATOR_ATTR_NAME = "blends"

# Default settings used when building the model
DEFAULT_SETTINGS = {
    "desired_filter_string": "",
    "undesired_filter_string": "",
    "desired_filter_type": METHOD_INCLUDES,
    "undesired_filter_type": METHOD_INCLUDES,
    "ignore_case": True,
    "modify_range": True,
    "new_range_min": 0,
    "new_range_max": 10,
    "old_range_min": 0,
    "old_range_max": 1,
    "ignore_connected": True,
    "add_separator": True,
    "sort_attr": True,
    "delete_instead": False,
}


def get_maya_cmds():
    """Imports Maya commands lazily so this module stays importable outside Maya.

    Returns:
        module: The "maya.cmds" module.
    """
    try:
        import maya.cmds as cmds
    except ImportError:
        raise RuntimeError("Maya commands are not available.")
    return cmds


def method_from_label(label):
    """Converts a user-facing filter label into its internal method string.

    Args:
        label (str): User-facing label such as "Starts With".

    Returns:
        str: Internal method string such as "startswith".
    """
    return str(label).replace(" ", "").lower()


def parse_filter_string(filter_string):
    """Splits a comma separated filter string into a clean list of tokens.

    Args:
        filter_string (str): Raw comma separated filter text.

    Returns:
        list: List of non-empty filter tokens with surrounding spaces removed.
    """
    if not filter_string:
        return []
    tokens = [token.strip() for token in str(filter_string).split(",")]
    return [token for token in tokens if token]


def target_matches_filter(target_name, filter_string, method, ignore_case):
    """Checks whether a single target name matches a single filter token.

    Args:
        target_name (str): Blend shape target name being tested.
        filter_string (str): Filter token to compare against.
        method (str): Comparison method ("includes", "startswith" or "endswith").
        ignore_case (bool): Whether the comparison should be case-insensitive.

    Returns:
        bool: True when the target matches the filter using the given method.
    """
    compare_target = target_name
    compare_filter = filter_string
    if ignore_case:
        compare_target = compare_target.lower()
        compare_filter = compare_filter.lower()
    if method == METHOD_INCLUDES:
        return compare_filter in compare_target
    if method == METHOD_STARTS_WITH:
        return compare_target.startswith(compare_filter)
    if method == METHOD_ENDS_WITH:
        return compare_target.endswith(compare_filter)
    return False


def filter_desired_targets(targets, desired_strings, method, ignore_case):
    """Filters targets down to those matching any desired filter token.

    When no desired tokens are provided every target is considered desired.

    Args:
        targets (list): List of blend shape target names.
        desired_strings (list): Desired filter tokens.
        method (str): Comparison method for desired tokens.
        ignore_case (bool): Whether the comparison should be case-insensitive.

    Returns:
        list: Desired targets, preserving order and without duplicates.
    """
    if not desired_strings:
        return list(targets)
    filtered = []
    for target in targets:
        if target in filtered:
            continue
        for filter_string in desired_strings:
            if target_matches_filter(target, filter_string, method, ignore_case):
                filtered.append(target)
                break
    return filtered


def filter_undesired_targets(targets, undesired_strings, method, ignore_case):
    """Removes targets that match any undesired filter token.

    Args:
        targets (list): List of blend shape target names.
        undesired_strings (list): Undesired filter tokens.
        method (str): Comparison method for undesired tokens.
        ignore_case (bool): Whether the comparison should be case-insensitive.

    Returns:
        list: Targets that do not match any undesired token, order preserved.
    """
    if not undesired_strings:
        return list(targets)
    result = []
    for target in targets:
        is_undesired = False
        for filter_string in undesired_strings:
            if target_matches_filter(target, filter_string, method, ignore_case):
                is_undesired = True
                break
        if not is_undesired:
            result.append(target)
    return result


class MorphingAttributesModel:
    """Stores morphing attribute settings and runs the Maya scene operations."""

    def __init__(self):
        """Initializes the model with default settings and empty object slots."""
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        self.morphing_obj = ""
        self.blend_node = ""
        self.attr_holder = ""

    # ------------------------------------------------------------------ Settings
    def set_setting(self, key, value):
        """Sets a single setting value.

        Args:
            key (str): Settings dictionary key.
            value: Value to store for the given key.
        """
        self.settings[key] = value

    def get_setting(self, key):
        """Gets a single setting value.

        Args:
            key (str): Settings dictionary key.

        Returns:
            The stored value for the given key, or None when missing.
        """
        return self.settings.get(key)

    # ------------------------------------------------------------- Maya Queries
    @staticmethod
    def object_exists(obj):
        """Checks whether an object currently exists in the scene.

        Args:
            obj (str): Object name to test.

        Returns:
            bool: True when the object exists, False otherwise.
        """
        if not obj:
            return False
        cmds = get_maya_cmds()
        return bool(cmds.objExists(obj))

    @staticmethod
    def get_selection():
        """Gets the current Maya selection.

        Returns:
            list: List of currently selected object names.
        """
        cmds = get_maya_cmds()
        return cmds.ls(selection=True) or []

    @staticmethod
    def find_blend_shape_nodes(mesh):
        """Finds blend shape nodes in the history of the provided mesh.

        Args:
            mesh (str): Mesh (or transform) to inspect.

        Returns:
            list: Blend shape node names found in the mesh history.
        """
        cmds = get_maya_cmds()
        history = cmds.listHistory(mesh) or []
        return cmds.ls(history, type="blendShape") or []

    @staticmethod
    def list_target_names(blend_node):
        """Lists the morphing target names available on a blend shape node.

        Args:
            blend_node (str): Blend shape node name.

        Returns:
            list: Target (weight) attribute names on the blend shape node.
        """
        cmds = get_maya_cmds()
        return cmds.listAttr(blend_node + ".w", m=True) or []

    def select_object(self, obj):
        """Selects an object in the scene and provides in-view feedback.

        Args:
            obj (str): Object to select.

        Returns:
            bool: True when the object was selected, False otherwise.
        """
        cmds = get_maya_cmds()
        if not obj:
            cmds.warning("Nothing loaded. Please load an object before attempting to select it.")
            return False
        if not cmds.objExists(obj):
            cmds.warning(
                '"{0}" couldn\'t be selected. Make sure you didn\'t rename or delete '
                "the object after loading it.".format(obj)
            )
            return False
        cmds.select(obj)
        message = '<{0}><span style="color:#FF0000;text-decoration:underline;">{1}</span>'.format(
            str(random.random()), str(obj)
        )
        message += '<span style="color:#FFFFFF;"> selected.</span>'
        cmds.inViewMessage(amg=message, pos="botLeft", fade=True, alpha=0.9)
        return True

    # ---------------------------------------------------------------- Execution
    def run(self):
        """Validates the current state and creates or deletes morphing attributes.

        Returns:
            list: Names of the attributes that were created/connected or deleted.
                  Returns an empty list when validation fails or nothing changed.
        """
        cmds = get_maya_cmds()

        if not self.attr_holder or not cmds.objExists(self.attr_holder):
            cmds.warning("Missing attribute holder. Make sure you loaded an object and try again.")
            return []
        if not self.blend_node or not cmds.objExists(self.blend_node):
            cmds.warning("Select a blend shape node to be used as source.")
            return []

        desired_strings = parse_filter_string(self.settings.get("desired_filter_string"))
        undesired_strings = parse_filter_string(self.settings.get("undesired_filter_string"))

        current_selection = cmds.ls(selection=True)
        cmds.undoInfo(openChunk=True, chunkName=SCRIPT_NAME)
        try:
            affected_attributes = self.apply_morphing_attributes(desired_strings, undesired_strings)
            self.show_result_feedback(affected_attributes, bool(self.settings.get("delete_instead")))
            return affected_attributes
        except Exception as exception:
            logger.debug(str(exception))
            return []
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=SCRIPT_NAME)
            if current_selection:
                cmds.select(current_selection)

    def resolve_targets(self, all_targets, desired_strings, undesired_strings, current_attributes):
        """Resolves the final list of targets to operate on.

        Args:
            all_targets (list): Every target available on the blend shape node.
            desired_strings (list): Desired filter tokens.
            undesired_strings (list): Undesired filter tokens.
            current_attributes (list): User-defined attributes already on the holder.

        Returns:
            list: Targets that should be created/connected or deleted.
        """
        cmds = get_maya_cmds()
        method_desired = self.settings.get("desired_filter_type")
        method_undesired = self.settings.get("undesired_filter_type")
        ignore_case = self.settings.get("ignore_case")
        ignore_connected = self.settings.get("ignore_connected")
        delete_instead = self.settings.get("delete_instead")

        filtered = filter_desired_targets(all_targets, desired_strings, method_desired, ignore_case)

        if ignore_connected and not delete_instead:
            accessible = []
            for target in filtered:
                connections = (
                    cmds.listConnections(self.blend_node + "." + target, destination=False, plugs=True) or []
                )
                if not connections:
                    accessible.append(target)
        else:
            accessible = filtered

        return filter_undesired_targets(accessible, undesired_strings, method_undesired, ignore_case)

    def apply_morphing_attributes(self, desired_strings, undesired_strings):
        """Creates or deletes morphing driver attributes on the attribute holder.

        Args:
            desired_strings (list): Desired filter tokens.
            undesired_strings (list): Undesired filter tokens.

        Returns:
            list: Names of created/connected attributes, or deleted attribute plugs.
        """
        cmds = get_maya_cmds()
        delete_instead = self.settings.get("delete_instead")
        add_separator = self.settings.get("add_separator")
        sort_attr = self.settings.get("sort_attr")
        modify_range = self.settings.get("modify_range")
        old_min = self.settings.get("old_range_min")
        old_max = self.settings.get("old_range_max")
        new_min = self.settings.get("new_range_min")
        new_max = self.settings.get("new_range_max")

        all_targets = self.list_target_names(self.blend_node)
        current_attributes = cmds.listAttr(self.attr_holder, userDefined=True) or []
        target_list = self.resolve_targets(all_targets, desired_strings, undesired_strings, current_attributes)

        if delete_instead:
            return self.delete_target_attributes(target_list, current_attributes)

        # Separator Attribute
        if target_list and add_separator and SEPARATOR_ATTR_NAME not in current_attributes:
            cmds.addAttr(self.attr_holder, ln=SEPARATOR_ATTR_NAME, at="enum", en="-------------:", keyable=True)
            cmds.setAttr(self.attr_holder + "." + SEPARATOR_ATTR_NAME, e=True, lock=True)

        if sort_attr:
            target_list = sorted(target_list)

        for target in target_list:
            if modify_range:
                self.create_remapped_attribute(target, current_attributes, old_min, old_max, new_min, new_max)
            else:
                self.create_direct_attribute(target, current_attributes)
        return target_list

    def create_remapped_attribute(self, target, current_attributes, old_min, old_max, new_min, new_max):
        """Creates a driver attribute connected through a remapValue node.

        Args:
            target (str): Blend shape target name.
            current_attributes (list): Attributes already present on the holder.
            old_min (float): Original range minimum (blend shape side).
            old_max (float): Original range maximum (blend shape side).
            new_min (float): New range minimum (attribute side).
            new_max (float): New range maximum (attribute side).
        """
        cmds = get_maya_cmds()
        if target not in current_attributes:
            cmds.addAttr(self.attr_holder, ln=target, at="double", k=True, maxValue=new_max, minValue=new_min)
        else:
            cmds.warning(
                '"{0}" already existed on attribute holder. '
                "Please check if no previous connections were lost.".format(target)
            )
        remap_node = cmds.createNode("remapValue", name=REMAP_MORPHING_PREFIX + target)
        cmds.setAttr(remap_node + ".inputMax", new_max)
        cmds.setAttr(remap_node + ".inputMin", new_min)
        cmds.setAttr(remap_node + ".outputMax", old_max)
        cmds.setAttr(remap_node + ".outputMin", old_min)
        cmds.connectAttr(self.attr_holder + "." + target, remap_node + ".inputValue")
        cmds.connectAttr(remap_node + ".outValue", self.blend_node + "." + target, force=True)

    def create_direct_attribute(self, target, current_attributes):
        """Creates a driver attribute connected directly to the blend shape target.

        Args:
            target (str): Blend shape target name.
            current_attributes (list): Attributes already present on the holder.
        """
        cmds = get_maya_cmds()
        if target not in current_attributes:
            cmds.addAttr(self.attr_holder, ln=target, at="double", k=True, maxValue=1, minValue=0)
        else:
            cmds.warning(
                '"{0}" already existed on attribute holder. '
                "Please check if no previous connections were lost.".format(target)
            )
        cmds.connectAttr(self.attr_holder + "." + target, self.blend_node + "." + target, force=True)

    def delete_target_attributes(self, target_list, current_attributes):
        """Deletes driver attributes (and their remap nodes) from the holder.

        Args:
            target_list (list): Targets to remove from the attribute holder.
            current_attributes (list): Attributes already present on the holder.

        Returns:
            list: Names of the attribute plugs that were deleted.
        """
        cmds = get_maya_cmds()
        deleted_attributes = []
        for target in target_list:
            if target not in current_attributes:
                continue
            if cmds.getAttr(self.attr_holder + "." + target, lock=True):
                continue
            connections = cmds.listConnections(self.attr_holder + "." + target, source=True) or []
            if (
                connections
                and cmds.objectType(connections[0]) == "remapValue"
                and str(connections[0]).startswith(REMAP_MORPHING_PREFIX)
            ):
                cmds.delete(connections[0])
            cmds.deleteAttr(self.attr_holder + "." + target)
            deleted_attributes.append(self.attr_holder + "." + target)

        separator_plug = self.attr_holder + "." + SEPARATOR_ATTR_NAME
        if SEPARATOR_ATTR_NAME in current_attributes:
            try:
                cmds.setAttr(separator_plug, e=True, lock=False)
                cmds.deleteAttr(separator_plug)
                deleted_attributes.append(separator_plug)
            except Exception as exception:
                logger.debug(str(exception))
        return deleted_attributes

    @staticmethod
    def show_result_feedback(affected_attributes, delete_instead):
        """Prints and shows an in-view message summarizing the operation result.

        Args:
            affected_attributes (list): Attributes that were created/connected or deleted.
            delete_instead (bool): Whether the operation deleted attributes.
        """
        cmds = get_maya_cmds()
        count = len(affected_attributes)
        if not count:
            if delete_instead:
                sys.stdout.write("No attributes were deleted. Review your settings and try again.\n")
            else:
                sys.stdout.write("No attributes were created. Review your settings and try again.\n")
            return
        is_plural = "morphing attribute was" if count == 1 else "morphing attributes were"
        operation_message = " deleted." if delete_instead else " created/connected."
        message = '<{0}><span style="color:#FF0000;text-decoration:underline;">{1} </span>'.format(
            str(random.random()), str(count)
        )
        message += is_plural + operation_message
        cmds.inViewMessage(amg=message, pos="botLeft", fade=True, alpha=0.9)
        sys.stdout.write("{0} {1}{2}\n".format(str(count), is_plural, operation_message))


if __name__ == "__main__":
    print('Run it from "__init__.py".')
