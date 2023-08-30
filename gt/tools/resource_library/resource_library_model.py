"""
Resource Library Model
"""
from gt.ui.resource_library import parse_rgb_numbers
from gt.utils.system_utils import get_desktop_path
from gt.ui.qt_utils import create_color_pixmap
from PySide2.QtCore import QFile, QIODevice
from PySide2.QtGui import QColor, QIcon
from gt.ui import resource_library
import logging
import shutil
import sys
import os

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
        self.colors_raw = {}
        self.package_icons = {}
        self.package_icons_raw = {}
        self.maya_icons = {}
        self.maya_icons_raw = {}
        self.import_package_colors()
        self.import_package_icons()
        self.import_maya_icons()

    def get_colors(self):
        """
        Get all colors
        Returns:
            dict: A list containing all the colors in the ResourceLibraryModel.
        """
        return self.colors

    def get_package_icons(self):
        """
        Get all package icons
        Returns:
            dict: A list containing all the package icons in the ResourceLibraryModel.
        """
        return self.package_icons

    def get_maya_icons(self):
        """
        Get all Maya icons (from resource browser)
        Returns:
            dict: A list containing all the package icons in the ResourceLibraryModel.
        """
        return self.maya_icons

    def get_row_maya_icons(self):
        """
        Get all Maya icons (Raw strings) (from resource browser)
        Returns:
            dict: A list containing all the package icons in the ResourceLibraryModel.
        """
        return self.maya_icons_raw

    def add_color(self, color_key, color_str):
        """
        Adds a new color object to the color list
        Args:
            color_key (str): Color key for the color dictionary. Must be unique or it will overwrite other colors.
            color_str (str): A string with RGB+A values representing the color. e.g. "rgba(0, 0, 0, 0)"
        """
        color_tuple = parse_rgb_numbers(color_str)
        if color_tuple and len(color_tuple) >= 3:
            if len(color_tuple) == 4:
                r, g, b, a = color_tuple
            else:
                a = 255
                r, g, b = color_tuple
            color = QColor(r, g, b, a)
        self.colors_raw[color_key] = color_tuple
        self.colors[color_key] = color

    def add_package_icon(self, icon_key, icon):
        """
        Adds a new icon object to the package icons list
        Args:
            icon_key (str): Icon key for the color dictionary. Must be unique or it will overwrite other icons.
            icon (QIcon): QIcon representing the icon.
        """
        self.package_icons_raw[icon_key] = icon
        self.package_icons[icon_key] = QIcon(icon)

    def add_maya_icon(self, icon_key, icon_str):
        """
        Adds a new icon to the maya icons list
        Args:
            icon_key (str): Icon key for the color dictionary. Must be unique or it will overwrite other icons.
            icon_str (str): Maya resource string
        """
        self.maya_icons_raw[icon_key] = icon_str
        icon = QIcon(f':{icon_str}')
        if icon_str.endswith(".png"):
            try:
                pixmap = icon.pixmap(icon.actualSize(icon.availableSizes()[0]))
                scaled_pixmap = pixmap.scaled(pixmap.width() * 10, pixmap.height() * 10)
                icon = QIcon(scaled_pixmap)
            except Exception as e:
                logger.debug(f'Unable to re-scale Maya icon. Issue: {str(e)}')
        self.maya_icons[icon_key] = icon

    def import_package_colors(self):
        """
        Imports all control curves found in "control_utils.Controls" to the ResourceLibraryModel controls list
        """
        class_attributes = vars(resource_library.Color.RGB)
        attr_keys = [attr for attr in class_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for attr_key in attr_keys:
            color_str = getattr(resource_library.Color.RGB, attr_key)
            self.add_color(color_key=attr_key, color_str=color_str)

    def import_package_icons(self):
        """
        Imports all control curves found in "control_utils.Controls" to the ResourceLibraryModel controls list
        """
        class_attributes = vars(resource_library.Icon)
        attr_keys = [attr for attr in class_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for attr_key in attr_keys:
            icon_path = getattr(resource_library.Icon, attr_key)
            self.add_package_icon(icon_key=attr_key, icon=icon_path)

    def import_maya_icons(self):
        """
        Imports all control curves found in "control_utils.Controls" to the ResourceLibraryModel controls list
        """
        undesired_resources = ["ce2_icons", "ce2_python", "ce2_scripts", "qgradient", "qpdf", "qt-project.org", "qtwebchannel", "sows"]
        try:
            import maya.cmds as cmds
            for icon in cmds.resourceManager(nameFilter="*"):
                if icon not in undesired_resources:
                    self.add_maya_icon(icon_key=icon, icon_str=icon)
        except Exception as e:
            logger.debug(f'Unable to get Maya resources. Issue: {e}')

    @staticmethod
    def get_preview_image(item):
        """
        Gets the preview image path for the given curve name.

        Args:
            item (Any): Library item to retrieve the preview from

        Returns:
            str: The path to the preview image, or the path to the default missing file icon if the image is not found.
        """
        if isinstance(item, QColor):
            return create_color_pixmap(item)
        if isinstance(item, QIcon):
            return item.pixmap(512)
        return resource_library.Icon.curve_library_missing_file

    def export_resource(self, key, source=None):
        """
        Saves/Exports resource
        Args:
            key (str): Key for the resource, so it can be retrieved from the source.
            source (str, optional): Name of the source dictionary. (Must be "colors", "package_icons" or "maya_icons")
        """
        # ------------------------ Colors ------------------------
        if source == "colors":
            item = self.colors.get(key)
            if not item:
                logger.warning(f'Unable to export color resource. Missing provided key.')
                return
            # Save Dialog
            import maya.cmds as cmds
            starting_dir = os.path.join(get_desktop_path(), f'{key}.png')
            file_path = cmds.fileDialog2(fileFilter="PNG Image (*.png);;All Files (*)",
                                         dialogStyle=2,
                                         okCaption='Export',
                                         startingDirectory=starting_dir,
                                         caption='Exporting Color Resource') or []
            if file_path and len(file_path) > 0:
                file_path = file_path[0]
            else:
                logger.debug(f'Skipped color resource save operation. Invalid file path.')
                return
            pixmap = create_color_pixmap(item)
            pixmap.save(file_path)
            sys.stdout.write(f'Color sample resource exported to: {file_path}')
        # --------------------- Package Icons ---------------------
        if source == "package_icons":
            icon_path = self.package_icons_raw.get(key)
            if not icon_path:
                logger.warning(f'Unable to export package icon resource. Missing provided key.')
                return
            if not os.path.exists(icon_path):
                logger.warning(f'Unable to export package icon resource. Missing source icon.')
                return

            extension = "svg"
            file_name = ""
            try:
                file_name = os.path.basename(icon_path)
                extension = file_name.rsplit('.', 1)[-1].lower()
            except Exception as e:
                logger.debug(f'Unable to parse source extension for file dialog. Using default "SVG". Issue: {str(e)}')
            # Save Dialog
            import maya.cmds as cmds
            starting_dir = os.path.join(get_desktop_path(), file_name)
            file_path = cmds.fileDialog2(fileFilter=f'{extension.upper()} Image (*.{extension});;All Files (*)',
                                         dialogStyle=2,
                                         okCaption='Export',
                                         startingDirectory=starting_dir,
                                         caption='Exporting Icon Resource') or []
            if file_path and len(file_path) > 0:
                file_path = file_path[0]
            else:
                logger.debug(f'Skipped package icon resource save operation. Invalid file path.')
                return
            shutil.copy(icon_path, file_path)
            sys.stdout.write(f'Package icon resource exported to: {file_path}')
        # --------------------- Maya Icons ---------------------
        if source == "maya_icons":
            icon_str = self.maya_icons_raw.get(key)
            if not icon_str:
                logger.warning(f'Unable to export Maya resource. Missing provided key.')
                return
            extension = "png"
            try:
                file_name = os.path.basename(icon_str)
                extension = file_name.rsplit('.', 1)[-1].lower()
            except Exception as e:
                logger.debug(f'Unable to parse source extension for file dialog. Using default "PNG". Issue: {str(e)}')
            # Save Dialog
            import maya.cmds as cmds
            starting_dir = os.path.join(get_desktop_path(), icon_str)
            file_path = cmds.fileDialog2(fileFilter=f'{extension.upper()} Image (*.{extension});;All Files (*)',
                                         dialogStyle=2,
                                         okCaption='Export',
                                         startingDirectory=starting_dir,
                                         caption='Exporting Icon Resource') or []
            if file_path and len(file_path) > 0:
                file_path = file_path[0]
            else:
                logger.debug(f'Skipped Maya resource save operation. Invalid file path.')
                return

            # Extract Resource
            resource_file = QFile(f':{icon_str}')
            if not resource_file.exists():
                logger.debug(f'Skipped Maya resource save operation. Missing resource.')
                return
            if not resource_file.open(QIODevice.ReadOnly):
                return
            resource_data = resource_file.readAll()
            resource_file.close()

            with open(file_path, "wb") as save_file:
                save_file.write(resource_data)

            sys.stdout.write(f'Maya resource exported to: {file_path}')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = ResourceLibraryModel()
    print(model.get_package_icons())
