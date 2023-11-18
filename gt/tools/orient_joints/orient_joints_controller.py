"""
Orient Joints Controller
"""
from gt.utils.attr_utils import get_user_attr_to_python, get_trs_attr_as_python, get_trs_attr_as_formatted_string
from gt.utils.system_utils import execute_python_code
from gt.utils.misc_utils import create_shelf_button
from gt.utils.feedback_utils import FeedbackMessage
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OrientJointsController:
    def __init__(self, view):
        """
        Initialize the OrientJointsController object.

        Args:
            view: The view object to interact with the user interface.
        """
        self.view = view
        self.view.controller = self

        # # Connections
        self.view.help_btn.clicked.connect(self.open_help)
        # self.view.show_axis_btn.clicked.connect(self.show_axis)
        # self.view.hide_axis_btn.clicked.connect(self.hide_axis)
        # self.view.copy_parent_btn.clicked.connect(self.copy_parent_btn)
        # self.view.copy_world_btn.clicked.connect(self.copy_world_btn)
        # self.view.orient_joints_btn.clicked.connect(self.orient_joints_btn)
        self.view.show()

    @staticmethod
    def open_help():
        """ Opens package docs """
        from gt.utils.request_utils import open_package_docs_url_in_browser
        open_package_docs_url_in_browser()

    @staticmethod
    def __get_selection():
        """
        Gets selection while warning the user in case nothing is elected
        Returns:
            list: Selection or empty list when nothing is selected.
        """
        import maya.cmds as cmds
        selection = cmds.ls(selection=True) or []
        if len(selection) == 0:
            cmds.warning(f'Please select at least one object and try again.')
            return []
        return selection


if __name__ == "__main__":
    print('Run it from "__init__.py".')

