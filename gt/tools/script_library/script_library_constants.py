"""Constants used by the Script Library tool."""


class ScriptLibraryConstants:
    """Stores persistent keys, file formats, and icon modes for Script Library."""

    PREFS_NAME = "script_library"
    USER_FILES_SUB_FOLDER = "script_library_scripts"

    PREF_KEY_SCRIPTS = "scripts"
    PREF_KEY_EDIT_MODE = "edit_mode"
    PREF_KEY_SELECTED_SCRIPT_ID = "selected_script_id"
    PREF_KEY_LAST_DIRECTORY = "last_directory"
    PREF_KEY_SPLITTER_SIZES = "splitter_sizes"
    PREF_KEY_SHOW_DETAILS_IN_USE_MODE = "show_details_in_use_mode"
    PREF_KEY_AUTO_SAVE = "auto_save"

    ICON_MODE_DEFAULT = "default"
    ICON_MODE_PACKAGE = "package"
    ICON_MODE_CUSTOM = "custom"
    ICON_MODE_SNAPSHOT = "snapshot"
    ICON_MODES = (
        ICON_MODE_DEFAULT,
        ICON_MODE_PACKAGE,
        ICON_MODE_CUSTOM,
        ICON_MODE_SNAPSHOT,
    )

    ICON_MODE_LABELS = {
        ICON_MODE_DEFAULT: "Default Script Icon",
        ICON_MODE_PACKAGE: "Package Icon",
        ICON_MODE_CUSTOM: "Uploaded Icon",
        ICON_MODE_SNAPSHOT: "Viewport Snapshot",
    }

    SCRIPT_EXTENSION = ".py"
    SCRIPT_ARCHIVE_EXTENSION = ".gtscript"
    LIBRARY_ARCHIVE_EXTENSION = ".gtscriptlib"
    ARCHIVE_FORMAT = "gt_script_library"
    ARCHIVE_VERSION = 1
    ARCHIVE_MANIFEST = "manifest.json"
    ARCHIVE_SCRIPT_FOLDER = "scripts"
    ARCHIVE_ASSET_FOLDER = "assets"

    SUPPORTED_ICON_EXTENSIONS = (
        ".svg",
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".ico",
    )
    MAX_ARCHIVE_FILE_SIZE = 5 * 1024 * 1024
    MAX_ARCHIVE_SIZE = 25 * 1024 * 1024

    DEFAULT_SCRIPT_NAME = "new_script"
    DEFAULT_SCRIPT_CONTENT = (
        '"""Quick Script."""\n\n'
        "# Write the Python code you want to run here.\n"
    )
