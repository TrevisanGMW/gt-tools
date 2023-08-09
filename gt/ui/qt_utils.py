from PySide2.QtWidgets import QApplication, QWidget, QDesktopWidget
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


def resize_to_screen(window, percentage=20, width_percentage=None, height_percentage=None):
    """
    Resizes the window to match a percentage of the screen size.

    Args:
        window (QDialog, any): Window to be resized.
        percentage (int, optional): The percentage of the screen size that the window should inherit.
                                    Must be a value between 0 and 100. Default is 20.
        width_percentage (int, optional): If provided, it will overwrite general set percentage when setting width
        height_percentage (int, optional): If provided, it will overwrite general set percentage when setting height

    Raises:
        ValueError: If the percentage is not within the range [0, 100].
    """
    if not 0 <= percentage <= 100:
        raise ValueError("Percentage should be between 0 and 100")

    screen_geometry = QDesktopWidget().availableGeometry(window)
    width = screen_geometry.width() * percentage / 100
    height = screen_geometry.height() * percentage / 100
    if height_percentage:
        height = screen_geometry.height() * height_percentage / 100
    if width_percentage:
        width = screen_geometry.height() * width_percentage / 100
    window.setGeometry(0, 0, width, height)


def center_window(window):
    """
    Moves the given window to the center of the screen.

    Args:
        window (QDialog, any): The window to be centered on the screen.
    """
    rect = window.frameGeometry()
    center_position = get_screen_center()
    rect.moveCenter(center_position)
    window.move(rect.topLeft())


def update_formatted_label(target_label,
                           new_title,
                           new_text_output,
                           title_size=3,
                           title_color="grey",
                           version_size=4,
                           version_color="white",
                           overall_alignment="center"):
    """
    Updates the target QLabel with formatted text containing a title and text output.

    Args:
       target_label (QtWidgets.QLabel): The QLabel to update with the formatted text.
       new_title (str): The title to be displayed before the new_text_output.
       new_text_output (str): The text output to be displayed after the new_title.
       title_size (int, optional): The font size of the title. Default is 3.
       title_color (str, optional): The color of the title. Default is "grey".
       version_size (int, optional): The font size of the text output. Default is 4.
       version_color (str, optional): The color of the text output. Default is "white".
       overall_alignment (str, optional): The overall alignment of the formatted text. Default is "center".
                                          Possible values are "left", "center", and "right".
    """
    _html = f"<html><div style='text-align:{overall_alignment};'>"
    _html += f"<font size='{str(title_size)}' color='{title_color}'>{new_title}: </font>"
    _html += f"<b><font size='{str(version_size)}' color='{version_color}'>{new_text_output}</font></b>"
    _html += "</div></html>"
    target_label.setText(_html)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    out = None
    print(out)
