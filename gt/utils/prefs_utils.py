"""
Preferences Utilities - Settings and Getting persistent settings using JSONs
This script should not directly import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.system_utils import get_maya_preferences_dir, get_system
from gt.utils.data_utils import write_json, read_json_dict
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
        if location_dir:
            if os.path.exists(location_dir) and os.path.isdir(location_dir):
                self.filename = os.path.join(location_dir, f'{prefs_name}.{PACKAGE_PREFS_EXT}')
        else:
            _maya_preferences_dir = get_maya_preferences_dir(get_system())
            _package_parent_dir = os.path.join(_maya_preferences_dir, PACKAGE_NAME)
            _prefs_dir = os.path.join(_package_parent_dir, PACKAGE_PREFS_DIR)
            self.filename = os.path.join(_prefs_dir, f'{prefs_name}.{PACKAGE_PREFS_EXT}')
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

    def get_raw_json(self):
        """
        Returns the entire raw JSON data as a dictionary.

        Returns:
            dict: The raw JSON data as a dictionary.
        """
        return self.preferences

    def has_key(self, key):
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
            key (str): The key to set the float value in preferences.
            value (float): The float value to be set for the given key.
        """
        self.preferences[key] = float(value)

    def set_int(self, key, value):
        """
        Sets a single integer value for the preference identified by the given key.

        Args:
            key (str): The key to set the integer value in preferences.
            value (int): The integer value to be set for the given key.
        """
        self.preferences[key] = int(value)

    def set_string(self, key, value):
        """
        Sets a single string value for the preference identified by the given key.

        Args:
            key (str): The key to set the string value in preferences.
            value (str): The string value to be set for the given key.
        """
        self.preferences[key] = str(value)

    # ------------------------------------ Load/Save ------------------------------------

    def load(self):
        """
        Loads preferences from the JSON file if it exists.
        """
        if os.path.exists(self.filename):
            self.preferences = read_json_dict(path=self.filename)

    def save(self):
        """
        Saves all modified preferences to the JSON file.
        """
        _prefs_dir = os.path.dirname(self.filename)
        if not os.path.isdir(_prefs_dir):
            os.makedirs(_prefs_dir)
            logger.debug(f'Prefs directory was missing and was created when saving: {_prefs_dir}')
        write_json(path=self.filename, data=self.preferences)

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
        _prefs_dir = os.path.dirname(self.filename)
        if os.path.exists(_prefs_dir) and purge_preferences:
            logger.debug(f'Purging all preferences from: "{_prefs_dir}"')
            shutil.rmtree(_prefs_dir)
            return True
        return False


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
