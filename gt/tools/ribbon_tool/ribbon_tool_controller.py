"""
Ribbon Tool Controller
"""
from gt.utils.iterable_utils import sanitize_maya_list
from gt.utils.naming_utils import get_short_name
from gt.utils.feedback_utils import FeedbackMessage
from gt.utils.surface_utils import Ribbon
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RibbonToolController:
    def __init__(self, view, model=None):
        """
        Initialize the RibbonToolController object.

        Args:
            view: The view object to interact with the user interface.
            model: The CurveToPythonModel object used for data manipulation.
        """
        self.model = model
        self.view = view
        self.view.controller = self

        # Surface Data and Mode Variables
        self.source_mode = 0
        self.source_data = None

        # Connections
        self.view.help_btn.clicked.connect(self.open_help)
        self.view.mode_combo_box.currentIndexChanged.connect(self.on_mode_change)
        self.view.surface_data_set_btn.clicked.connect(self.set_source_data)
        self.view.surface_data_clear_btn.clicked.connect(self.clear_source_data)
        self.view.surface_data_content_btn.clicked.connect(self.select_source_data)
        self.view.create_ribbon_btn.clicked.connect(self.create_ribbon)
        self.view.show()

    def on_mode_change(self):
        """
        Called when the mode combobox is updated.
        It clears the source data value and stores the new source mode index.
        """
        self.source_mode = self.view.get_mode_combobox_index()
        self.source_data = None

    def set_source_data(self):
        """ Sets the source data by using selection and updating the button view """
        if not self.source_mode:
            return
        if self.source_mode == 1:  # Surface Input
            selection = self.__get_selection_surface()
            if selection:
                self.source_data = selection[0]
                short_name = get_short_name(long_name=selection[0])
                self.view.set_source_data_button_values(text=short_name)
        if self.source_mode == 2:  # List Input
            selection = self.__get_selection_transform_list()
            if selection:
                self.source_data = selection
                message = f"{len(selection)} objects"
                self.view.set_source_data_button_values(text=message)

    def clear_source_data(self):
        """ Clears source data button by changing its colors and text back to "No Data"."""
        self.source_data = None
        self.view.clear_source_data_button()

    def select_source_data(self):
        """ Selects the items stored in the source data. This is the input surface or a transform list. """
        if self.source_data:
            import maya.cmds as cmds
            cmds.select(self.source_data)

    @staticmethod
    def open_help():
        """ Opens package docs """
        from gt.utils.request_utils import open_package_docs_url_in_browser
        open_package_docs_url_in_browser()

    @staticmethod
    def __get_selection_surface():
        """
        Gets selection while warning the user in case nothing is elected
        Returns:
         list: Selection or empty list when nothing is selected.
        """
        import maya.cmds as cmds
        selection = cmds.ls(selection=True) or []
        if len(selection) == 0 or len(selection) > 1 :
            cmds.warning(f'Please select one surface and try again.')
            return []
        return selection

    @staticmethod
    def __get_selection_transform_list():
        """
        Gets selection while warning the user in case nothing is elected
        Returns:
         list: Selection or empty list when nothing is selected.
        """
        import maya.cmds as cmds
        selection = cmds.ls(selection=True) or []
        if len(selection) <= 1:
            cmds.warning(f'Please select two or more transforms and try again.')
            return []
        return selection

    def create_ribbon(self):
        """
        Create ribbon using view settings
        """
        prefix = self.view.get_prefix()
        num_ctrls = self.view.get_num_controls_value()
        num_joints = self.view.get_num_joints_value()
        dropoff_rate = self.view.get_dropoff_rate_value()
        span_multiplier = self.view.get_span_multiplier_value()
        equidistant = self.view.is_equidistant_checked()
        add_fk = self.view.is_add_fk_checked()
        parent_skin_joints = self.view.is_parent_skin_joints_checked()
        constraint_source = self.view.is_constraint_source_checked()
        # Create Ribbon Factory
        ribbon_factory = Ribbon(prefix=prefix,
                                num_controls=num_ctrls,
                                num_joints=num_joints,
                                equidistant=equidistant,
                                add_fk=add_fk)
        ribbon_factory.set_dropoff_rate(rate=dropoff_rate)
        ribbon_factory.set_bind_joints_parenting(parenting=parent_skin_joints)
        ribbon_factory.set_surface_span_multiplier(span_multiplier=span_multiplier)
        if self.source_mode == 1 or self.source_mode == 2:
            ribbon_factory.set_surface_data(surface_data=self.source_data, is_driven=constraint_source)
        function_name = 'Build Ribbon'
        import maya.cmds as cmds
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        try:
            ribbon_factory.build()
        except Exception as e:
            raise e
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=function_name)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
