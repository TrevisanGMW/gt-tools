"""
Auto Rigger Scene Options

Pure Python definitions for the options used by the "New Scene" module.
The options are stored as a dictionary (see "core_scene.set_scene_from_dict()"), where a missing key means the
option is ignored when a new scene is created. This module describes the known keys, so the UI can offer a proper
widget for each of them. It must remain importable outside Maya.

Import Line:
    import gt.tools.auto_rigger.rigger_scene_options as tools_rig_scene_opts
"""

import copy


class SceneOptionType:
    def __init__(self):
        """
        Value types used by the scene option definitions. Each type maps to a different widget.
        """

    ENUM = "enum"
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"


class SceneOption:
    def __init__(
        self,
        key,
        nice_name,
        value_type,
        default,
        section,
        items=None,
        minimum=None,
        maximum=None,
        decimals=3,
        tooltip="",
    ):
        """
        Describes a single scene option.

        Args:
            key (str): Dictionary key recognized by "core_scene.set_scene_from_dict()".
            nice_name (str): Name displayed in the UI.
            value_type (str): One of the "SceneOptionType" values.
            default (any): Default value used when the option is enabled or reset.
            section (str): Name of the UI section that groups this option.
            items (list, optional): Available values for enum options.
            minimum (int, float, optional): Minimum value for numeric options.
            maximum (int, float, optional): Maximum value for numeric options.
            decimals (int, optional): Decimal places shown for float options.
            tooltip (str, optional): Description displayed as a tooltip.
        """
        self.key = key
        self.nice_name = nice_name
        self.value_type = value_type
        self.default = default
        self.section = section
        self.items = list(items or [])
        self.minimum = minimum
        self.maximum = maximum
        self.decimals = decimals
        self.tooltip = tooltip

    def __repr__(self):
        """
        Returns a readable representation of the scene option.

        Returns:
            str: Readable representation.
        """
        return f'SceneOption(key="{self.key}", type="{self.value_type}", default={self.default!r})'

    def coerce_value(self, value):
        """
        Converts a stored value to the type expected by this option. Falls back to the default when invalid.

        Args:
            value (any): Stored value to convert.

        Returns:
            any: Value converted to the option type.
        """
        try:
            if self.value_type == SceneOptionType.BOOL:
                return bool(value)
            if self.value_type == SceneOptionType.INT:
                return int(round(float(value)))
            if self.value_type == SceneOptionType.FLOAT:
                return float(value)
            if self.value_type == SceneOptionType.ENUM:
                if self.key == "frame_rate":
                    return normalize_frame_rate(value)
                return value
        except (TypeError, ValueError):
            pass
        return copy.deepcopy(self.default)


class SceneSection:
    def __init__(self):
        """
        Section names used to group the scene options in the UI.
        """

    UNITS = "Units"
    VIEWPORT = "Viewport"
    CAMERA = "Perspective Camera"
    TIMELINE = "Timeline"
    GRID = "Grid"


LINEAR_UNITS = ["millimeter", "centimeter", "meter", "kilometer", "inch", "foot", "yard", "mile"]
ANGULAR_UNITS = ["degree", "radian"]
FRAME_RATES = [
    "12fps",
    "15fps",
    "23.976fps",
    "24fps",
    "25fps",
    "29.97fps",
    "30fps",
    "48fps",
    "50fps",
    "59.94fps",
    "60fps",
    "120fps",
]
MULTI_SAMPLE_COUNTS = [1, 2, 4, 8, 16]
_FRAME_RANGE = (-1_000_000.0, 1_000_000.0)

SCENE_OPTIONS = [
    # Units
    SceneOption(
        key="linear_unit",
        nice_name="Linear Unit",
        value_type=SceneOptionType.ENUM,
        default="centimeter",
        section=SceneSection.UNITS,
        items=LINEAR_UNITS,
        tooltip="Scene linear (working) unit.",
    ),
    SceneOption(
        key="angular_unit",
        nice_name="Angular Unit",
        value_type=SceneOptionType.ENUM,
        default="degree",
        section=SceneSection.UNITS,
        items=ANGULAR_UNITS,
        tooltip="Scene angular unit.",
    ),
    SceneOption(
        key="frame_rate",
        nice_name="Frame Rate",
        value_type=SceneOptionType.ENUM,
        default="30fps",
        section=SceneSection.UNITS,
        items=FRAME_RATES,
        tooltip="Scene time unit (frames per second).",
    ),
    # Viewport
    SceneOption(
        key="multi_sample",
        nice_name="Multi-Sample AA",
        value_type=SceneOptionType.BOOL,
        default=True,
        section=SceneSection.VIEWPORT,
        tooltip="Enables or disables viewport multi-sample anti-aliasing.",
    ),
    SceneOption(
        key="multi_sample_count",
        nice_name="Sample Count",
        value_type=SceneOptionType.ENUM,
        default=8,
        section=SceneSection.VIEWPORT,
        items=MULTI_SAMPLE_COUNTS,
        tooltip="Viewport multi-sample anti-aliasing level.",
    ),
    SceneOption(
        key="display_textures",
        nice_name="Display Textures",
        value_type=SceneOptionType.BOOL,
        default=True,
        section=SceneSection.VIEWPORT,
        tooltip="When checked, textures are displayed in all viewports. (Unchecked does not disable them)",
    ),
    SceneOption(
        key="use_default_material",
        nice_name="Use Default Material",
        value_type=SceneOptionType.BOOL,
        default=False,
        section=SceneSection.VIEWPORT,
        tooltip='Sets the state of the viewport "Use Default Material" option.',
    ),
    # Camera
    SceneOption(
        key="persp_clip_plane_near",
        nice_name="Near Clip Plane",
        value_type=SceneOptionType.FLOAT,
        default=1.0,
        section=SceneSection.CAMERA,
        minimum=0.0001,
        maximum=1_000_000.0,
        tooltip="Near clipping plane of the perspective (persp) camera.",
    ),
    SceneOption(
        key="persp_clip_plane_far",
        nice_name="Far Clip Plane",
        value_type=SceneOptionType.FLOAT,
        default=10000.0,
        section=SceneSection.CAMERA,
        minimum=0.001,
        maximum=100_000_000.0,
        tooltip="Far clipping plane of the perspective (persp) camera.",
    ),
    # Timeline
    SceneOption(
        key="playback_frame_start",
        nice_name="Playback Start",
        value_type=SceneOptionType.FLOAT,
        default=1.0,
        section=SceneSection.TIMELINE,
        minimum=_FRAME_RANGE[0],
        maximum=_FRAME_RANGE[1],
        decimals=2,
        tooltip="Start frame of the playback range.",
    ),
    SceneOption(
        key="playback_frame_end",
        nice_name="Playback End",
        value_type=SceneOptionType.FLOAT,
        default=120.0,
        section=SceneSection.TIMELINE,
        minimum=_FRAME_RANGE[0],
        maximum=_FRAME_RANGE[1],
        decimals=2,
        tooltip="End frame of the playback range.",
    ),
    SceneOption(
        key="animation_frame_start",
        nice_name="Animation Start",
        value_type=SceneOptionType.FLOAT,
        default=1.0,
        section=SceneSection.TIMELINE,
        minimum=_FRAME_RANGE[0],
        maximum=_FRAME_RANGE[1],
        decimals=2,
        tooltip="Start frame of the animation range.",
    ),
    SceneOption(
        key="animation_frame_end",
        nice_name="Animation End",
        value_type=SceneOptionType.FLOAT,
        default=200.0,
        section=SceneSection.TIMELINE,
        minimum=_FRAME_RANGE[0],
        maximum=_FRAME_RANGE[1],
        decimals=2,
        tooltip="End frame of the animation range.",
    ),
    SceneOption(
        key="current_time",
        nice_name="Current Time",
        value_type=SceneOptionType.FLOAT,
        default=1.0,
        section=SceneSection.TIMELINE,
        minimum=_FRAME_RANGE[0],
        maximum=_FRAME_RANGE[1],
        decimals=2,
        tooltip="Current frame on the timeline.",
    ),
    # Grid
    SceneOption(
        key="grid_size",
        nice_name="Grid Size",
        value_type=SceneOptionType.FLOAT,
        default=12.0,
        section=SceneSection.GRID,
        minimum=0.0,
        maximum=1_000_000.0,
        tooltip="Length and width of the grid.",
    ),
    SceneOption(
        key="grid_spacing",
        nice_name="Grid Spacing",
        value_type=SceneOptionType.FLOAT,
        default=5.0,
        section=SceneSection.GRID,
        minimum=0.0,
        maximum=1_000_000.0,
        tooltip="Distance between the grid lines.",
    ),
    SceneOption(
        key="grid_divisions",
        nice_name="Grid Divisions",
        value_type=SceneOptionType.INT,
        default=5,
        section=SceneSection.GRID,
        minimum=0,
        maximum=10_000,
        tooltip="Number of subdivisions between the main grid lines.",
    ),
]


def normalize_frame_rate(value):
    """
    Converts numeric frame rates to the "<value>fps" string format used by the scene options.
    Strings (e.g. "30fps", "film") are returned unchanged.

    Args:
        value (int, float, str): Frame rate value.

    Returns:
        str: Frame rate string. e.g. 30 becomes "30fps".
    """
    if isinstance(value, bool):
        raise ValueError("Frame rate cannot be a boolean.")
    if isinstance(value, (int, float)):
        number = int(value) if float(value).is_integer() else value
        return f"{number}fps"
    if isinstance(value, str) and value:
        return value
    raise ValueError(f'Invalid frame rate value: "{value}".')


def get_scene_option_definitions():
    """
    Gets the known scene option definitions in display order.

    Returns:
        list: A list of "SceneOption" objects.
    """
    return list(SCENE_OPTIONS)


def get_scene_option_definition(key):
    """
    Gets a scene option definition using its dictionary key.

    Args:
        key (str): Scene option key. e.g. "linear_unit"

    Returns:
        SceneOption or None: The matching definition, None if the key is unknown.
    """
    for option in SCENE_OPTIONS:
        if option.key == key:
            return option
    return None


def get_scene_option_sections():
    """
    Gets the section names in display order, without duplicates.

    Returns:
        list: A list of section names.
    """
    sections = []
    for option in SCENE_OPTIONS:
        if option.section not in sections:
            sections.append(option.section)
    return sections


def get_default_scene_options():
    """
    Gets a new dictionary with all known scene options set to their default values.

    Returns:
        dict: Scene options dictionary.
    """
    return {option.key: copy.deepcopy(option.default) for option in SCENE_OPTIONS}


def get_unknown_scene_option_keys(scene_options):
    """
    Gets keys of a scene options dictionary that have no definition (only editable as raw data).

    Args:
        scene_options (dict): Scene options dictionary.

    Returns:
        list: Unknown keys, in the order they appear in the dictionary.
    """
    if not isinstance(scene_options, dict):
        return []
    known_keys = {option.key for option in SCENE_OPTIONS}
    return [key for key in scene_options.keys() if key not in known_keys]


def get_updated_scene_options(scene_options, key, is_enabled, value=None):
    """
    Gets a copy of the scene options with one option enabled (set) or disabled (removed).
    A copy is returned, so references to the original dictionary are not affected.

    Args:
        scene_options (dict, None): Current scene options dictionary.
        key (str): Scene option key to update.
        is_enabled (bool): If True, the key is set to the value. If False, the key is removed.
        value (any, optional): Value to store. If None, the stored value or the default is used.

    Returns:
        dict: Updated copy of the scene options dictionary.
    """
    updated_options = copy.deepcopy(scene_options) if isinstance(scene_options, dict) else {}
    if not is_enabled:
        updated_options.pop(key, None)
        return updated_options
    option = get_scene_option_definition(key)
    if value is None:
        value = updated_options.get(key)
    if value is None and option:
        value = copy.deepcopy(option.default)
    if option:
        value = option.coerce_value(value)
    updated_options[key] = value
    return updated_options
