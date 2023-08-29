"""
Resource Library Model
"""
from gt.ui.resource_library import parse_rgb_numbers
from gt.ui.qt_utils import create_color_pixmap
from gt.ui import resource_library
from PySide2.QtGui import QColor
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ResourceLibraryModel:
    def __init__(self):
        """
        Initialize the ResourceLibraryModel object.
        """
        self.colors = {}
        self.import_package_colors()
        # self.import_controls_library()

    def get_colors(self):
        """
        Get all colors
        Returns:
            dict: A list containing all the colors in the ResourceLibraryModel.
        """
        return self.colors

    def add_color(self, color_key, color):
        """
        Adds a new color object to the color list
        Args:
            color_key (str): Color key for the color dictionary. Must be unique or it will overwrite other colors.
            color (QColor): QColor representing the color.
        """
        self.colors[color_key] = color

    def import_package_colors(self):
        """
        Imports all control curves found in "control_utils.Controls" to the ResourceLibraryModel controls list
        """
        class_attributes = vars(resource_library.Color.RGB)
        attr_keys = [attr for attr in class_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for attr_key in attr_keys:
            color_str = getattr(resource_library.Color.RGB, attr_key)
            color_tuple = parse_rgb_numbers(color_str)
            if color_tuple and len(color_tuple) >= 3:
                if len(color_tuple) == 4:
                    r, g, b, a = color_tuple
                else:
                    a = 255
                    r, g, b = color_tuple
                color = QColor(r, g, b, a)
                self.add_color(color_key=attr_key, color=color)

    def get_preview_image(self, item):
        """
        Gets the preview image path for the given curve name.

        Args:
            item (Any): Library item to retrieve the preview from

        Returns:
            str: The path to the preview image, or the path to the default missing file icon if the image is not found.
        """
        if isinstance(item, QColor):
            return create_color_pixmap(item)
        return resource_library.Icon.curve_library_missing_file

    def save_resource(self, item):
        print(item)
        if isinstance(item, QColor):
            # Create an image with the specified color
            # import maya.cmds as cmds
            # file_name = cmds.fileDialog2(fileFilter="PNG Image (*.png);;All Files (*)",
            #                              dialogStyle=2,
            #                              okCaption='Export',
            #                              caption='Exporting Color Resource') or []
            # if file_name and len(file_name) > 0:
            #      file_name = file_name[0]
            file_name = r"C:\Users\guilherme.trevisan\Desktop\test.png"

            pixmap = create_color_pixmap(item)

            if file_name:
                # Save the image
                pixmap.save(file_name)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = ResourceLibraryModel()
    print(model.get_colors())
    # items = model.get_curve_names(formatted=True)
    # print(model.get_user_curves())
