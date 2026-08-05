"""
Animation Retargeter Model
"""

import gt.tools.retargeter.retargeter_framework as tools_retargeter_frm
import gt.tools.retargeter.retargeter_preferences as tools_retargeter_prefs
from gt.core.io import write_json, read_json_dict
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RetargeterModel:
    def __init__(self):
        """
        Initialize the RiggerModel object.
        """
        self.project = tools_retargeter_frm.RetargeterDefinition()
        self.preferences = tools_retargeter_prefs.RetargeterPreferences()

    def get_preference(self, key, default=None):
        """Gets a persistent tool preference.

        Args:
            key (str): Preference key.
            default (object, optional): Value returned for an unknown key.

        Returns:
            object: Stored preference value.
        """
        return self.preferences.get(key, default)

    def set_preference(self, key, value, save=False):
        """Updates a persistent tool preference.

        Args:
            key (str): Preference key.
            value (object): Preference value.
            save (bool, optional): Whether to immediately write preferences.

        Returns:
            bool: True when the preference was updated.
        """
        was_updated = self.preferences.set(key, value)
        if was_updated and save:
            self.preferences.save()
        return was_updated

    def save_preferences(self):
        """Writes Retargeter preferences to disk."""
        self.preferences.save()

    # --------------------- Project ---------------------
    def clear_project(self):
        """
        Re-initializes the project to an empty one.
        """
        self.project = tools_retargeter_frm.RetargeterDefinition()

    def set_project(self, project):
        """
        Sets a new project.
        Args:
            project (RetargeterDefinition): A new project to be stored in "self.project"
        """
        if not project or not isinstance(project, tools_retargeter_frm.RetargeterDefinition):
            logger.debug(f"Unable to set project. Invalid input.")
            return
        self.project = project

    def set_source_path(self, path):
        """
        Sets the source path.
        Args:
            path (str): the source path to set.
        """
        if not os.path.isfile(path):
            logger.debug(f"Unable to set the given path. The file is invalid or missing: {path}")
            return
        self.project.set_source_path(path)

    def set_target_path(self, path):
        """
        Sets the target path.
        Args:
            path (str): the target path to set.
        """
        if not os.path.isfile(path):
            logger.debug(f"Unable to set the given path. The file is invalid or missing: {path}")
            return
        self.project.set_target_path(path)

    def set_source_namespace(self, source_namespace):
        """
        Sets the source namespace.
        Args:
            source_namespace (str): the source namespace to set.
        """
        if not isinstance(source_namespace, str):
            logger.debug("Invalid namespace. Please provide a string value.")
            return
        self.project.set_source_namespace(source_namespace)

    def set_target_namespace(self, target_namespace):
        """
        Sets the target namespace.
        Args:
            target_namespace (str): the target namespace to set.
        """
        if not isinstance(target_namespace, str):
            logger.debug("Invalid namespace. Please provide a string value.")
            return
        self.project.set_target_namespace(target_namespace)

    def get_project(self):
        """
        Gets the current project. (RetargeterDefinition)
        Returns:
            RetargeterDefinition: Current project stored in "self.project".
        """
        return self.project

    def get_source_path(self):
        """
        Gets the current source path.
        Returns:
            str: RetargeterDefinition source path.
        """
        return self.project.get_source_path()

    def get_target_path(self):
        """
        Gets the current target path.
        Returns:
            str: RetargeterDefinition target path.
        """
        return self.project.get_target_path()

    def get_source_namespace(self):
        """
        Gets the current source namespace.
        Returns:
            str: RetargeterDefinition source namespace.
        """
        return self.project.get_source_namespace()

    def get_target_namespace(self):
        """
        Gets the current target namespace.
        Returns:
            str: RetargeterDefinition target namespace.
        """
        return self.project.get_target_namespace()

    # ---------------------- Links ----------------------
    def add_link(self, link, reject_existing_targets=True):
        """
        Adds a new item to the links list of the current project.
        Args:
            link (TargetingLink): The link to be added.
            reject_existing_targets (bool, optional): If True it will reject links carrying targets that are
                                                      already present in this definition.
        """
        self.project.add_link(link=link, reject_existing_targets=reject_existing_targets)

    def remove_link(self, link):
        """
        Removes a specific TargetingLink from the list of links.

        Args:
            link (TargetingLink): The link to be removed.

        Returns:
            bool: True if it was removed, False otherwise
        """
        return self.project.remove_link(link)

    def update_links(self):
        """Updates links with model values (paths and namespaces)."""
        self.project.retarget_refresh_links_data()  # Gives namespaces and other data to links

    def get_links_health_score(self, verbose=True):
        """
        Gets a dictionary where the key is a link object and the value is the health score for the key link.
        e.g. {TargetingLink: 2, TargetingLink: 0}  # The first one is healthy, the second one is not.
        Args:
            verbose (bool, optional): If True, the logger will print warning when issues are detected.

        Returns:
            dict: A dictionary where the key is a link and the value is its health score.
                  2 = healthy (green), 1 = required fallback (yellow), 0 = unhealthy (red)
        """
        return self.project.get_links_health_score(verbose=verbose)

    def retarget_edit_mode(self, linked_mode=False):
        """Function used to edit retarget elements in the scene.

        Args:
            linked_mode (bool): if True, it creates links and applies addons.
        """
        return self.project.retarget_edit_mode(linked_mode=linked_mode)

    # ---------------------- Addons ----------------------
    def add_addon(self, addon):
        """
        Adds a TargetingLink to the list of links.

        Args:
            addon (TargetingAddon): The link to be added.
        """
        self.project.add_addon(addon)

    # ------------------- Input/Output -------------------
    def save_project_to_file(self, path):
        """
        Save the current project to the provided path (JSON format)
        Args:
            path (str): The file path where the project JSON will be saved.
        """
        data = self.project.get_definition_as_dict()
        write_json(path=path, data=data)

    def load_project_from_file(self, path):
        """
        Loads a new project from the provided path. The path should point to a project definition description (JSON)
        This function also updates the name of the definition to be the name of the loaded file. (No extension)
        Args:
            path (str): Path to the project description (JSON format)
        """
        if not path or not os.path.isfile(path):
            raise ValueError(f"Invalid path: '{path}'")

        self.project = tools_retargeter_frm.RetargeterDefinition()
        data = read_json_dict(path)
        self.project.read_data_from_dict(data)

        # Extract filename without extension and set as project name
        try:
            project_name = os.path.splitext(os.path.basename(path))[0]
            self.project.set_name(project_name)
        except Exception as e:
            logging.debug(f"Failed to set project name from file '{path}'. Issue: {e}")

    def convert_links_short_to_long(self):
        """
        Converts links (target and source) that are relying on fallback operations with their short name
        applying the long-absolute path.
        """
        if self.project.links:
            self.project.convert_link_fallbacks_to_long(targets=True, sources=True)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = RetargeterModel()

    # Test JSON Output
    import os

    desktop_path = os.path.join(os.path.expanduser(os.getenv("USERPROFILE")), "Desktop")
    test_json_path = os.path.join(desktop_path, r"retarget_definition.json")
    model.save_project_to_file(path=test_json_path)
