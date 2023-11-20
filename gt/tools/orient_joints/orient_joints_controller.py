"""
Orient Joints Controller
"""
from gt.utils.joint_utils import orient_joint, copy_parent_orients, reset_orients
from gt.utils.display_utils import set_lra_state
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
        self.view.copy_world_btn.clicked.connect(self.reset_world)
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
        """
        Shows local rotation axis for target elements.
        """
        target = self._get_selection(hierarchy=self.view.is_selecting_hierarchy(), type_filter="joint") or []
        set_lra_state(obj_list=target, state=True)

    def hide_axis(self):
        """
        Hides local rotation axis for target elements.
        """
        target = self._get_selection(hierarchy=self.view.is_selecting_hierarchy(), type_filter="joint") or []
        set_lra_state(obj_list=target, state=False)

    def copy_parent(self):
        """
        Copies the orients from the parent of the target elements.
        """
        target = self._get_selection(hierarchy=self.view.is_selecting_hierarchy(), type_filter="joint") or []
        copy_parent_orients(joint_list=target)

    def reset_world(self):
        """
        Resets the orientation of the target elements to origin (world)
        """
        target = self._get_selection(hierarchy=self.view.is_selecting_hierarchy(), type_filter="joint") or []
        reset_orients(joint_list=target)

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

