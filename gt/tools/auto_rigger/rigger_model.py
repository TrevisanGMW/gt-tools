"""
Auto Rigger Model
"""
from gt.tools.auto_rigger.template_biped import create_template_biped
from gt.utils.data_utils import write_json, read_json_dict
from gt.tools.auto_rigger.rig_framework import RigProject
from gt.ui.file_dialog import file_dialog
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
        file_path = file_dialog(caption="Save Rig Project",
                                write_mode=False,
                                starting_directory=None,
                                file_filter="All Files (*);;",
                                ok_caption="Save Project",
                                cancel_caption="Cancel")
        if file_path:
            data = self.project.get_project_as_dict()
            write_json(path=file_path, data=data)

    def load_project_from_file(self):
        file_path = file_dialog(caption="Open Rig Project",
                                write_mode=False,
                                starting_directory=None,
                                file_filter="All Files (*);;",
                                ok_caption="Open Project",
                                cancel_caption="Cancel")
        if file_path:
            self.project = RigProject()
            data = read_json_dict(file_path)
            self.project.read_data_from_dict(data)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = RiggerModel()
    model.save_project_to_file()
