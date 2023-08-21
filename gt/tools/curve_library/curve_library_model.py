"""
Curve Library Model

This module contains the CurveLibraryModel class, which manages a library of curves. It allows adding, retrieving,
and building curves based on their names. The curves are represented as instances of the Curve class from
"gt.utils.curve_utils".

Classes:
    CurveLibraryModel: A class for managing a library of curves.
"""
import os.path

from gt.utils.control_utils import Controls, get_control_preview_image_path, Control
from gt.utils.curve_utils import Curves, get_curve_preview_image_path, Curve
from gt.ui import resource_library
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CurveLibraryModel:
    def __init__(self):
        """
        Initialize the CurveLibraryModel object.
        """
        self.base_curves = []
        self.user_curves = []  # User-defined curves
        self.controls = []
        self.import_default_library()
        self.import_controls_library()

    def is_conflicting_name(self, name):
        """
        Checks if curve name already exists in any of the lists
        Args:
            name (str): Name of the curve to check
        Returns:
            bool: True if it's conflict (already in the list), False if not.
        """
        current_names = self.get_all_curve_names()
        if name in current_names:
            return True
        return False

    def validate_curve(self, curve):
        """
        Validates object to make sure it's valid
        Args:
            curve (Curve, Control, any): A Curve, Control or any element to be validated
        Returns:
            bool: True if valid (can be built, has expected attributes, etc...), False if not.
        """
        if not curve:
            logger.debug(f'Invalid Curve detected. "None" or empty element')
            return False
        if not curve.is_curve_valid():
            logger.debug(f'Invalid Curve. Missing required elements for a curve: {curve}')
            return False
        if self.is_conflicting_name(curve.get_name()):
            logger.debug(f'Invalid Name. This curve name is already in the list. No duplicates allowed.')
            return False
        return True

    def add_base_curve(self, curve):
        """
        Add a curve to the list.
        Args:
            curve (Curve): The curve to be added
        """
        if not self.validate_curve(curve):
            logger.debug(f'Unable to add Curve to base curves. Curve failed validation.')
            return
        self.base_curves.append(curve)

    def add_user_curve(self, user_curve):
        """
        Add a curve to the list.
        Args:
            user_curve (Curve): The curve to be added
        """
        if not self.validate_curve(user_curve):
            logger.debug(f'Unable to add Curve to user-defined curves. Curve failed validation.')
            return
        self.user_curves.append(user_curve)

    def add_control(self, control):
        """
        Add a curve to the list.
        Args:
            control (Control): The curve to be added
        """
        if not self.validate_curve(control):
            logger.debug(f'Unable to add Control to control curves. Curve failed validation.')
            return
        self.controls.append(control)

    def get_base_curves(self):
        """
        Get all curves
        Returns:
            list: A list containing all the curves in the CurveLibraryModel.
        """
        return self.base_curves

    def get_user_curves(self):
        """
        Get all user-defined curves
        Returns:
            list: A list containing all the user-defined curves in the CurveLibraryModel.
        """
        return self.user_curves

    def get_controls(self):
        """
        Get all controls
        Returns:
            list: A list containing all the controls in the CurveLibraryModel.
        """
        return self.controls

    def get_all_curves(self):
        """
        Get all curves, controls and user-defined curves. (All elements stored in this model)
        Returns:
            list: A list containing all the user-defined curves in the CurveLibraryModel.
        """
        return self.base_curves + self.user_curves + self.controls

    @staticmethod
    def __get_names(obj_list, formatted=False):
        """
        Get the list of items.
        Args:
            obj_list (list): List of objects to look through (Must be Curves or Controls)
            formatted (bool, optional): If active, it will return a formatted version of the name.
                                        e.g. "circle_arrow" becomes "Circle Arrow"
        Returns:
            list: A list containing the names of the items fed through the object list.
        """
        names = []
        for crv in obj_list:
            names.append(crv.get_name(formatted=formatted))
        return names

    def get_base_curve_names(self, formatted=False):
        """
        Get the list of names from self.curves.
        Args:
            formatted (bool, optional): If active, it will return a formatted version of the name.
                                        e.g. "circle_arrow" becomes "Circle Arrow"
        Returns:
            list: A list containing all curve names in the CurveLibraryModel.
        """
        return self.__get_names(obj_list=self.get_base_curves(), formatted=formatted)

    def get_user_curve_names(self, formatted=False):
        """
        Get the list of names from self.user_curves.
        Args:
            formatted (bool, optional): If active, it will return a formatted version of the name.
                                        e.g. "circle_arrow" becomes "Circle Arrow"
        Returns:
            list: A list containing all user curve names in the CurveLibraryModel.
        """
        return self.__get_names(obj_list=self.get_user_curves(), formatted=formatted)

    def get_control_names(self, formatted=False):
        """
        Get the list of names from self.controls.
        Args:
            formatted (bool, optional): If active, it will return a formatted version of the name.
                                        e.g. "circle_arrow" becomes "Circle Arrow"
        Returns:
            list: A list containing all control names in the CurveLibraryModel.
        """
        return self.__get_names(obj_list=self.get_controls(), formatted=formatted)

    def get_all_curve_names(self, formatted=False):
        """
        Get the list of names from all curves (curves, controls, user_curves).
        Args:
            formatted (bool, optional): If active, it will return a formatted version of the name.
                                        e.g. "circle_arrow" becomes "Circle Arrow"
        Returns:
            list: A list containing all the items in the CurveLibraryModel.
        """
        all_curves = self.get_base_curves() + self.get_controls() + self.get_user_curves()
        return self.__get_names(obj_list=all_curves, formatted=formatted)

    def import_default_library(self):
        """
        Imports all curves found in "curve_utils.Curves" to the CurveLibraryModel curves list
        """
        curve_attributes = vars(Curves)
        curve_keys = [attr for attr in curve_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for curve_key in curve_keys:
            curve_obj = getattr(Curves, curve_key)
            self.add_base_curve(curve_obj)

    def import_user_curve_library(self, source_dir, reset_user_curves=True):
        """
        Imports all control curves found in the user-defined curve directory to the CurveLibraryModel user curves list
        Args:
            source_dir (str): Path to a folder with curve files.
            reset_user_curves (bool, optional): If active, user curves list will be first reset before importing.
        """
        if reset_user_curves:
            self.user_curves = []
        if not source_dir:
            logger.debug('Invalid user curves directory')
            return
        if not os.path.exists(source_dir):
            logger.debug("User curves directory is missing.")
            return
        for file in os.listdir(source_dir):
            if file.endswith(".crv"):
                try:
                    user_curve = Curve(data_from_file=os.path.join(source_dir, file))
                    if user_curve.is_curve_valid():
                        self.add_user_curve(user_curve)
                except Exception as e:
                    logger.debug(f'Failed to read user curve. Issue: {e}')

    def import_controls_library(self):
        """
        Imports all control curves found in "control_utils.Controls" to the CurveLibraryModel controls list
        """
        control_attributes = vars(Controls)
        control_keys = [attr for attr in control_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for ctrl_key in control_keys:
            control_obj = getattr(Controls, ctrl_key)
            self.add_control(control_obj)

    def build_curve_from_name(self, curve_name):
        """
        Builds a curve based on the provided name. (Curve name, not file name)
        In this context, curve is considered anything found inside "curves", "controls" or "user_curves".
        Args:
            curve_name (str): Name of the element to build. Must exist in "curves", "controls" or "user_curves".
        Returns:
            str or None: Name of the built curve
        """
        crv = self.get_curve_from_name(curve_name)
        result = None
        if crv:
            result = crv.build()
        return result

    @staticmethod
    def build_curve(curve):
        """
        Builds a curve based on the provided curve object.
        In this context, curve is considered anything found inside "curves", "controls" or "user_curves".
        Args:
            curve (Curve, Control): Curve to build
        Returns:
            str or None: Name of the built curve
        """
        result = None
        if curve and isinstance(curve, Curve):
            result = curve.build()
        return result

    def get_curve_from_name(self, curve_name):
        """
        Gets a curve based on the provided name. (Curve name, not file name)
        Args:
            curve_name (str): Name of the curve to build
        Returns:
            Curve or None: Curve object with the requested name. None if not found.
        """
        for crv in self.get_all_curves():
            if isinstance(crv, Curve) and curve_name == crv.get_name():
                return crv

    def get_preview_image(self, object_name):
        """
        Gets the preview image path for the given curve name.

        Args:
            object_name (str): Name of the curve or control

        Returns:
            str: The path to the preview image, or the path to the default missing file icon if the image is not found.
        """
        curve = self.get_curve_from_name(object_name)
        preview_image = None
        if curve and isinstance(curve, Curve):
            preview_image = get_curve_preview_image_path(object_name)
        if curve and isinstance(curve, Control):
            preview_image = get_control_preview_image_path(object_name)
        if preview_image:
            return preview_image
        else:
            return resource_library.Icon.curve_library_missing_file

    @staticmethod
    def build_control_with_custom_parameters(parameters, target_control):
        """
        Attempts to build a control using custom parameters
        Args:
            parameters (Callable, dict): Function used to get parameters or dictionary with parameters.
            target_control (Control): Control object to build
        """
        new_parameters = None
        if callable(parameters):
            new_parameters = parameters()
        elif isinstance(parameters, dict):
            new_parameters = parameters
        if new_parameters:
            try:
                target_control.set_parameters(new_parameters)
                target_control.build()
            except Exception as e:
                logger.warning(f'Unable to build curve. Issue: "{e}".')
            finally:
                target_control.reset_parameters()

    def get_potential_user_curve_from_selection(self):
        """
        Gets a user-defined curve if it's unique and valid. (Uses user selection in Maya)
        Returns:
            Curve or None: The custom curve if the curve was valid. None if it failed.
        """
        import maya.cmds as cmds
        selection = cmds.ls(selection=True) or []
        if not selection:
            cmds.warning("Nothing selected. Select a curve and try again.")
            return
        if len(selection) != 1:
            cmds.warning("Select only one object and try again.")
            return
        curve = Curve(read_existing_curve=selection[0])
        if curve.is_curve_valid():
            curve_name = curve.get_name()
            if curve_name in self.get_all_curve_names():
                cmds.warning("Unable to add curve. Curve name already exists in the library. Rename it and try again.")
                return
            return curve


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = CurveLibraryModel()
    # items = model.get_curve_names(formatted=True)
    # print(model.get_user_curves())
