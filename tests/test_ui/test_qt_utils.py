from PySide2.QtCore import QPoint
from PySide2.QtWidgets import QApplication, QDialog
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
