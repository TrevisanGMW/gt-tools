"""
Color Manager Model
"""

import json
import logging
import math
import os
import random


logging.basicConfig()
logger = logging.getLogger("gt_color_manager")
logger.setLevel(logging.INFO)

UI_MODE_MINIMAL = "Minimal"
UI_MODE_DEFAULT = "Default"
UI_MODE_COMPLETE = "Complete"
UI_MODES = [UI_MODE_MINIMAL, UI_MODE_DEFAULT, UI_MODE_COMPLETE]

COLOR_MODE_DRAWING_OVERRIDE = "Drawing Override"
COLOR_MODE_WIREFRAME = "Wireframe Color"
COLOR_MODES = [COLOR_MODE_DRAWING_OVERRIDE, COLOR_MODE_WIREFRAME]

TARGET_TRANSFORM = "Transform"
TARGET_SHAPE = "Shape"
TARGETS = [TARGET_TRANSFORM, TARGET_SHAPE]

CURRENT_COLOR_UNCONVERTED = "Unconverted (Clicked)"
CURRENT_COLOR_CONVERTED = "Converted (Viewport)"
CURRENT_COLOR_MODES = [CURRENT_COLOR_UNCONVERTED, CURRENT_COLOR_CONVERTED]

PREFS_FILENAME = "color_manager"
PREFS_KEY_STATE = "state"

PRESET_COLORS = [
    [1, 0.25, 0.25],
    [1, 0.45, 0.15],
    [1, 1, 0.35],
    [0.5, 1, 0.20],
    [0.3, 1, 0.8],
    [0.2, 0.6, 1],
    [0, 0.2, 1],
    [1, 0.45, 0.70],
    [0.75, 0.35, 0.90],
    [0.45, 0.2, 0.9],
]


def get_maya_cmds():
    """Gets maya.cmds lazily.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds

    return cmds


def normalize_color(color):
    """Normalizes an RGB color into a clamped three-float list.

    Args:
        color (list or tuple): RGB color data.

    Returns:
        list: Clamped RGB color.
    """
    if not isinstance(color, (list, tuple)) or len(color) < 3:
        return [0.3, 0.3, 0.3]
    normalized = []
    for index in range(3):
        try:
            value = float(color[index])
        except (TypeError, ValueError):
            value = 0.0
        normalized.append(max(0.0, min(1.0, value)))
    return normalized


def normalize_saved_colors(saved_colors):
    """Normalizes saved color payloads.

    Args:
        saved_colors (list or dict): Saved color data.

    Returns:
        list: RGB color lists.
    """
    if isinstance(saved_colors, dict):
        saved_colors = saved_colors.get("colors") or saved_colors.get("saved_colors") or []
    if not isinstance(saved_colors, list):
        return []
    normalized = []
    for color in saved_colors:
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            normalized.append(normalize_color(color))
    return normalized


def colors_match(color_a, color_b, tolerance=0.0001):
    """Checks whether two colors are effectively equal.

    Args:
        color_a (list): First RGB color.
        color_b (list): Second RGB color.
        tolerance (float, optional): Allowed difference.

    Returns:
        bool: True if all channels match within tolerance.
    """
    color_a = normalize_color(color_a)
    color_b = normalize_color(color_b)
    return all(abs(color_a[index] - color_b[index]) <= tolerance for index in range(3))


def convert_color_for_outliner(color, enabled=True):
    """Converts UI/viewport color data into outliner color data.

    Args:
        color (list): RGB color.
        enabled (bool, optional): Whether to apply correction.

    Returns:
        list: Converted RGB color.
    """
    color = normalize_color(color)
    if not enabled:
        return color
    return [math.pow(value, 0.454) for value in color]


def convert_color_from_outliner(color, enabled=True):
    """Converts outliner color data into UI/viewport color data.

    Args:
        color (list): RGB color.
        enabled (bool, optional): Whether to apply correction.

    Returns:
        list: Converted RGB color.
    """
    color = normalize_color(color)
    if not enabled:
        return color
    return [math.pow((value + 0.055) / 1.055, 2.4) for value in color]


class ColorManagerModel:
    """Stores Color Manager state and runs Maya color operations."""

    def __init__(self):
        """Initializes the color manager model."""
        self.current_color = [0.3, 0.3, 0.3]
        self.color_mode = COLOR_MODE_DRAWING_OVERRIDE
        self.target = TARGET_TRANSFORM
        self.set_outliner = True
        self.set_viewport = False
        self.ui_mode = UI_MODE_MINIMAL
        self.saved_colors = []
        self.auto_adjust_outliner_to_viewport = True
        self.auto_adjust_viewport_to_outliner = True
        self.current_color_mode = CURRENT_COLOR_UNCONVERTED
        import gt.core.prefs as core_prefs

        self._prefs = core_prefs.Prefs(PREFS_FILENAME)

    def load_preferences(self):
        """Loads persistent package preferences."""
        preferences = self._prefs.get_raw_preferences() or {}
        state = preferences.get(PREFS_KEY_STATE)
        if not isinstance(state, dict):
            state = preferences if isinstance(preferences, dict) else {}
        self.set_outliner = bool(state.get("set_outliner", self.set_outliner))
        self.set_viewport = bool(state.get("set_viewport", self.set_viewport))
        self.auto_adjust_outliner_to_viewport = bool(
            state.get("auto_adjust_outliner_to_viewport", self.auto_adjust_outliner_to_viewport)
        )
        self.auto_adjust_viewport_to_outliner = bool(
            state.get("auto_adjust_viewport_to_outliner", self.auto_adjust_viewport_to_outliner)
        )
        self.current_color_mode = self._validate_value(
            state.get("current_color_mode", self.current_color_mode),
            CURRENT_COLOR_MODES,
            CURRENT_COLOR_UNCONVERTED,
        )
        self.current_color = normalize_color(state.get("current_color", self.current_color))
        self.target = self._validate_value(state.get("target", self.target), TARGETS, TARGET_TRANSFORM)
        self.color_mode = self._validate_value(
            state.get("color_mode", self.color_mode),
            COLOR_MODES,
            COLOR_MODE_DRAWING_OVERRIDE,
        )
        self.ui_mode = self._validate_value(state.get("ui_mode", self.ui_mode), UI_MODES, UI_MODE_MINIMAL)
        self.saved_colors = normalize_saved_colors(state.get("saved_colors", self.saved_colors))

    def save_preferences(self):
        """Saves all persistent package preferences."""
        payload = {
            "current_color": normalize_color(self.current_color),
            "color_mode": str(self.color_mode),
            "target": str(self.target),
            "set_outliner": bool(self.set_outliner),
            "set_viewport": bool(self.set_viewport),
            "ui_mode": str(self.ui_mode),
            "saved_colors": normalize_saved_colors(self.saved_colors),
            "auto_adjust_outliner_to_viewport": bool(self.auto_adjust_outliner_to_viewport),
            "auto_adjust_viewport_to_outliner": bool(self.auto_adjust_viewport_to_outliner),
            "current_color_mode": str(self.current_color_mode),
        }
        self._prefs.set_raw_preferences({PREFS_KEY_STATE: payload})
        self._prefs.save()

    def reset_preferences(self):
        """Clears persistent preferences and restores defaults."""
        self._prefs.delete_all()
        self._prefs.save()
        self.__init__()

    def set_current_color(self, color):
        """Sets the current color and persists it.

        Args:
            color (list): RGB color.
        """
        self.current_color = normalize_color(color)
        self.save_preferences()

    def prepare_clicked_color(self, color):
        """Prepares a clicked swatch color for the Current Color control.

        Args:
            color (list): Unconverted clicked RGB color.

        Returns:
            list: Color represented by the active Current Color mode.
        """
        color = normalize_color(color)
        if self.current_color_mode == CURRENT_COLOR_CONVERTED:
            return convert_color_from_outliner(color, self.auto_adjust_outliner_to_viewport)
        return color

    def get_viewport_color(self):
        """Gets the current color converted for viewport application.

        Returns:
            list: RGB color for viewport drawing overrides or wireframes.
        """
        color = normalize_color(self.current_color)
        if self.current_color_mode == CURRENT_COLOR_UNCONVERTED:
            return convert_color_from_outliner(color, self.auto_adjust_outliner_to_viewport)
        return color

    def get_outliner_color(self):
        """Gets the current color converted for Outliner application.

        Returns:
            list: RGB color for the Maya Outliner.
        """
        viewport_color = self.get_viewport_color()
        return convert_color_for_outliner(viewport_color, self.auto_adjust_viewport_to_outliner)

    def cycle_ui_mode(self):
        """Cycles the active UI mode.

        Returns:
            str: New UI mode.
        """
        try:
            current_index = UI_MODES.index(self.ui_mode)
        except ValueError:
            current_index = 0
        self.ui_mode = UI_MODES[(current_index + 1) % len(UI_MODES)]
        self.save_preferences()
        return self.ui_mode

    def save_current_color(self):
        """Adds the current color to the saved colors list.

        Returns:
            bool: True if a color was added.
        """
        color = normalize_color(self.current_color)
        if any(colors_match(color, saved_color) for saved_color in self.saved_colors):
            return False
        self.saved_colors.append(color)
        self.save_preferences()
        return True

    def delete_current_color(self):
        """Deletes the current color if saved, otherwise deletes the last saved color.

        Returns:
            bool: True if a color was removed.
        """
        if not self.saved_colors:
            return False
        color = normalize_color(self.current_color)
        for index, saved_color in enumerate(list(self.saved_colors)):
            if colors_match(color, saved_color):
                del self.saved_colors[index]
                self.save_preferences()
                return True
        self.saved_colors.pop()
        self.save_preferences()
        return True

    def delete_saved_color(self, index):
        """Deletes a saved color by index.

        Args:
            index (int): Saved color index.

        Returns:
            bool: True if a color was removed.
        """
        if index < 0 or index >= len(self.saved_colors):
            return False
        del self.saved_colors[index]
        self.save_preferences()
        return True

    def clear_saved_colors(self):
        """Clears all saved colors."""
        self.saved_colors = []
        self.save_preferences()

    def export_saved_colors(self, file_path):
        """Exports saved colors to a JSON file.

        Args:
            file_path (str): Output JSON path.

        Returns:
            str: Written file path.
        """
        if not file_path:
            return ""
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
        payload = {"version": 1, "colors": normalize_saved_colors(self.saved_colors)}
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=4, sort_keys=True)
        return file_path

    def import_saved_colors(self, file_path):
        """Imports saved colors from a JSON file.

        Args:
            file_path (str): JSON file path.

        Returns:
            int: Number of colors added.
        """
        if not file_path or not os.path.isfile(file_path):
            return 0
        with open(file_path, "r", encoding="utf-8") as json_file:
            payload = json.load(json_file)
        added_count = 0
        for color in normalize_saved_colors(payload):
            if not any(colors_match(color, saved_color) for saved_color in self.saved_colors):
                self.saved_colors.append(color)
                added_count += 1
        if added_count:
            self.save_preferences()
        return added_count

    def get_selection_color(self):
        """Gets the color from the current Maya selection.

        Returns:
            list or None: RGB color, if found.
        """
        cmds = get_maya_cmds()
        selection = cmds.ls(selection=True) or []
        if len(selection) != 1:
            cmds.warning("Select only one object to get the color from and try again.")
            return None
        selected_item = self._get_target_object(selection[0])
        if not selected_item:
            return None
        try:
            if self.set_outliner:
                outliner_color = [
                    cmds.getAttr("{0}.outlinerColorR".format(selected_item)),
                    cmds.getAttr("{0}.outlinerColorG".format(selected_item)),
                    cmds.getAttr("{0}.outlinerColorB".format(selected_item)),
                ]
                return self.prepare_clicked_color(outliner_color)
            if self.set_viewport:
                viewport_color = [
                    cmds.getAttr("{0}.overrideColorR".format(selected_item)),
                    cmds.getAttr("{0}.overrideColorG".format(selected_item)),
                    cmds.getAttr("{0}.overrideColorB".format(selected_item)),
                ]
                if self.current_color_mode == CURRENT_COLOR_UNCONVERTED:
                    return convert_color_for_outliner(
                        viewport_color,
                        self.auto_adjust_viewport_to_outliner,
                    )
                return viewport_color
        except Exception as exception:
            cmds.warning("Unable to extract color. Issue: {0}".format(exception))
        return None

    def apply_color(self, reset=False):
        """Applies or resets color on the current selection.

        Args:
            reset (bool, optional): Whether to reset instead of apply.

        Returns:
            tuple: Changed object count and error text.
        """
        cmds = get_maya_cmds()
        function_name = "Color Manager - Set Color"
        changed_count = 0
        errors = []
        try:
            cmds.undoInfo(openChunk=True, chunkName=function_name)
            target_objects = self.get_target_objects()
            if not target_objects:
                return 0, ""
            for obj in target_objects:
                if reset:
                    changed_count += self._reset_object_color(obj)
                else:
                    changed_count += self._apply_object_color(obj)
        except Exception as exception:
            errors.append(str(exception))
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=function_name)
        self.show_feedback(changed_count=changed_count, reset=reset)
        if errors:
            cmds.warning("An error occurred. Open the script editor for more information.")
            print("######## Errors: ########")
            print("\n".join(errors))
        return changed_count, "\n".join(errors)

    def get_target_objects(self):
        """Gets selected objects affected by the current target mode.

        Returns:
            list: Target object paths.
        """
        cmds = get_maya_cmds()
        selection = cmds.ls(selection=True) or []
        if not selection:
            cmds.warning("You need to select at least one object.")
            return []
        if self.target == TARGET_TRANSFORM:
            return selection
        shapes = []
        for selected_item in selection:
            shapes.extend(cmds.listRelatives(selected_item, shapes=True, fullPath=True) or [])
        if not shapes:
            cmds.warning('No shapes were found. Make sure you are using the correct "Target" option.')
        return shapes

    def show_feedback(self, changed_count, reset=False):
        """Shows a Maya viewport feedback message.

        Args:
            changed_count (int): Number of affected objects.
            reset (bool, optional): Whether the action was reset.
        """
        cmds = get_maya_cmds()
        message = '<{0}><span style="color:#FF0000;text-decoration:underline;">{1} </span>'.format(
            random.random(),
            changed_count,
        )
        suffix = "object was" if changed_count == 1 else "objects were"
        if reset:
            message += "{0} reset to the default color.".format(suffix)
        else:
            message += "{0} colored.".format(suffix)
        cmds.inViewMessage(amg=message, pos="botLeft", fade=True, alpha=0.9)

    def _apply_object_color(self, obj):
        """Applies active color settings to one object.

        Args:
            obj (str): Maya object path.

        Returns:
            int: Number of counted changes.
        """
        changed_count = 0
        if self.set_viewport:
            if self.color_mode == COLOR_MODE_DRAWING_OVERRIDE:
                changed_count += self._set_drawing_override_color(obj)
            else:
                changed_count += self._set_wireframe_color(obj)
        if self.set_outliner:
            self._set_outliner_color(obj)
            if not self.set_viewport:
                changed_count += 1
        return changed_count

    def _reset_object_color(self, obj):
        """Resets active color settings on one object.

        Args:
            obj (str): Maya object path.

        Returns:
            int: Number of counted changes.
        """
        changed_count = 0
        cmds = get_maya_cmds()
        if self.set_viewport:
            try:
                if cmds.getAttr("{0}.overrideEnabled".format(obj)):
                    cmds.setAttr("{0}.overrideEnabled".format(obj), 0)
                    cmds.setAttr("{0}.overrideColorR".format(obj), 0)
                    cmds.setAttr("{0}.overrideColorG".format(obj), 0)
                    cmds.setAttr("{0}.overrideColorB".format(obj), 0)
                if cmds.getAttr("{0}.useObjectColor".format(obj)) != 0:
                    cmds.color(obj)
                changed_count += 1
            except Exception as exception:
                logger.debug(str(exception))
        if self.set_outliner:
            try:
                cmds.setAttr("{0}.useOutlinerColor".format(obj), 0)
                if not self.set_viewport:
                    changed_count += 1
            except Exception as exception:
                logger.debug(str(exception))
        return changed_count

    def _set_drawing_override_color(self, obj):
        """Sets drawing override color on one object.

        Args:
            obj (str): Maya object path.

        Returns:
            int: One when the operation was attempted.
        """
        cmds = get_maya_cmds()
        if cmds.getAttr("{0}.useObjectColor".format(obj)) != 0:
            cmds.color(obj)
        cmds.setAttr("{0}.overrideEnabled".format(obj), 1)
        cmds.setAttr("{0}.overrideRGBColors".format(obj), 1)
        viewport_color = self.get_viewport_color()
        cmds.setAttr("{0}.overrideColorR".format(obj), viewport_color[0])
        cmds.setAttr("{0}.overrideColorG".format(obj), viewport_color[1])
        cmds.setAttr("{0}.overrideColorB".format(obj), viewport_color[2])
        return 1

    def _set_wireframe_color(self, obj):
        """Sets wireframe color on one object.

        Args:
            obj (str): Maya object path.

        Returns:
            int: One when the operation was attempted.
        """
        cmds = get_maya_cmds()
        if cmds.getAttr("{0}.overrideEnabled".format(obj)):
            cmds.setAttr("{0}.overrideEnabled".format(obj), 0)
            cmds.setAttr("{0}.overrideColorR".format(obj), 0)
            cmds.setAttr("{0}.overrideColorG".format(obj), 0)
            cmds.setAttr("{0}.overrideColorB".format(obj), 0)
        viewport_color = self.get_viewport_color()
        cmds.color(obj, rgb=(viewport_color[0], viewport_color[1], viewport_color[2]))
        return 1

    def _set_outliner_color(self, obj):
        """Sets outliner color on one object.

        Args:
            obj (str): Maya object path.
        """
        import gt.core.color as core_color

        outliner_color = self.get_outliner_color()
        core_color.set_color_outliner(obj_list=obj, rgb_color=outliner_color)

    def _get_target_object(self, selected_item):
        """Gets the object to inspect for selection color.

        Args:
            selected_item (str): Selected object.

        Returns:
            str or None: Target object.
        """
        cmds = get_maya_cmds()
        if self.target == TARGET_TRANSFORM:
            return selected_item
        shapes = cmds.listRelatives(selected_item, shapes=True, fullPath=True) or []
        if shapes:
            return shapes[0]
        cmds.warning('No shapes were found. Make sure you are using the correct "Target" option.')
        return None

    @staticmethod
    def _validate_value(value, valid_values, fallback):
        """Gets a valid option value.

        Args:
            value (str): Incoming value.
            valid_values (list): Valid values.
            fallback (str): Fallback value.

        Returns:
            str: Valid value.
        """
        return value if value in valid_values else fallback
