"""
Multi-File Importer Constants

Option values, setting keys and defaults shared by the model, view, controller and services.
This module is pure Python and safe to import outside Maya.
"""

TOOL_NAME = "Multi-File Importer"
PREFS_FILENAME = "multi_file_importer"
PREFS_KEY_SETTINGS = "settings"
PREFS_KEY_FORMAT_SETTINGS = "format_settings"
PREFS_KEY_SECTIONS = "sections"
PREFS_KEY_LAST_DIRECTORY = "last_directory"
PREFS_KEY_FILES = "files"
PREFS_KEY_SELECTED_FORMAT = "selected_format"
EXPORT_TOOL_KEY = "multi_file_importer"
EXPORT_VERSION = 1
EXPORT_FILE_FILTER = "Multi-File Importer Settings (*.json);;All Files (*)"

# ------------------------------------------------------------------ statuses
STATUS_PENDING = "Pending"
STATUS_IMPORTED = "Imported"
STATUS_WARNING = "Warning"
STATUS_FAILED = "Failed"
STATUS_SKIPPED = "Skipped"
STATUS_CANCELLED = "Cancelled"
FINISHED_STATUSES = [STATUS_IMPORTED, STATUS_WARNING, STATUS_FAILED, STATUS_SKIPPED, STATUS_CANCELLED]

# ------------------------------------------------------------------ choices
FILTER_ALL = "All Supported"

SORT_NAME = "By Name"
SORT_FOLDER = "By Folder and Name"
SORT_REVERSE = "Reverse Order"
SORT_MODES = [SORT_NAME, SORT_FOLDER, SORT_REVERSE]

LOAD_MODE_IMPORT = "Import"
LOAD_MODE_REFERENCE = "Reference"
LOAD_MODES = [LOAD_MODE_IMPORT, LOAD_MODE_REFERENCE]

NAMESPACE_NONE = "None"
NAMESPACE_FILE_NAME = "File Name"
NAMESPACE_CUSTOM = "Custom"
NAMESPACE_MODES = [NAMESPACE_NONE, NAMESPACE_FILE_NAME, NAMESPACE_CUSTOM]

FAILURE_SKIP = "Skip File"
FAILURE_STOP = "Stop Import"
FAILURE_POLICIES = [FAILURE_SKIP, FAILURE_STOP]

NAME_TOKEN = "{name}"
INDEX_TOKEN = "{index}"
NAME_TOKENS = [NAME_TOKEN, INDEX_TOKEN]

OFFSET_NONE = "None"
OFFSET_LINE = "Line"
OFFSET_GRID = "Grid"
OFFSET_MODES = [OFFSET_NONE, OFFSET_LINE, OFFSET_GRID]

GRID_PLANE_XZ = "XZ (Floor)"
GRID_PLANE_XY = "XY (Wall)"
GRID_PLANES = [GRID_PLANE_XZ, GRID_PLANE_XY]

SOURCE_KEEP = "Keep Current"
SOURCE_FIRST = "First File"
SOURCE_LAST = "Last File"
SOURCE_CUSTOM = "Custom"
SCENE_SOURCES = [SOURCE_KEEP, SOURCE_FIRST, SOURCE_LAST, SOURCE_CUSTOM]

FRAME_RATES = ["23.976", "24", "25", "29.97", "30", "48", "50", "59.94", "60", "120"]
LINEAR_UNITS = ["mm", "cm", "m", "in", "ft", "yd"]
UP_AXES = ["y", "z"]

TIMELINE_KEYFRAMES = "Keyframes (All Files)"
TIMELINE_STORED = "Saved Ranges (All Files)"
TIMELINE_FIRST = "First File"
TIMELINE_LAST = "Last File"
TIMELINE_MANUAL = "Manual"
TIMELINE_KEEP = "Keep Current"
TIMELINE_MODES = [TIMELINE_KEYFRAMES, TIMELINE_STORED, TIMELINE_FIRST, TIMELINE_LAST, TIMELINE_MANUAL, TIMELINE_KEEP]

ANTI_ALIASING_SAMPLES = ["2", "4", "8", "16"]
SHOW = "Show"
HIDE = "Hide"
VISIBILITY_VALUES = [SHOW, HIDE]
SHADING_SMOOTH = "Smooth Shaded"
SHADING_WIREFRAME = "Wireframe"
SHADING_WIREFRAME_ON_SHADED = "Wireframe on Shaded"
SHADING_FLAT = "Flat Shaded"
SHADING_VALUES = [SHADING_SMOOTH, SHADING_WIREFRAME_ON_SHADED, SHADING_WIREFRAME, SHADING_FLAT]
LIGHTING_DEFAULT = "Default Lighting"
LIGHTING_ALL = "All Lights"
LIGHTING_FLAT = "Flat Lighting"
LIGHTING_VALUES = [LIGHTING_DEFAULT, LIGHTING_ALL, LIGHTING_FLAT]

# ------------------------------------------------------------------ settings
# Every setting is a flat scalar so the view can map one widget per key.
DEFAULT_SETTINGS = {
    # Files
    "recursive": False,
    "extension_filter": FILTER_ALL,
    # Import
    "load_mode": LOAD_MODE_IMPORT,
    "namespace_mode": NAMESPACE_FILE_NAME,
    "namespace_template": f"{NAME_TOKEN}",
    "on_failure": FAILURE_SKIP,
    # Placement
    "group_per_file": True,
    "group_template": f"{NAME_TOKEN}_grp",
    "parent_all": False,
    "parent_all_name": "imported_files_grp",
    "offset_mode": OFFSET_NONE,
    "line_step_x": 150.0,
    "line_step_y": 0.0,
    "line_step_z": 0.0,
    "grid_columns": 0,
    "grid_plane": GRID_PLANE_XZ,
    "grid_spacing_a": 150.0,
    "grid_spacing_b": 150.0,
    "auto_spacing": False,
    "auto_spacing_padding": 25.0,
    "center_layout": False,
    "protect_skinned_meshes": True,
    "create_layout_controls": False,
    "layout_controls_name": "imported_files_layout",
    # Scene settings
    "frame_rate_source": SOURCE_LAST,
    "frame_rate_custom": "30",
    "linear_unit_source": SOURCE_LAST,
    "linear_unit_custom": "cm",
    "up_axis_source": SOURCE_LAST,
    "up_axis_custom": "y",
    "timeline_mode": TIMELINE_KEYFRAMES,
    "timeline_start": 1.0,
    "timeline_end": 120.0,
    "timeline_round": True,
    "reapply_scene_settings": True,
    # Review overrides
    "review_anti_aliasing": True,
    "review_anti_aliasing_samples": "8",
    "review_textures": False,
    "review_textures_value": SHOW,
    "review_joints": False,
    "review_joints_value": HIDE,
    "review_shading": False,
    "review_shading_value": SHADING_SMOOTH,
    "review_lighting": False,
    "review_lighting_value": LIGHTING_DEFAULT,
    "review_grid": False,
    "review_grid_value": HIDE,
    "review_clip_planes": False,
    "review_clip_near": 1.0,
    "review_clip_far": 100000.0,
    "review_frame_content": True,
    "review_go_to_start": True,
    "review_clear_selection": True,
    # Scripts
    "per_file_script_enabled": False,
    "per_file_script": "",
    "post_script_enabled": False,
    "post_script": "",
    # Preferences
    "keep_file_list": False,
    "new_scene_on_import": False,
    "include_files_in_export": False,
}

CHOICE_SETTINGS = {
    "load_mode": LOAD_MODES,
    "namespace_mode": NAMESPACE_MODES,
    "on_failure": FAILURE_POLICIES,
    "offset_mode": OFFSET_MODES,
    "grid_plane": GRID_PLANES,
    "frame_rate_source": SCENE_SOURCES,
    "linear_unit_source": SCENE_SOURCES,
    "linear_unit_custom": LINEAR_UNITS,
    "up_axis_source": SCENE_SOURCES,
    "up_axis_custom": UP_AXES,
    "timeline_mode": TIMELINE_MODES,
    "review_anti_aliasing_samples": ANTI_ALIASING_SAMPLES,
    "review_textures_value": VISIBILITY_VALUES,
    "review_joints_value": VISIBILITY_VALUES,
    "review_shading_value": SHADING_VALUES,
    "review_lighting_value": LIGHTING_VALUES,
    "review_grid_value": VISIBILITY_VALUES,
}

SECTION_IMPORT = "import"
SECTION_FORMATS = "formats"
SECTION_PLACEMENT = "placement"
SECTION_SCENE = "scene"
SECTION_REVIEW = "review"
SECTION_SCRIPTS = "scripts"
SECTION_PREFERENCES = "preferences"
DEFAULT_SECTION_STATES = {
    SECTION_IMPORT: False,
    SECTION_FORMATS: False,
    SECTION_PLACEMENT: False,
    SECTION_SCENE: False,
    SECTION_REVIEW: False,
    SECTION_SCRIPTS: False,
    SECTION_PREFERENCES: False,
}

PER_FILE_SCRIPT_VARIABLES = (
    "cmds, file_path, file_index, total_files, record, nodes, root_nodes, group, "
    "namespace, reference_node, records, settings"
)
POST_SCRIPT_VARIABLES = (
    "cmds, records, imported_records, failed_records, time_range, cancelled, top_group, control_node, settings"
)
