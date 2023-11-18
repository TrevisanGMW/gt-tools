"""
Orient Joints Controller
"""
from gt.utils.attr_utils import get_user_attr_to_python, get_trs_attr_as_python, get_trs_attr_as_formatted_string
from gt.utils.system_utils import execute_python_code
from gt.utils.misc_utils import create_shelf_button
from gt.utils.feedback_utils import FeedbackMessage
from gt.utils.joint_utils import orient_joint
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
        self.view.show_axis_btn.clicked.connect(self.show_axis)
        self.view.hide_axis_btn.clicked.connect(self.hide_axis)
        self.view.copy_parent_btn.clicked.connect(self.copy_parent)
        self.view.copy_world_btn.clicked.connect(self.copy_world)
        self.view.orient_joints_btn.clicked.connect(self.orient_joints)
        self.view.show()

    @staticmethod
    def _get_selection(hierarchy=True, type_filter=None):
        """
        Gets selection while warning the user in case nothing is elected
        Args:
            hierarchy (bool, optional): If True, it will also select hierarchy before querying the selection.
            type_filter (str, optional): If provided, it will filter to include only items of this type
        Returns:
            list: Selection or empty list when nothing is selected.
        """
        import maya.cmds as cmds
        _current = cmds.ls(selection=True) or []
        if hierarchy:
            cmds.select(hierarchy=True)
        if type_filter and isinstance(type_filter, str):
            selection = cmds.ls(selection=True, typ=type_filter) or []
        else:
            selection = cmds.ls(selection=True) or []
        if _current:
            try:
                cmds.select(_current)
            except Exception as e:
                logger.debug(f'Unable to recover previous selection. Issue: {e}')
        if len(selection) == 0:
            cmds.warning(f'Please select at least one object and try again.')
            return []
        return selection

    def show_axis(self):
        print("show_axis called")

    def hide_axis(self):
        print("hide_axis called")

    def copy_parent(self):
        print("copy_parent called")

    def copy_world(self):
        print("copy_world called")

    def orient_joints(self):
        """
        Orient joints according to provided view settings
        """
        selection = self._get_selection(hierarchy=self.view.is_selecting_hierarchy(), type_filter="joint")
        aim_axis = self.view.get_aim_axis_tuple()
        up_axis = self.view.get_up_axis_tuple()
        up_dir = self.view.get_up_dir_tuple()
        orient_joint(joint_list=selection, aim_axis=aim_axis, up_axis=up_axis, up_dir=up_dir)


if __name__ == "__main__":
    print('Run it from "__init__.py".')

