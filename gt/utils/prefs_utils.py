"""
Preferences Utilities - Settings and Getting persistent settings using JSONs
This script should not directly import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.system_utils import get_maya_preferences_dir, get_system, get_temp_dir
from gt.utils.data_utils import write_json, read_json_dict, write_data, delete_paths
from gt.utils.feedback_utils import FeedbackMessage
from gt.utils.setup_utils import PACKAGE_NAME
import logging
import shutil
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
PACKAGE_GLOBAL_PREFS = "package_prefs"
PACKAGE_PREFS_DIR = "prefs"
PACKAGE_PREFS_EXT = "json"


def get_prefs_dir():
    """
    Gets the path to the package prefs (preferences) directory. e.g. ".../Documents/maya/gt-tools/prefs"
    Returns:
        str: Path to package prefs dir. e.g. ".../Documents/maya/gt-tools/prefs"
    """
    _maya_preferences_dir = get_maya_preferences_dir(get_system())
    _package_parent_dir = os.path.join(_maya_preferences_dir, PACKAGE_NAME)
    _prefs_dir = os.path.join(_package_parent_dir, PACKAGE_PREFS_DIR)
    return _prefs_dir


class Prefs:
    def __init__(self, prefs_name, location_dir=None):
        """
        Initialize the Prefs class.

        Args:
            prefs_name (str): The name of the preferences file to save and load. (File extension is not necessary)
                              This name should ideally end with the suffix "_prefs" to clarify its use.
            location_dir (str, optional): Path to a folder where it should save the JSON file.
                                          By default, preferences are saved in the package installation path.
                                          e.g. "Documents/maya/gt-tools/prefs"
        """
        self.prefs_name = prefs_name
        self.sub_folder = prefs_name
        if location_dir:
            if os.path.exists(location_dir) and os.path.isdir(location_dir):
                self.file_name = os.path.join(location_dir, f'{prefs_name}.{PACKAGE_PREFS_EXT}')
        else:
            _prefs_dir = get_prefs_dir()
            self.file_name = os.path.join(_prefs_dir, f'{prefs_name}.{PACKAGE_PREFS_EXT}')
        self.preferences = {}
        self.load()

    # ------------------------------------ Getters ------------------------------------

    def get_float(self, key, default=None):
        """
        Returns a float value corresponding to key in the preference file if it exists.
        It also has a second argument for a default value, which is returned when the key doesn't exist.

        Args:
            key (str): The key to retrieve the float value from preferences.
            default (float, optional): The default value to return when the key doesn't exist. Defaults to None.

        Returns:
            float: The float value associated with the key, or the default value if the key is not found.
        """
        return self.preferences.get(key, default)

    def get_int(self, key, default=None):
        """
        Returns the value corresponding to key in the preference file if it exists.
        It also has a second argument for a default value, which is returned when the key doesn't exist.

        Args:
            key (str): The key to retrieve the integer value from preferences.
            default (int, optional): The default value to return when the key doesn't exist. Defaults to None.

        Returns:
            int: The integer value associated with the key, or the default value if the key is not found.
        """
        return self.preferences.get(key, default)

    def get_string(self, key, default=None):
        """
        Returns the value corresponding to key in the preference file if it exists.
        It also has a second argument for a default value, which is returned when the key doesn't exist.

        Args:
            key (str): The key to retrieve the string value from preferences.
            default (str, optional): The default value to return when the key doesn't exist. Defaults to None.

        Returns:
            str: The string value associated with the key, or the default value if the key is not found.
        """
        return self.preferences.get(key, default)

    def get_bool(self, key, default=None):
        """
        Returns the value corresponding to key in the preference file if it exists.
        It also has a second argument for a default value, which is returned when the key doesn't exist.

        Args:
            key (str): The key to retrieve the bool value from preferences.
            default (bool, optional): The default value to return when the key doesn't exist. Defaults to None.

        Returns:
            bool: The bool value associated with the key, or the default value if the key is not found.
        """
        if self.is_key_available(key):
            return bool(self.preferences.get(key))
        else:
            return default

    def get_raw_preferences(self):
        """
        Returns the entire preferences raw dictionary data.

        Returns:
            dict: The raw JSON data as a dictionary.
        """
        return self.preferences

    def is_key_available(self, key):
        """
        Returns True if the given key exists in Prefs, otherwise returns False.

        Args:
            key (str): The key to check for existence in preferences.

        Returns:
            bool: True if the key exists in preferences, False otherwise.
        """
        return key in self.preferences

    # ------------------------------------ Setters ------------------------------------

    def set_float(self, key, value):
        """
        Sets the float value of the preference identified by the given key.

        Args:
            key (str): The key to set the float value in preferences. (Keys should be snake_case)
            value (float): The float value to be set for the given key.
        """
        self.preferences[key] = float(value)

    def set_int(self, key, value):
        """
        Sets a single integer value for the preference identified by the given key.

        Args:
            key (str): The key to set the integer value in preferences. (Keys should be snake_case)
            value (int): The integer value to be set for the given key.
        """
        self.preferences[key] = int(value)

    def set_string(self, key, value):
        """
        Sets a single string value for the preference identified by the given key. (Keys should be snake_case)

        Args:
            key (str): The key to set the string value in preferences.
            value (str): The string value to be set for the given key.
        """
        self.preferences[key] = str(value)

    def set_bool(self, key, value):
        """
        Sets a single bool value for the preference identified by the given key. (Keys should be snake_case)

        Args:
            key (str): The key to set the string value in preferences.
            value (bool): The bool value to be set for the given key.
        """
        self.preferences[key] = bool(value)

    def set_raw_preferences(self, pref_dict):
        """
        Sets a dictionary as the current preferences

        Args:
            pref_dict (dict): The dictionary to replace the preferences with.
        """
        if isinstance(pref_dict, dict):
            self.preferences = pref_dict
        else:
            logger.warning(f"Unable to set raw preferences. Provided parameter is not a dictionary.")

    # ------------------------------------ Load/Save ------------------------------------

    def load(self):
        """
        Loads preferences from the JSON file if it exists.
        """
        if os.path.exists(self.file_name):
            self.preferences = read_json_dict(path=self.file_name)

    def save(self):
        """
        Saves all modified preferences to the JSON file.
        """
        _prefs_dir = os.path.dirname(self.file_name)
        if not os.path.isdir(_prefs_dir):
            os.makedirs(_prefs_dir)
            logger.debug(f'Missing Prefs directory created during "save" command: "{_prefs_dir}".')
        write_json(path=self.file_name, data=self.preferences)

    # ------------------------------------ Utilities ------------------------------------

    def delete_all(self):
        """
        Removes all keys and values from the preferences.
        """
        self.preferences = {}

    def delete_key(self, key):
        """
        Removes the given key from the Prefs class.

        Args:
            key (str): The key to be deleted from preferences.
        """
        if key in self.preferences:
            del self.preferences[key]
        else:
            logger.debug(f'Key "{key}" not found.')

    def purge_preferences_dir(self, purge_preferences=False):
        """
        WARNING!!!! Be careful!!! This will delete all preferences files.
        Purges the preferences' directory associated with the current filename.

        This method deletes all preferences located in the directory containing the file specified by 'self.filename',
        provided that the 'purge_preferences' flag is set to True.

        Args:
           purge_preferences (bool, optional): If True, the function will delete all preferences in the directory.
               If False or not provided, the function will not perform any deletion.

        Returns:
           bool: True if the preferences' directory was purged successfully, False otherwise.

        Note:
           The preferences' directory will only be purged if both 'self.filename' points to an existing file and
           'purge_preferences' is set to True. If 'self.filename' does not exist or 'purge_preferences' is False,
           the function will do nothing and return False.

        Example:
           # Create an instance of the class
           obj = SomeClass()

           # Set the filename attribute
           obj.filename = '/path/to/preferences/file.txt'

           # Purge preferences from the directory
           result = obj.purge_preferences_dir(purge_preferences=True)
        """
        _prefs_dir = os.path.dirname(self.file_name)
        if os.path.exists(_prefs_dir) and purge_preferences:
            logger.debug(f'Purging all preferences from: "{_prefs_dir}"')
            shutil.rmtree(_prefs_dir)
            return True
        return False

    def set_user_files_sub_folder(self, sub_folder_name):
        """
        sub_folder_name (str): Name of the sub-folder created for the user file.
                               If not provided, it will use the preferences name as the name of the sub-folder.
                               This variable will also be stored in "self.user_files_sub_folders" used to later
                               retrieve the data from the correct folder. This value can be set
        """
        if not sub_folder_name or not isinstance(sub_folder_name, str):
            logger.warning(f'Unable to set sub-folder. Invalid input. (Must be a non-empty string)')
            return
        self.sub_folder = sub_folder_name

    def write_user_file(self, file_name, content, is_json=False):
        """
        Writes user-defined file to the preferences' folder.
        NOTE: This function doesn't require "save()" to be run to create the file. It writes it immediately when called.
        Args:
            file_name (str): Name of the file to be created. This is not a path, justa  file name. e.g. "my_file.json"
            content (any): Data to write to the file. If "is_json" is active, it would be a dictionary,
                           but it's often a string or bytes.
            is_json (bool, optional): If active, it will write JSON data instead of directly writing it.
                                      When this option is active, the content must be a dictionary.
        Returns:
            str or None: Path to the generated file. None if it failed the operation.
        """
        _prefs_dir = os.path.dirname(self.file_name)
        if not os.path.isdir(_prefs_dir):
            os.makedirs(_prefs_dir)
            logger.debug(f'Missing Prefs directory created during the writing of a custom file: "{_prefs_dir}".')
        _sub_folder = os.path.join(_prefs_dir, self.sub_folder)
        if not self.sub_folder:
            _sub_folder = os.path.join(_prefs_dir, self.prefs_name)
        if not os.path.isdir(_sub_folder):
            os.makedirs(_sub_folder)
        user_file_path = os.path.join(_sub_folder, file_name)

        if is_json:
            write_json(path=user_file_path ,data=content)
        else:
            write_data(path=user_file_path, data=content)

        return user_file_path

    def get_user_file(self, file_name, verbose=False):
        """
        Gets a user file from prefs/sub-folder
        Args:
            file_name (str): Name of the file with its extension. e.g. "my_file.txt" (not a path)
            verbose (bool, optional): If active, it will give warnings when files are missing.
        Returns:
            str or None: Path to the requested file, or None if not found.
        """
        _prefs_dir = os.path.dirname(self.file_name)
        _sub_folder = os.path.join(_prefs_dir, self.sub_folder)
        if not self.sub_folder:
            _sub_folder = os.path.join(_prefs_dir, self.prefs_name)
        if not os.path.exists(_sub_folder):
            if verbose:
                logger.warning(f'Unable to retrieve user file. '
                               f'User file sub-folder does not exist. Path: "{_sub_folder}".')
            return
        folder_files = os.listdir(_sub_folder)
        if file_name in folder_files:
            return os.path.join(_sub_folder, file_name)
        else:
            if verbose:
                logger.warning(f'Requested user file not found. File: "{file_name}". - Search dir: "{_sub_folder}".')

    def get_all_user_files(self, verbose=False):
        """
        Returns a list of all user files (custom files stored in prefs/sub_folder)
        Returns:
            dict: A dictionary of files in the preferences sub-folder. Dictionary pattern: {"file_name.ext": "path"}
        """
        files_dict = {}
        _prefs_dir = os.path.dirname(self.file_name)
        _sub_folder = os.path.join(_prefs_dir, self.sub_folder)
        if not self.sub_folder:
            _sub_folder = os.path.join(_prefs_dir, self.prefs_name)
        if not os.path.exists(_sub_folder):
            if verbose:
                logger.warning(f'Unable to retrieve user files. '
                               f'User file sub-folder does not exist. Path: "{_sub_folder}".')
            return files_dict

        for filename in os.listdir(_sub_folder):
            file_path = os.path.join(_sub_folder, filename)
            if os.path.isfile(file_path):
                files_dict[filename] = file_path
        return files_dict


class PackagePrefs(Prefs):
    def __init__(self):
        """
        Creates a Prefs object with a predetermined name and location (default)
        To be used as Package Preferences (or global preferences)
        """
        super().__init__(prefs_name=PACKAGE_GLOBAL_PREFS)

    # Common Keys Start ------------------------------------------------------------------
    def set_dev_menu_visibility(self, dev_mode_state):
        """
        Sets state of development mode. When active, package shows extra options used for development.
        Args:
            dev_mode_state (bool): New state of development mode.
        """
        self.set_bool("dev_menu_visible", dev_mode_state)

    def is_dev_menu_visible(self):
        """
        Gets state of development mode. If not found it returns False
        Returns:
            bool: Stored settings for development mode
        """
        return self.get_bool("dev_menu_visible", default=False)

    def set_skip_menu_creation(self, skip_menu_creation):
        """
        Sets preference that determines if menu will be created when initializing package.
        If active, it will not build the menu.
        Args:
            skip_menu_creation (bool): New state of "skip menu creation" preference.
        """
        self.set_bool("skip_menu_creation", skip_menu_creation)

    def is_skipping_menu_creation(self):
        """
        Gets state of the "skip menu creation" preference. If not found it returns False
        Returns:
            bool: Stored settings for the key "skip menu creation"
        """
        return self.get_bool("skip_menu_creation", default=False)
    # Common Keys End ------------------------------------------------------------------


class PackageCache:
    def __init__(self, custom_cache_dir=None):
        _package_installation_dir = os.path.dirname(get_prefs_dir())
        if os.path.exists(_package_installation_dir):
            _cache_dir = os.path.join(_package_installation_dir, "cache")
        else:
            _cache_dir = os.path.join(get_temp_dir(), f'{PACKAGE_NAME}_cache')
        self.cache_dir = _cache_dir
        if custom_cache_dir and os.path.exists(custom_cache_dir):
            self.cache_dir = custom_cache_dir
        self.cache_paths = []

    def clear_cache(self):
        """
        Deletes all paths found under "cache_files" - If the "cache_dir" is empty, it is deleted too.
        """
        delete_paths(self.cache_paths)
        # Delete cache folder in case it's empty
        if os.path.exists(self.cache_dir):
            all_cache_files = os.listdir(self.cache_dir)
            if not all_cache_files:
                delete_paths(self.cache_dir)

    def get_cache_dir(self):
        """
        Gets the path to the cache directory. If the direction doesn't exist, this function creates it.
        Returns:
            str: Path to the cache directory
        """
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        return self.cache_dir

    def add_path_list(self, path_to_add):
        """
        Adds path to path list.
        Used to purge cache at the end.
        Args:
            path_to_add (str, list): Path(s) to add. Only added if it exists.
        """
        if isinstance(path_to_add, str):
            path_to_add = [path_to_add]
        for path in path_to_add:
            if os.path.exists(path):
                self.cache_paths.append(path)

    def get_cache_paths_list(self):
        """
        Gets the cache_paths list. These are the elements added to the cache folder.
        Returns:
            list: A list stored in "cache_paths"
        """
        return self.cache_paths


def toggle_dev_sub_menu():
    """
    Toggles development mode preference.
    If it's active, it becomes inactive, and vice-versa.
    """
    prefs = PackagePrefs()
    inverted_state = not prefs.is_dev_menu_visible()
    prefs.set_dev_menu_visibility(inverted_state)
    prefs.save()
    feedback = FeedbackMessage(intro='Development Menu Visibility set to:',
                               conclusion=str(inverted_state),
                               style_conclusion='color:#FF0000;text-decoration:underline;')
    feedback.print_inview_message()


def toggle_skip_menu_creation():
    """
    Toggles "skip_menu_creation" preference.
    If it's active, it becomes inactive, and vice-versa.
    """
    prefs = PackagePrefs()
    inverted_state = not prefs.is_skipping_menu_creation()
    prefs.set_skip_menu_creation(inverted_state)
    prefs.save()
    feedback = FeedbackMessage(intro='Skipping Menu Creation set to:',
                               conclusion=str(inverted_state),
                               style_conclusion='color:#FF0000;text-decoration:underline;')
    feedback.print_inview_message()


def purge_package_settings():
    """
    WARNING!!!! Be careful!!! This will delete all preferences files.
    Purges the preferences' directory associated with the package.
    """
    prefs = PackagePrefs()
    prefs.purge_preferences_dir(purge_preferences=True)
    feedback = FeedbackMessage(intro='Package preferences were',
                               conclusion="purged",
                               suffix=".",
                               style_conclusion='color:#FF0000;text-decoration:underline;')
    feedback.print_inview_message()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    test = PackageCache()
    print(test.__dict__)
    pprint(out)
