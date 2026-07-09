"""
Selection Manager Model
"""

import logging
import os
import random
import sys


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


PREFS_FILENAME = "selection_manager"
PREFS_KEY_STATE = "state"

UI_MODE_MINIMAL = "Minimal"
UI_MODE_DEFAULT = "Default"
UI_MODE_COMPLETE = "Complete"
UI_MODES = [UI_MODE_MINIMAL, UI_MODE_DEFAULT, UI_MODE_COMPLETE]

SHAPE_BEHAVIOR_BOTH = "Transforms and Shapes"
SHAPE_BEHAVIOR_SHAPES = "Shape Nodes"
SHAPE_BEHAVIOR_PARENT = "Transforms From Shapes"
SHAPE_BEHAVIOR_IGNORE = "Transforms Only"
SHAPE_BEHAVIOR_OPTIONS = [
    SHAPE_BEHAVIOR_BOTH,
    SHAPE_BEHAVIOR_SHAPES,
    SHAPE_BEHAVIOR_PARENT,
    SHAPE_BEHAVIOR_IGNORE,
]
LEGACY_SHAPE_BEHAVIOR_MAP = {
    "Select Both Parent and Shape": SHAPE_BEHAVIOR_BOTH,
    "Select Shapes as Objects": SHAPE_BEHAVIOR_SHAPES,
    "Select Parent Instead": SHAPE_BEHAVIOR_PARENT,
    "Ignore Shape Nodes": SHAPE_BEHAVIOR_IGNORE,
}


class SelectionManagerModel:
    """Stores Selection Manager state and executes Maya selection operations."""

    def __init__(self):
        """Initializes the selection manager model."""
        self.prefs = create_preferences()
        self.reset_to_defaults()
        self.load_preferences()

    def reset_to_defaults(self):
        """Resets all model values to factory defaults."""
        self.use_contains_string = False
        self.use_contains_no_string = False
        self.use_contains_type = False
        self.use_contains_no_type = False
        self.use_visibility_state = False
        self.use_outliner_color = False
        self.use_no_outliner_color = False
        self.stored_outliner_color = [1, 1, 1]
        self.stored_no_outliner_color = [1, 1, 1]
        self.contains_string = "_jnt"
        self.contains_no_string = "endJnt, eye"
        self.contains_type = "joint"
        self.contains_no_type = "mesh"
        self.shape_node_behavior = SHAPE_BEHAVIOR_SHAPES
        self.visibility_state = False
        self.stored_selections = [[], []]
        self.ui_mode = UI_MODE_DEFAULT

    def load_preferences(self):
        """Loads persisted Selection Manager state."""
        data = self.prefs.get_raw_preferences().get(PREFS_KEY_STATE) or {}
        if not isinstance(data, dict):
            return
        for key in [
            "contains_string",
            "contains_no_string",
            "contains_type",
            "contains_no_type",
            "use_contains_string",
            "use_contains_no_string",
            "use_contains_type",
            "use_contains_no_type",
            "use_visibility_state",
            "use_outliner_color",
            "use_no_outliner_color",
            "visibility_state",
            "ui_mode",
        ]:
            if key in data:
                setattr(self, key, data.get(key))
        if self.ui_mode not in UI_MODES:
            self.ui_mode = UI_MODE_DEFAULT
        self.shape_node_behavior = normalize_shape_behavior(
            data.get("shape_node_behavior") or self.shape_node_behavior
        )
        self.stored_outliner_color = normalize_color(data.get("stored_outliner_color"), self.stored_outliner_color)
        self.stored_no_outliner_color = normalize_color(
            data.get("stored_no_outliner_color"), self.stored_no_outliner_color
        )
        stored_selections = data.get("stored_selections")
        if isinstance(stored_selections, list) and stored_selections:
            self.stored_selections = [list(selection or []) for selection in stored_selections]
        self.ensure_stored_slot_count(2)

    def save_preferences(self):
        """Saves current Selection Manager state."""
        data = {
            "contains_string": self.contains_string,
            "contains_no_string": self.contains_no_string,
            "contains_type": self.contains_type,
            "contains_no_type": self.contains_no_type,
            "use_contains_string": self.use_contains_string,
            "use_contains_no_string": self.use_contains_no_string,
            "use_contains_type": self.use_contains_type,
            "use_contains_no_type": self.use_contains_no_type,
            "use_visibility_state": self.use_visibility_state,
            "use_outliner_color": self.use_outliner_color,
            "use_no_outliner_color": self.use_no_outliner_color,
            "visibility_state": self.visibility_state,
            "ui_mode": self.ui_mode,
            "shape_node_behavior": self.shape_node_behavior,
            "stored_outliner_color": list(self.stored_outliner_color),
            "stored_no_outliner_color": list(self.stored_no_outliner_color),
            "stored_selections": [list(selection or []) for selection in self.stored_selections],
        }
        self.prefs.preferences[PREFS_KEY_STATE] = data
        self.prefs.save()

    def reset_preferences(self):
        """Clears persisted preferences and resets the model."""
        self.prefs.delete_all()
        self.prefs.save()
        self.reset_to_defaults()
        sys.stdout.write("Persistent settings for Selection Manager were cleared.\n")

    def manage_selection(self, create_new_selection=False):
        """Creates or updates the Maya selection using the current settings.

        Args:
            create_new_selection (bool, optional): If True, starts from all scene nodes. Otherwise selected nodes.

        Returns:
            list: Final selected objects.
        """
        cmds = get_maya_cmds()
        managed_selection = []
        to_remove = []
        to_add = []
        selection = cmds.ls() if create_new_selection else cmds.ls(selection=True)
        selection = selection or []

        for obj in selection:
            self.collect_name_matches(obj, to_add, to_remove)
            self.collect_type_matches(obj, to_add, to_remove)
            self.collect_visibility_matches(obj, to_add, to_remove)
            self.collect_outliner_color_matches(obj, to_add, to_remove)

        has_add_operation = (
            self.use_contains_string
            or self.use_contains_type
            or self.use_outliner_color
            or (self.use_visibility_state and self.visibility_state)
        )
        has_remove_operation = (
            self.use_contains_no_string
            or self.use_contains_no_type
            or self.use_no_outliner_color
            or (self.use_visibility_state and not self.visibility_state)
        )

        if not has_add_operation and not has_remove_operation:
            managed_selection = list(selection)
            cmds.warning("No option was active, everything was selected.")
        elif not has_add_operation and has_remove_operation:
            managed_selection = list(selection)

        for obj_add in to_add:
            if obj_add not in to_remove and obj_add not in managed_selection:
                managed_selection.append(obj_add)

        for obj_remove in list(to_remove):
            managed_selection = [obj for obj in managed_selection if obj_remove not in obj]

        cmds.select(managed_selection, ne=True)
        show_selection_feedback(len(managed_selection))
        return managed_selection

    def collect_name_matches(self, obj, to_add, to_remove):
        """Collects matches from name filters.

        Args:
            obj (str): Object name.
            to_add (list): Objects to add.
            to_remove (list): Objects to remove.
        """
        if self.use_contains_string:
            for string in parse_text_filter(self.contains_string):
                if string in obj:
                    to_add.append(obj)
        if self.use_contains_no_string:
            for string in parse_text_filter(self.contains_no_string):
                if string in obj:
                    to_remove.append(obj)

    def collect_type_matches(self, obj, to_add, to_remove):
        """Collects matches from type filters.

        Args:
            obj (str): Object name.
            to_add (list): Objects to add.
            to_remove (list): Objects to remove.
        """
        if not self.use_contains_type and not self.use_contains_no_type:
            return
        cmds = get_maya_cmds()
        obj_type = cmds.objectType(obj)
        obj_shape_type = ""
        if self.shape_node_behavior != SHAPE_BEHAVIOR_IGNORE:
            shape_nodes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            if shape_nodes:
                obj_shape_type = cmds.objectType(shape_nodes[0])
        for string in parse_text_filter(self.contains_type if self.use_contains_type else ""):
            if self.should_match_type(obj, obj_type, obj_shape_type, string):
                to_add.append(self.get_type_target(obj))
        for string in parse_text_filter(self.contains_no_type if self.use_contains_no_type else ""):
            if self.should_match_type(obj, obj_type, obj_shape_type, string):
                to_remove.append(self.get_type_target(obj))

    def should_match_type(self, obj, obj_type, obj_shape_type, string):
        """Checks whether an object matches a type string.

        Args:
            obj (str): Object name.
            obj_type (str): Object type.
            obj_shape_type (str): Shape node type.
            string (str): Type search string.

        Returns:
            bool: True when the object matches.
        """
        self.shape_node_behavior = normalize_shape_behavior(self.shape_node_behavior)
        if self.shape_node_behavior == SHAPE_BEHAVIOR_SHAPES:
            return string in obj_type
        if self.shape_node_behavior == SHAPE_BEHAVIOR_PARENT:
            return bool(string in obj_shape_type or string in obj_type) and not is_object_shape(obj)
        if self.shape_node_behavior == SHAPE_BEHAVIOR_IGNORE:
            return bool(string in obj_type) and not is_object_shape(obj)
        return bool(string in obj_shape_type or string in obj_type)

    def get_type_target(self, obj):
        """Gets the object that should be added or removed for a type match.

        Args:
            obj (str): Object name.

        Returns:
            str: Target object.
        """
        return obj

    def collect_visibility_matches(self, obj, to_add, to_remove):
        """Collects matches from visibility filters.

        Args:
            obj (str): Object name.
            to_add (list): Objects to add.
            to_remove (list): Objects to remove.
        """
        if not self.use_visibility_state or not has_attr(obj, "visibility"):
            return
        cmds = get_maya_cmds()
        if bool(cmds.getAttr("{0}.visibility".format(obj))) == bool(self.visibility_state):
            to_add.append(obj)
        else:
            to_remove.append(obj)

    def collect_outliner_color_matches(self, obj, to_add, to_remove):
        """Collects matches from outliner color filters.

        Args:
            obj (str): Object name.
            to_add (list): Objects to add.
            to_remove (list): Objects to remove.
        """
        if not self.use_outliner_color and not self.use_no_outliner_color:
            return
        if not has_attr(obj, "outlinerColor") or not has_attr(obj, "useOutlinerColor"):
            return
        cmds = get_maya_cmds()
        if not cmds.getAttr("{0}.useOutlinerColor".format(obj)):
            return
        color = list(cmds.getAttr("{0}.outlinerColor".format(obj))[0])
        if self.use_outliner_color and compare_color(color, self.stored_outliner_color):
            to_add.append(obj)
        if self.use_no_outliner_color and compare_color(color, self.stored_no_outliner_color):
            to_remove.append(obj)

    def store_selection(self, slot):
        """Stores the current Maya selection in a slot.

        Args:
            slot (int): Slot number, either 1 or 2.

        Returns:
            list: Stored selection.
        """
        selection = get_maya_cmds().ls(selection=True) or []
        self.set_stored_selection(slot, selection)
        return selection

    def add_to_stored_selection(self, slot):
        """Adds current selection to a stored selection slot.

        Args:
            slot (int): Slot number.

        Returns:
            list: Updated stored selection.
        """
        stored_selection = self.get_stored_selection(slot)
        for obj in get_maya_cmds().ls(selection=True) or []:
            if obj not in stored_selection:
                stored_selection.append(obj)
        self.set_stored_selection(slot, stored_selection)
        return stored_selection

    def remove_from_stored_selection(self, slot):
        """Removes current selection from a stored selection slot.

        Args:
            slot (int): Slot number.

        Returns:
            list: Updated stored selection.
        """
        selected = get_maya_cmds().ls(selection=True) or []
        stored_selection = [obj for obj in self.get_stored_selection(slot) if obj not in selected]
        self.set_stored_selection(slot, stored_selection)
        return stored_selection

    def reset_stored_selection(self, slot):
        """Clears a stored selection slot.

        Args:
            slot (int): Slot number.
        """
        self.set_stored_selection(slot, [])

    def load_stored_selection(self, slot):
        """Selects all existing objects in a stored selection slot.

        Args:
            slot (int): Slot number.

        Returns:
            list: Existing objects that were selected.
        """
        cmds = get_maya_cmds()
        stored_selection = self.get_stored_selection(slot)
        existing = [obj for obj in stored_selection if cmds.objExists(obj)]
        missing = [obj for obj in stored_selection if not cmds.objExists(obj)]
        print_stored_selection(existing=existing, missing=missing)
        if existing:
            cmds.select(existing)
        return existing

    def save_stored_selection(self, slot, as_text=False):
        """Saves a stored selection as a quick set or text file.

        Args:
            slot (int): Slot number.
            as_text (bool, optional): If True, export as text. Otherwise save a Maya set.

        Returns:
            str or None: Saved set or text path.
        """
        stored_selection = self.get_stored_selection(slot)
        if as_text:
            return export_selection_to_text(stored_selection)
        set_name = "Set_StoredSelection_{0:02d}".format(int(slot))
        cmds = get_maya_cmds()
        if cmds.objExists(set_name):
            cmds.delete(set_name)
        selection_set = cmds.sets(name=set_name)
        for obj in stored_selection:
            if cmds.objExists(obj):
                cmds.sets(obj, add=selection_set)
        return selection_set

    def get_stored_selection(self, slot):
        """Gets a stored selection list.

        Args:
            slot (int): Slot number.

        Returns:
            list: Stored selection.
        """
        self.ensure_stored_slot_count(slot)
        return list(self.stored_selections[int(slot) - 1])

    def set_stored_selection(self, slot, selection):
        """Sets a stored selection slot.

        Args:
            slot (int): Slot number.
            selection (list): Selection to store.
        """
        self.ensure_stored_slot_count(slot)
        self.stored_selections[int(slot) - 1] = list(selection or [])

    def ensure_stored_slot_count(self, slot):
        """Ensures the stored selection list contains at least the requested slot.

        Args:
            slot (int): One-based slot number or minimum count.
        """
        slot = max(1, int(slot))
        while len(self.stored_selections) < slot:
            self.stored_selections.append([])

    def add_stored_selection_slot(self):
        """Adds a stored selection slot.

        Returns:
            int: New slot number.
        """
        self.stored_selections.append([])
        return len(self.stored_selections)

    def delete_stored_selection_slot(self, slot):
        """Deletes a stored selection slot.

        Args:
            slot (int): One-based slot number.

        Returns:
            bool: True when a row was deleted, False when the last row was cleared instead.
        """
        self.ensure_stored_slot_count(slot)
        if len(self.stored_selections) <= 1:
            self.set_stored_selection(1, [])
            return False
        del self.stored_selections[int(slot) - 1]
        return True

    def get_color_from_selection(self):
        """Gets the outliner color from the first selected object.

        Returns:
            list or None: RGB color values.
        """
        cmds = get_maya_cmds()
        selection = cmds.ls(selection=True) or []
        if not selection:
            cmds.warning("Nothing selected. Select an object with an outliner color and try again.")
            return None
        obj = selection[0]
        if not has_attr(obj, "outlinerColor"):
            cmds.warning("Selected object does not have an outliner color attribute.")
            return None
        return list(cmds.getAttr("{0}.outlinerColor".format(obj))[0])

    def print_selection_types(self, selection_only=True):
        """Prints selected or scene node types.

        Args:
            selection_only (bool, optional): Whether to inspect only selected objects.

        Returns:
            list: Sorted type names.
        """
        cmds = get_maya_cmds()
        nodes = cmds.ls(selection=True) if selection_only else cmds.ls()
        type_names = []
        for obj in nodes or []:
            obj_type = cmds.objectType(obj)
            if obj_type not in type_names:
                type_names.append(obj_type)
            shape_nodes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape_node in shape_nodes:
                shape_type = "{0} (Shape Node)".format(cmds.objectType(shape_node))
                if shape_type not in type_names:
                    type_names.append(shape_type)
        if type_names:
            print("#" * 80)
            print("Types:")
            for type_name in sorted(type_names):
                print(type_name)
            print("#" * 80)
            message = 'Open the <span style="color:#FF0000;">Script Editor</span> to see the list of types.'
            show_in_view_message(message)
        else:
            cmds.warning("Nothing selected (or no types to be displayed).")
        return sorted(type_names)

    def select_hierarchy(self):
        """Adds selected hierarchy descendants to the Maya selection."""
        get_maya_cmds().select(hierarchy=True)


def get_maya_cmds():
    """Gets maya.cmds lazily.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds

    return cmds


def parse_text_filter(text):
    """Parses a comma-separated text filter.

    Args:
        text (str): Text to parse.

    Returns:
        list: Non-empty filter strings.
    """
    text = str(text or "").replace(" ", "")
    if not text:
        return []
    return [item for item in text.split(",") if item]


def is_object_shape(obj):
    """Checks whether an object is a shape.

    Args:
        obj (str): Object name.

    Returns:
        bool: True when the object inherits from shape.
    """
    cmds = get_maya_cmds()
    return "shape" in [item.lower() for item in cmds.nodeType(obj, inherited=True)]


def has_attr(obj, attr_name):
    """Checks whether a Maya object has an attribute.

    Args:
        obj (str): Object name.
        attr_name (str): Attribute name.

    Returns:
        bool: True when the attribute exists.
    """
    cmds = get_maya_cmds()
    return attr_name in (cmds.listAttr(obj) or [])


def compare_color(color_a, color_b):
    """Compares two RGB colors using rounded components.

    Args:
        color_a (list): First RGB color.
        color_b (list): Second RGB color.

    Returns:
        bool: True when the colors match.
    """
    return [round(float(value), 6) for value in color_a] == [round(float(value), 6) for value in color_b]


def normalize_shape_behavior(value):
    """Normalizes a stored shape behavior label.

    Args:
        value (str): Behavior label.

    Returns:
        str: Current behavior label.
    """
    value = str(value or "")
    value = LEGACY_SHAPE_BEHAVIOR_MAP.get(value, value)
    if value in SHAPE_BEHAVIOR_OPTIONS:
        return value
    return SHAPE_BEHAVIOR_SHAPES


def create_preferences():
    """Creates a preferences object.

    Returns:
        Prefs or MemoryPrefs: Preferences object.
    """
    try:
        import gt.core.prefs as core_prefs

        return core_prefs.Prefs(PREFS_FILENAME)
    except Exception as exception:
        logger.debug("Using in-memory Selection Manager preferences. Issue: %s", exception)
        return MemoryPrefs()


class MemoryPrefs:
    """In-memory fallback used when Maya preferences are unavailable."""

    def __init__(self):
        """Initializes the fallback preferences."""
        self.preferences = {}

    def get_raw_preferences(self):
        """Gets the raw fallback preferences.

        Returns:
            dict: Preference data.
        """
        return self.preferences

    def save(self):
        """No-op save used by the fallback preferences."""

    def delete_all(self):
        """Clears the fallback preferences."""
        self.preferences = {}


def normalize_color(value, default):
    """Normalizes RGB color preference data.

    Args:
        value (object): Stored color value.
        default (list): Fallback RGB value.

    Returns:
        list: RGB values between zero and one.
    """
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return list(default)
    try:
        return [max(0, min(1, float(value[index]))) for index in range(3)]
    except (TypeError, ValueError):
        return list(default)


def export_selection_to_text(selection):
    """Exports a selection list to a text file.

    Args:
        selection (list): Objects to export.

    Returns:
        str: Written text file path.
    """
    cmds = get_maya_cmds()
    temp_dir = cmds.internalVar(userTmpDir=True)
    txt_file = os.path.join(temp_dir, "tmp_sel.txt")
    string_for_python = "', '".join(selection or [])
    string_for_list = "\n# ".join(selection or [])
    select_command = (
        "# Python command to select it:\n\n"
        "import maya.cmds as cmds\nselected_objects = ['"
        + string_for_python
        + "']\ncmds.select(selected_objects)\n\n\n# List of Objects:\n# "
        + string_for_list
    )
    with open(txt_file, "w", encoding="utf-8") as file_stream:
        file_stream.write(select_command)
    try:
        os.startfile(txt_file)
    except Exception:
        pass
    return txt_file


def print_stored_selection(existing, missing):
    """Prints a stored selection summary.

    Args:
        existing (list): Existing objects.
        missing (list): Missing objects.
    """
    print("#" * 32 + " Objects List " + "#" * 32)
    for obj in existing:
        print(obj)
    for obj in missing:
        print("{0} no longer exists!".format(obj))
    print("#" * 80)
    if missing:
        show_in_view_message('Some elements are <span style="color:#FF0000;">missing!</span>')
        show_in_view_message("Open script editor for more information.")
    else:
        show_in_view_message("Stored elements have been selected.")


def show_selection_feedback(number_objects):
    """Shows selection count feedback in Maya.

    Args:
        number_objects (int): Number of selected objects.
    """
    if number_objects:
        label = "object was" if number_objects == 1 else "objects were"
        message = '<{0}><span style="color:#FF0000;text-decoration:underline;">{1}</span> {2} selected.'
        show_in_view_message(message.format(random.random(), number_objects, label))
    else:
        show_in_view_message("No objects were selected.")


def show_in_view_message(message):
    """Shows a Maya in-view message.

    Args:
        message (str): Message to show.
    """
    try:
        get_maya_cmds().inViewMessage(amg=message, pos="botLeft", fade=True, alpha=0.9)
    except Exception:
        logger.info(message)
