"""
Auto Rigger Model
"""

import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.core.logger as core_log
import gt.core.io as core_io
import logging

# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=False)
logger.setLevel(logging.INFO)
core_log.add_custom_log_levels()


class RiggerModel:
    def __init__(self):
        """
        Initialize the RiggerModel object.
        """
        self.project = tools_rig_frm.RigProject()

    def clear_project(self):
        """
        Re-initializes the project to an empty one.
        """
        self.project = tools_rig_frm.RigProject()

    def set_project(self, project):
        """
        Sets a new project.
        Args:
            project (RigProject): A new project to be stored in "self.project"
        """
        if not project or not isinstance(project, tools_rig_frm.RigProject):
            logger.debug(f"Unable to set project. Invalid input.")
            return
        self.project = project

    def get_project(self):
        """
        Gets the current project. (RigProject)
        Returns:
            RigProject: Current project stored in "self.project"
        """
        return self.project

    def get_modules(self):
        """
        Gets the modules stored in the current project
        Returns:
            list: A list of modules. e.g. [ModuleGeneric, ModuleGeneric, ...]
        """
        return self.project.get_modules()

    def set_modules(self, modules):
        """
        Sets the modules list directly.
        Args:
            modules (list): A list of modules (ModuleGeneric as base)
        """
        self.project.set_modules(modules=modules)

    def add_to_modules(self, module):
        """
        Adds a new item to the modules list of the current project.
        Args:
            module (ModuleGeneric, List[ModuleGeneric]): New module element to be added to the current project.
        """
        self.project.add_to_modules(module=module)

    def save_project_to_file(self, path):
        """
        Save the current project to the provided path (JSON format)
        Args:
            path (str): The file path where the project data will be saved.
        """
        data = self.project.get_project_as_dict()
        core_io.write_json(path=path, data=data)

    def load_project_from_file(self, path):
        """
        Loads a new project from the provided path (path should point to a project description (JSON)
        Args:
            path (str): Path to the project description (JSON format)
        """
        data = core_io.read_json_dict(path)
        loaded_project = tools_rig_frm.RigProject()
        loaded_project.read_data_from_dict(data)
        self.project = loaded_project


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = RiggerModel()
