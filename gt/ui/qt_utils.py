from PySide2.QtWidgets import QApplication, QWidget
from PySide2 import QtGui, QtCore, QtWidgets
from PySide2.QtGui import QFontDatabase, QColor
import logging
import os
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_cursor_position(offset_x=0, offset_y=0):
    """
    The current position of the mouse cursor

    Args:
        offset_x: (int) A value to offset the returned x position by - in pixels
        offset_y: (int) A value to offset the returned y position by - in pixels

    Returns:
        QPoint: the current cursor position, offset by the given x and y offset values>

    """
    cursor_position = QtGui.QCursor().pos()
    return QtCore.QPoint(cursor_position.x() + offset_x, cursor_position.y() + offset_y)


def get_screen_center():
    """
    Gets the screen center
    Returns:
        QPoint: With X and Y coordinates for the center of the screen
    """
    return QtWidgets.QDesktopWidget().availableGeometry().center()


def load_custom_font(font_path):
    """
    Loads a custom font using its path.
    NOTE: This function can only be used after loading an instance of QApplication.
    If an instance is not found, the default font is returned instead.
    Args:
        font_path (str): Path to a font file. (Accepted formats: ".ttf", "otf")
    Returns:
        QFont: A QFont object for the provided custom font or a default one if the operation failed
    """
    custom_font = QtGui.QFont()  # default font
    if QApplication.instance():
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            logger.debug(f"Failed to load the font:{font_path}")
        else:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if len(font_families) > 0:
                custom_font = QtGui.QFont(font_families[0])
    return custom_font


def is_font_available(font_name):
    """
    Checks the font QT font database to see if the font is available in the system.
    Args:
        font_name (str): The name of the font to check. For example: "Arial"
    Returns:
        bool: True if the font is available, false if it's not.
    """
    if QApplication.instance():
        font_db = QFontDatabase()
        available_fonts = font_db.families()
        return font_name in available_fonts


def get_font(font):
    """
    Function used to get QFont object from a font path or a font name.
    This will only work if an instance of a QApplication is present.
    Args:
        font (str): This is the font to load. It can be a font name or a font path.
                    If a name is provided, and it's found in the system, then a QFont object containing it is returned.
                    If a path is provided, it attempts to add it to the font database and create a QFont object for it.
    Returns:
        QFont: A QFont object with the provided font or a default QFont object in case the operation failed.
    """
    qt_font = QtGui.QFont()
    if not isinstance(font, str):
        return qt_font
    if is_font_available(font):
        qt_font = QtGui.QFont(font)
    elif os.path.exists(font) and os.path.isfile(font):
        qt_font = load_custom_font(font)
    return qt_font


def get_maya_main_window():
    """
    Finds the instance of maya's main window
    Returns:
        QWidget: The main maya widget
    """
    from shiboken2 import wrapInstance
    from maya import OpenMayaUI as OpenMayaUI
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    maya_window = wrapInstance(int(ptr), QWidget)
    return maya_window


def get_qt_color(color):
    if isinstance(color, str):
        if re.match(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", color):  # Hex pattern (e.g. "#FF0000"):
            return QColor(color)
        else:
            try:
                return QColor(color)
            except Exception as e:
                logger.error(f'Unable to create QColor. Issue: {e}')
    elif isinstance(color, QColor):
        return color
    elif color is not None:
        logger.error(f'Unable to create QColor. Unrecognized object type received: "{type(color)}"')


if __name__ == "__main__":
    import sys
    import resource_library
    app = QApplication(sys.argv)
    out = None
    # out = is_font_available(resource_library.Font.inter)
    out = get_qt_color("#FF00FF")
    print(out)
