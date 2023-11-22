"""
Auto Rigger Model
"""
from gt.tools.auto_rigger.template_biped import create_template_biped
from gt.utils.data_utils import write_json, read_json_dict
from gt.tools.auto_rigger.rig_framework import RigProject
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RiggerModel:
    def __init__(self):
        """
        Initialize the RiggerModel object.
        """
        self.project = create_template_biped()  # TODO TEMP
        # self.project = RigProject()  # TODO TEMP

    def clear_project(self):
        """
        Re-initializes the project to an empty one.
        """
        self.project = RigProject()

    def set_project(self, project):
        """
        Sets a new project.
        Args:
            project (RigProject): A new project to be stored in "self.project"
        """
        if not project or not isinstance(project, RigProject):
            logger.debug(f'Unable to set project. Invalid input.')
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
        """
        data = self.project.get_project_as_dict()
        write_json(path=path, data=data)

    def load_project_from_file(self, path):
        """
        Loads a new project from the provided path (path should point to a project description (JSON)
        Args:
            path (str): Path to the project description (JSON format)
        """
        self.project = RigProject()
        data = read_json_dict(path)
        self.project.read_data_from_dict(data)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = RiggerModel()
