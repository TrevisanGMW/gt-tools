from PySide2.QtCore import QPoint
from PySide2.QtGui import QFont, QColor
from PySide2.QtWidgets import QApplication, QDialog, QWidget
from unittest.mock import patch, MagicMock, Mock
from PySide2 import QtGui, QtCore
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Script
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.ui.qt_utils import MayaWindowMeta
from gt.ui import qt_utils


class TestQtUtilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if not app:
            cls.app = QApplication(sys.argv)

    @patch('gt.ui.qt_utils.is_script_in_interactive_maya', MagicMock(return_value=True))
    def test_base_inheritance_default(self):
        """
        Test that MayaWindowMeta sets 'base_inheritance' to QDialog by default.
        """
        new_class = MayaWindowMeta('TestBaseInheritanceDefault', (object,), {})
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, QDialog))

    @patch('gt.ui.qt_utils.is_script_in_interactive_maya', MagicMock(return_value=True))
    @patch('gt.ui.qt_utils.is_system_macos', MagicMock(return_value=False))
    def test_base_inheritance_non_macos(self):
        new_class = MayaWindowMeta(name='TestBaseInheritanceNonMacOS', bases=(object,), attrs={})
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, QDialog))

    @patch('gt.ui.qt_utils.is_script_in_interactive_maya', MagicMock(return_value=True))
    def test_base_inheritance_widget(self):
        from PySide2.QtWidgets import QWidget
        new_class = MayaWindowMeta(name='TestBaseInheritance', bases=(object,), attrs={}, base_inheritance=(QWidget,))
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, QWidget))

    @patch('gt.utils.system_utils.import_from_path')
    @patch('gt.ui.qt_utils.get_maya_main_window')
    def test_with_valid_class_type(self, mock_get_maya_main_window, mock_import_from_path):
        mock_maya_window = MagicMock()
        mock_maya_window.findChildren.return_value = ["child_one", "child_two"]
        mock_import_from_path.return_value = Mock()
        mock_get_maya_main_window.return_value = mock_maya_window

        # Call the function
        result = qt_utils.get_maya_main_window_qt_elements(Mock())

        # Expected result
        expected = ["child_one", "child_two"]

        # Assert the result
        self.assertEqual(result, expected)

    def test_close_ui_elements_success(self):
        # Create mock UI elements
        ui_element1 = Mock()
        ui_element2 = Mock()

        # Call the function with the mock elements
        obj_list = [ui_element1, ui_element2]
        qt_utils.close_ui_elements(obj_list)

        # Assert that close() and deleteLater() methods were called for each UI element
        ui_element1.close.assert_called_once()
        ui_element1.deleteLater.assert_called_once()
        ui_element2.close.assert_called_once()
        ui_element2.deleteLater.assert_called_once()

    @patch.object(QtGui.QCursor, 'pos', return_value=QtCore.QPoint(100, 200))
    def test_get_cursor_position_no_offset(self, mock_cursor):
        expected = QtCore.QPoint(100, 200)
        result = qt_utils.get_cursor_position()
        self.assertEqual(expected, result)

    @patch.object(QtGui.QCursor, 'pos', return_value=QtCore.QPoint(100, 200))
    def test_get_cursor_position_with_offset(self, mock_cursor):
        offset_x = 10
        offset_y = 20
        expected = QtCore.QPoint(110, 220)
        result = qt_utils.get_cursor_position(offset_x, offset_y)
        self.assertEqual(expected, result)

    @patch('gt.ui.qt_utils.get_main_window_screen_number', return_value=0)
    @patch.object(QApplication, 'screens')
    def test_get_screen_center(self, mock_screens, mock_get_main_window_screen_number):
        expected = QPoint(100, 200)
        mocked_xy = MagicMock()
        mocked_xy.x.return_value = 100
        mocked_xy.y.return_value = 200
        mocked_center = MagicMock()
        mocked_center.center.return_value = mocked_xy
        mocked_geometry = MagicMock()
        mocked_geometry.geometry.return_value = mocked_center
        mock_screens.return_value = [mocked_geometry]
        result = qt_utils.get_screen_center()
        self.assertEqual(expected, result)

    @patch('gt.ui.qt_utils.QtGui.QFont', return_value="mocked_font")
    @patch('gt.ui.qt_utils.QApplication.instance', return_value=MagicMock())
    @patch('gt.ui.qt_utils.QtGui.QFontDatabase.addApplicationFontFromData', return_value=0)
    @patch('gt.ui.qt_utils.QtGui.QFontDatabase.applicationFontFamilies', return_value=['CustomFont'])
    def test_load_custom_font_success(self, mock_font_from_data, mock_app_font_families, mock_app, mock_font):
        custom_font = qt_utils.load_custom_font('custom_font.ttf',
                                                point_size=12, weight=QFont.Bold, italic=True)
        expected_font = "mocked_font"
        self.assertEqual(expected_font, custom_font)

    def test_font_available(self):
        # Test if a font that should be available returns True
        font_name = "Arial"
        expected_result = True
        result = qt_utils.is_font_available(font_name)
        self.assertEqual(result, expected_result)

    def test_font_not_available(self):
        # Test if a font that should not be available returns False
        font_name = "NonExistentFont123"
        expected_result = False
        result = qt_utils.is_font_available(font_name)
        self.assertEqual(result, expected_result)

    @patch('gt.ui.qt_utils.is_font_available', return_value=True)
    @patch('gt.ui.qt_utils.QApplication.instance')
    def test_get_font_with_font_name(self, mock_instance, mock_is_font_available):
        mock_instance.return_value = MagicMock()

        font_name = 'Arial'
        font = qt_utils.get_font(font_name)

        expected_font = QtGui.QFont(font_name)

        self.assertEqual(font, expected_font)

    @patch('gt.ui.qt_utils.is_font_available', return_value=False)
    @patch('gt.ui.qt_utils.load_custom_font', return_value=QtGui.QFont('CustomFont'))
    @patch('gt.ui.qt_utils.QApplication.instance')
    def test_get_font_with_font_path(self, mock_instance, mock_load_custom_font, mock_is_font_available):
        mock_instance.return_value = MagicMock()
        from gt.ui import resource_library
        result = qt_utils.get_font(resource_library.Font.roboto)
        expected_font = QtGui.QFont('CustomFont')
        self.assertEqual(expected_font, result)

    @patch('gt.ui.qt_utils.QApplication.instance')
    def test_get_font_invalid_font(self, mock_instance):
        mock_instance.return_value = MagicMock()

        invalid_font = 123  # Invalid input type
        font = qt_utils.get_font(invalid_font)

        expected_font = QtGui.QFont()  # Default font

        self.assertEqual(font, expected_font)

    def test_get_qt_color_valid_hex_color(self):
        # Test with a valid hex color
        expected = QColor("#FF0000")
        result = qt_utils.get_qt_color("#FF0000")
        self.assertEqual(expected, result)

    def test_get_qt_color_valid_color_name(self):
        # Test with a valid color name
        expected = QColor("red")
        result = qt_utils.get_qt_color("red")
        self.assertEqual(expected, result)

    def test_get_qt_color_invalid_color_input(self):
        # Test with an invalid color input
        expected = None
        result = qt_utils.get_qt_color("invalid_color")
        self.assertEqual(expected, result)

    def test_get_qt_color_color_object_input(self):
        # Test with a QColor object as input
        input_color = QColor("#00FF00")
        expected = input_color
        result = qt_utils.get_qt_color(input_color)
        self.assertEqual(expected, result)

    def test_get_qt_color_none_input(self):
        # Test with None as input
        expected = None
        result = qt_utils.get_qt_color(None)
        self.assertEqual(expected, result)

    def test_get_qt_color_library(self):
        # Test with None as input
        from gt.ui import resource_library
        expected = QColor(resource_library.Color.RGB.red)
        result = qt_utils.get_qt_color(resource_library.Color.RGB.red)
        self.assertEqual(expected, result)

    @patch('gt.ui.qt_utils.QDesktopWidget')
    def test_resize_to_screen_valid_percentage(self, mock_desktop_widget):
        mock_screen = MagicMock()
        mock_screen.width.return_value = 100
        mock_screen.height.return_value = 200
        mock_geo = MagicMock()
        mock_geo.availableGeometry.return_value = mock_screen
        mock_desktop_widget.return_value = mock_geo
        window = MagicMock()
        qt_utils.resize_to_screen(window, percentage=50)
        expected_width = 50
        expected_height = 100
        self.assertEqual(window.setGeometry.call_args[0][2], expected_width)
        self.assertEqual(window.setGeometry.call_args[0][3], expected_height)

    def test_resize_to_screen_invalid_percentage(self):
        window = Mock()
        with self.assertRaises(ValueError):
            qt_utils.resize_to_screen(window, percentage=110)
            