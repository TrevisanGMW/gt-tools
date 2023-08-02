"""
Curve Library Model
"""
from gt.utils.curve_utils import Curves, get_curve_preview_image_path
from gt.ui import resource_library
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CurveLibraryModel:
    def __init__(self):
        """
        Initialize the SampleToolModel object.
        """
        self.curves = []
        self.import_default_library()

    def add_curve(self, curve):
        """
        Add an item to the list.
        Args:
            curve (Curve): The curve to be added
        """
        self.curves.append(curve)

    def remove_indexed_curve(self, index):
        """
        Remove an item from the list based on its index.

        Args:
            index: The index of the item to be removed.

        """
        if 0 <= index < len(self.curves):
            del self.curves[index]

    def get_curves(self):
        """
        Get the list of items.
        Returns:
            list: A list containing all the items in the SampleToolModel.
        """
        return self.curves

    def get_curve_names(self, formatted=False):
        """
        Get the list of items.
        Args:
            formatted (bool, optional): If active, it will return a formatted version of the name.
                                        e.g. "circle_arrow" becomes "Circle Arrow"
        Returns:
            list: A list containing all the items in the SampleToolModel.
        """
        names = []
        for crv in self.curves:
            names.append(crv.get_name(formatted=formatted))
        return names

    def import_default_library(self):
        """
        Returns all curves found in "curve_utils.Curves"
        """
        curve_attributes = vars(Curves)
        curve_keys = [attr for attr in curve_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        curves = []
        for curve_key in curve_keys:
            curve_obj = getattr(Curves, curve_key)
            if not curve_obj:
                logger.warning(f'Missing curve: {curve_key}')
            curves.append(curve_obj)
            if not curve_obj.shapes:
                logger.warning(f'Missing shapes for a curve: {curve_obj}')
            self.add_curve(curve_obj)

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

    @staticmethod
    def get_preview_image(curve_name):
        preview_image = get_curve_preview_image_path(curve_name)
        if preview_image:
            return preview_image
        else:
            return resource_library.Icon.curve_library_missing_file


if __name__ == "__main__":
    # The model should be able to work without the controller or view
    model = CurveLibraryModel()
    model.import_default_library()
    items = model.get_curve_names(formatted=True)
    print(items)
