"""
Curve Library Model

This module contains the CurveLibraryModel class, which manages a library of curves. It allows adding, retrieving,
and building curves based on their names. The curves are represented as instances of the Curve class from
"gt.utils.curve_utils".

Classes:
    CurveLibraryModel: A class for managing a library of curves.
"""
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
        self.curves = []
        self.import_default_library()
        self.import_controls_library()

    def add_curve(self, curve):
        """
        Add a curve to the list.
        Args:
            curve (Curve): The curve to be added
        """
        self.curves.append(curve)

    def get_curves(self):
        """
        Get all curves
        Returns:
            list: A list containing all the curves in the CurveLibraryModel.
        """
        return self.curves

    def get_curve_names(self, formatted=False):
        """
        Get the list of items.
        Args:
            formatted (bool, optional): If active, it will return a formatted version of the name.
                                        e.g. "circle_arrow" becomes "Circle Arrow"
        Returns:
            list: A list containing all the items in the CurveLibraryModel.
        """
        names = []
        for crv in self.curves:
            names.append(crv.get_name(formatted=formatted))
        return names

    def import_default_library(self):
        """
        Imports all curves found in "curve_utils.Curves" to the CurveLibraryModel list
        """
        curve_attributes = vars(Curves)
        curve_keys = [attr for attr in curve_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for curve_key in curve_keys:
            curve_obj = getattr(Curves, curve_key)
            if not curve_obj:
                logger.debug(f'Missing curve: {curve_key}')
                continue
            if not curve_obj.shapes:
                logger.debug(f'Missing shapes for a curve: {curve_obj}')
                continue
            self.add_curve(curve_obj)

    def import_controls_library(self):
        control_attributes = vars(Controls)
        control_keys = [attr for attr in control_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for ctrl_key in control_keys:
            control_obj = getattr(Controls, ctrl_key)
            if not control_obj:
                logger.debug(f'Missing control: {ctrl_key}')
                continue
            if not control_obj.is_curve_valid():
                logger.debug(f'Invalid control. Missing build function: "{ctrl_key}"')
                continue
            self.add_curve(control_obj)

    def build_curve(self, curve_name):
        """
        Builds a curve based on the provided name. (Curve name, not file name)
        Args:
            curve_name (str): Name of the curve to build
        Returns:
            str or None: Name of the built curve
        """
        crv = self.get_curve_from_name(curve_name)
        result = None
        if crv:
            result = crv.build()
        return result

    def get_curve_from_name(self, curve_name):
        """
        Gets a curve based on the provided name. (Curve name, not file name)
        Args:
            curve_name (str): Name of the curve to build
        Returns:
            Curve or None: Curve object with the requested name. None if not found.
        """
        for crv in self.curves:
            if curve_name == crv.get_name():
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


if __name__ == "__main__":
    # The model should be able to work without the controller or view
    model = CurveLibraryModel()
    # items = model.get_curve_names(formatted=True)
    print(get_control_preview_image_path("scalable_arrow"))
