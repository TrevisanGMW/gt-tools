"""
Auto Rigger Model
"""
from gt.tools.auto_rigger.template_biped import create_template_biped
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

    def set_project(self, project):
        if not project or not isinstance(project, RigProject):
            logger.debug(f'Unable to set project. Invalid input.')
            return
        self.project = project

    def get_project(self):
        return self.project

    def get_modules(self):
        return self.project.get_modules()

    def save_project_to_file(self):
        pass  # TODO

    def load_project_from_file(self):
        pass  # TODO


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = RiggerModel()
