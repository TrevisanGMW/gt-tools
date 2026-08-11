import gt.ui.qt_import as ui_qt
from unittest.mock import patch, MagicMock, Mock
import unittest
import logging
import sys
import os
import types

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
from gt.ui.option_window import OptionWindow
from gt.tools.batch_processor.batch_processor_view import BatchProcessorView
from gt.tools.batch_processor.batch_processor_controller import BatchProcessorController


class TestQtUtilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = ui_qt.QtWidgets.QApplication.instance()
        if not app:
            cls.app = ui_qt.QtWidgets.QApplication(sys.argv)

    @patch("gt.core.session.is_script_in_interactive_maya", MagicMock(return_value=True))
    def test_base_inheritance_default(self):
        """
        Test that MayaWindowMeta sets 'base_inheritance' to QDialog by default.
        """
        new_class = MayaWindowMeta("TestBaseInheritanceDefault", (object,), {})
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, ui_qt.QtWidgets.QDialog))

    @patch("gt.core.session.is_script_in_interactive_maya", MagicMock(return_value=True))
    @patch("gt.utils.system.is_system_macos", MagicMock(return_value=False))
    def test_base_inheritance_non_macos(self):
        new_class = MayaWindowMeta(name="TestBaseInheritanceNonMacOS", bases=(object,), attrs={})
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, ui_qt.QtWidgets.QDialog))

    @patch("gt.core.session.is_script_in_interactive_maya", MagicMock(return_value=True))
    def test_base_inheritance_widget(self):
        widget_class = ui_qt.QtWidgets.QWidget

        new_class = MayaWindowMeta(
            name="TestBaseInheritance",
            bases=(object,),
            attrs={},
            base_inheritance=(widget_class,),
        )
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, widget_class))

    @patch("gt.utils.system.import_from_path")
    @patch("gt.ui.qt_utils.get_maya_main_window")
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

    def test_is_qt_object_valid_rejects_deleted_wrapper(self):
        widget = ui_qt.QtWidgets.QWidget()
        self.assertTrue(qt_utils.is_qt_object_valid(widget))

        ui_qt.shiboken.delete(widget)

        self.assertFalse(qt_utils.is_qt_object_valid(widget))

    def test_batch_processor_skips_unsaved_dialog_for_deleted_view(self):
        controller = Mock()
        controller.has_unsaved_changes.return_value = True
        widget = ui_qt.QtWidgets.QWidget()
        ui_qt.shiboken.delete(widget)

        result = BatchProcessorController.show_unsaved_changes_warning_dialog(controller, widget)

        expected = False
        self.assertEqual(expected, result)

    def test_batch_processor_close_callback_ignores_deleted_cpp_wrapper(self):
        stale_view = Mock()
        stale_view.close_func = Mock(
            side_effect=RuntimeError("Internal C++ object (BatchProcessorView) already deleted.")
        )

        BatchProcessorView._run_close_callback(stale_view)

        stale_view.close_func.assert_called_once()

    def test_batch_processor_close_callback_preserves_other_runtime_errors(self):
        stale_view = Mock()
        stale_view.close_func = Mock(side_effect=RuntimeError("Unexpected close failure"))

        with self.assertRaises(RuntimeError):
            BatchProcessorView._run_close_callback(stale_view)

    def test_remove_retained_workspace_windows(self):
        workspace_widget = ui_qt.QtWidgets.QWidget()
        retained_window_one = ui_qt.QtWidgets.QDialog(workspace_widget)
        retained_window_two = ui_qt.QtWidgets.QDialog(workspace_widget)
        replacement_window = ui_qt.QtWidgets.QDialog()
        workspace_pointer = ui_qt.shiboken.getCppPointer(workspace_widget)[0]

        MayaWindowMeta._remove_retained_workspace_windows(
            replacement_window,
            workspace_pointer,
        )

        expected = None
        result_one = retained_window_one.parent()
        result_two = retained_window_two.parent()
        self.assertEqual(expected, result_one)
        self.assertEqual(expected, result_two)

    def test_remove_retained_workspace_windows_preserves_replacement(self):
        workspace_widget = ui_qt.QtWidgets.QWidget()
        replacement_window = ui_qt.QtWidgets.QDialog(workspace_widget)
        workspace_pointer = ui_qt.shiboken.getCppPointer(workspace_widget)[0]

        MayaWindowMeta._remove_retained_workspace_windows(
            replacement_window,
            workspace_pointer,
        )

        expected = workspace_widget
        result = replacement_window.parent()
        self.assertEqual(expected, result)

    def test_remove_retained_workspace_windows_matches_reloaded_class_identity(self):
        workspace_widget = ui_qt.QtWidgets.QWidget()
        old_window_class = type(
            "ReloadedToolWindow",
            (ui_qt.QtWidgets.QDialog,),
            {"__module__": "gt.tools.reloaded_tool.reloaded_tool_view"},
        )
        new_window_class = type(
            "ReloadedToolWindow",
            (ui_qt.QtWidgets.QDialog,),
            {"__module__": "gt.tools.reloaded_tool.reloaded_tool_view"},
        )
        retained_window = old_window_class(workspace_widget)
        replacement_window = new_window_class()
        workspace_pointer = ui_qt.shiboken.getCppPointer(workspace_widget)[0]

        MayaWindowMeta._remove_retained_workspace_windows(
            replacement_window,
            workspace_pointer,
        )

        expected = None
        self.assertEqual(expected, retained_window.parent())

    def test_reuse_workspace_control_updates_retained_label(self):
        """Ensures a reopened tool uses the new view title for its workspace label."""
        maya_cmds = types.ModuleType("maya.cmds")
        maya_open_maya_ui = types.ModuleType("maya.OpenMayaUI")
        maya_module = types.ModuleType("maya")
        maya_module.cmds = maya_cmds
        maya_module.OpenMayaUI = maya_open_maya_ui

        workspace_control = MagicMock()

        def workspace_control_side_effect(control_name, **kwargs):
            """Provides the workspace-control query results used by the test."""
            if kwargs.get("query") and kwargs.get("exists"):
                return True
            if kwargs.get("query") and kwargs.get("visible"):
                return True
            return None

        workspace_control.side_effect = workspace_control_side_effect
        maya_cmds.workspaceControl = workspace_control
        maya_open_maya_ui.MQtUtil = MagicMock()
        maya_open_maya_ui.MQtUtil.findControl.return_value = 123

        window = MagicMock()
        window.objectName.return_value = "BatchProcessorView"
        window.windowTitle.return_value = "Batch Processor - (v1.0.0)"

        with patch.dict(
            sys.modules,
            {
                "maya": maya_module,
                "maya.cmds": maya_cmds,
                "maya.OpenMayaUI": maya_open_maya_ui,
            },
        ):
            with patch.object(MayaWindowMeta, "_attach_restored_window", return_value=True):
                result = MayaWindowMeta._reuse_workspace_control(window, "restore-script")

        expected = True
        self.assertEqual(expected, result)
        workspace_control.assert_any_call(
            "BatchProcessorViewWorkspaceControl",
            edit=True,
            label="Batch Processor - (v1.0.0)",
            uiScript="restore-script",
        )

    @patch("gt.core.session.is_script_in_interactive_maya", MagicMock(return_value=True))
    def test_non_restorable_window_is_dockable_without_workspace_retention(self):
        """Ensures dynamic windows do not save a startup restore script."""
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

        class NonRestorableWindow(metaclass=MayaWindowMeta):
            """Test window that cannot be recreated from a no-argument call."""

            allow_workspace_restore = False

            def __init__(self):
                """Initializes the test window."""
                super().__init__()
                self.setObjectName("NonRestorableWindow")

        with patch.object(MayaQWidgetDockableMixin, "show") as mock_show:
            with patch.object(MayaWindowMeta, "_discard_workspace_control") as mock_discard:
                window = NonRestorableWindow()
                window.show()

        expected_retain = False
        expected_restore_script = False
        result_retain = mock_show.call_args.kwargs.get("retain")
        result_restore_script = "uiScript" in mock_show.call_args.kwargs
        self.assertEqual(expected_retain, result_retain)
        self.assertEqual(expected_restore_script, result_restore_script)
        mock_discard.assert_called_once_with("NonRestorableWindowWorkspaceControl")

    def test_restore_window_discards_non_restorable_workspace_control(self):
        """Ensures a retained dynamic window is not constructed without its inputs."""
        maya_cmds = types.ModuleType("maya.cmds")
        maya_open_maya_ui = types.ModuleType("maya.OpenMayaUI")
        maya_module = types.ModuleType("maya")
        maya_module.cmds = maya_cmds
        maya_module.OpenMayaUI = maya_open_maya_ui
        maya_cmds.workspaceControl = MagicMock(return_value=True)
        maya_cmds.deleteUI = MagicMock()
        window_class = MagicMock()
        window_class.allow_workspace_restore = False
        window_module = types.ModuleType("gt.ui.option_window")
        window_module.OptionWindow = window_class
        package_module = types.ModuleType("gt.ui")

        def import_module(module_name):
            """Returns the test modules used by the workspace restore call."""
            if module_name == "gt.ui.option_window":
                return window_module
            if module_name == "gt.ui":
                return package_module
            raise ImportError(module_name)

        with patch.dict(
            sys.modules,
            {
                "maya": maya_module,
                "maya.cmds": maya_cmds,
                "maya.OpenMayaUI": maya_open_maya_ui,
            },
        ):
            with patch("importlib.import_module", side_effect=import_module):
                MayaWindowMeta.restore_window(
                    "gt.ui.option_window",
                    "OptionWindow",
                    "gtReloadFileOptionsWorkspaceControl",
                )

        window_class.assert_not_called()
        maya_cmds.deleteUI.assert_called_once_with(
            "gtReloadFileOptionsWorkspaceControl",
            control=True,
        )

    def test_restore_window_uses_workspace_restore_factory(self):
        """Ensures a dynamic window is rebuilt through its registered factory."""
        maya_open_maya_ui = types.ModuleType("maya.OpenMayaUI")
        maya_module = types.ModuleType("maya")
        maya_module.OpenMayaUI = maya_open_maya_ui
        maya_open_maya_ui.MQtUtil = MagicMock()
        maya_open_maya_ui.MQtUtil.findControl.return_value = 123
        window_class = MagicMock()
        window_class.allow_workspace_restore = False
        window_module = types.ModuleType("gt.ui.option_window")
        window_module.OptionWindow = window_class
        restore_key = MayaWindowMeta._get_restore_key(
            "gt.ui.option_window",
            "OptionWindow",
            "gtReloadFileOptionsWorkspaceControl",
        )

        def rebuild_window():
            """Simulates a factory attaching its newly created option window."""
            MayaWindowMeta._pending_restores.pop(restore_key, None)

        restore_factory = MagicMock(side_effect=rebuild_window)
        restore_module = types.ModuleType("gt.tools.utility_options.reload_file_options")
        restore_module.open_reload_file_options = restore_factory

        def import_module(module_name):
            """Returns the test modules used by the workspace restore call."""
            if module_name == "gt.ui.option_window":
                return window_module
            if module_name == "gt.tools.utility_options.reload_file_options":
                return restore_module
            raise ImportError(module_name)

        MayaWindowMeta._pending_restores.clear()
        with patch.dict(
            sys.modules,
            {
                "maya": maya_module,
                "maya.OpenMayaUI": maya_open_maya_ui,
            },
        ):
            with patch("importlib.import_module", side_effect=import_module):
                MayaWindowMeta.restore_window(
                    "gt.ui.option_window",
                    "OptionWindow",
                    "gtReloadFileOptionsWorkspaceControl",
                    "gt.tools.utility_options.reload_file_options.open_reload_file_options",
                )

        restore_factory.assert_called_once()
        window_class.assert_not_called()
        self.assertEqual({}, MayaWindowMeta._pending_restores)

    def test_restore_key_includes_workspace_control_name(self):
        """Ensures shared window classes can restore multiple workspace controls."""
        first_key = MayaWindowMeta._get_restore_key(
            "gt.ui.option_window",
            "OptionWindow",
            "gtReloadFileOptionsWorkspaceControl",
        )
        second_key = MayaWindowMeta._get_restore_key(
            "gt.ui.option_window",
            "OptionWindow",
            "gtDeleteKeyframesOptionsWorkspaceControl",
        )

        self.assertNotEqual(first_key, second_key)

    def test_restore_script_includes_workspace_restore_factory(self):
        """Ensures the persisted Maya script retains the factory import path."""
        factory_path = "gt.tools.utility_options.reload_file_options.open_reload_file_options"
        result = MayaWindowMeta._get_restore_script(
            "gt.ui.option_window",
            "OptionWindow",
            "gtReloadFileOptionsWorkspaceControl",
            factory_path,
        )

        self.assertIn(factory_path, result)

    def test_option_window_does_not_support_workspace_restore(self):
        """Ensures dynamic option windows opt out of startup workspace recovery."""
        expected = False
        result = OptionWindow.allow_workspace_restore
        self.assertEqual(expected, result)

    def test_option_window_enables_workspace_restore_for_factory(self):
        """Ensures an option window enables restore when a factory is provided."""
        factory_path = "gt.tools.utility_options.reload_file_options.open_reload_file_options"
        window = OptionWindow(
            "Reload File",
            "gtReloadFileOptions",
            workspace_restore_factory=factory_path,
        )

        self.assertTrue(window.allow_workspace_restore)
        self.assertEqual(factory_path, window.workspace_restore_factory)
        window.deleteLater()

    @patch.object(ui_qt.QtGui.QCursor, "pos", return_value=ui_qt.QtCore.QPoint(100, 200))
    def test_get_cursor_position_no_offset(self, mock_cursor):
        expected = ui_qt.QtCore.QPoint(100, 200)
        result = qt_utils.get_cursor_position()
        self.assertEqual(expected, result)

    @patch.object(ui_qt.QtGui.QCursor, "pos", return_value=ui_qt.QtCore.QPoint(100, 200))
    def test_get_cursor_position_with_offset(self, mock_cursor):
        offset_x = 10
        offset_y = 20
        expected = ui_qt.QtCore.QPoint(110, 220)
        result = qt_utils.get_cursor_position(offset_x, offset_y)
        self.assertEqual(expected, result)

    @patch("gt.ui.qt_utils.get_main_window_screen_number", return_value=0)
    @patch.object(ui_qt.QtWidgets.QApplication, "screens")
    def test_get_screen_center(self, mock_screens, mock_get_main_window_screen_number):
        expected = ui_qt.QtCore.QPoint(100, 200)
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

    @patch("gt.ui.qt_import.QtGui.QFont", return_value="mocked_font")
    @patch("gt.ui.qt_import.QtWidgets.QApplication.instance", return_value=MagicMock())
    @patch("gt.ui.qt_import.QtGui.QFontDatabase.addApplicationFontFromData", return_value=0)
    @patch("gt.ui.qt_import.QtGui.QFontDatabase.applicationFontFamilies", return_value=["CustomFont"])
    def test_load_custom_font_success(self, mock_font_from_data, mock_app_font_families, mock_app, mock_font):
        custom_font = qt_utils.load_custom_font("custom_font.ttf", point_size=12, weight=ui_qt.QtLib.Font.Bold, italic=True)
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

    @patch("gt.ui.qt_utils.is_font_available", return_value=True)
    @patch("gt.ui.qt_import.QtWidgets.QApplication.instance")
    def test_get_font_with_font_name(self, mock_instance, mock_is_font_available):
        mock_instance.return_value = MagicMock()

        font_name = "Arial"
        font = qt_utils.get_font(font_name)

        expected_font = ui_qt.QtGui.QFont(font_name)

        self.assertEqual(font, expected_font)

    @patch("gt.ui.qt_utils.is_font_available", return_value=False)
    @patch("gt.ui.qt_utils.load_custom_font", return_value=ui_qt.QtGui.QFont("CustomFont"))
    @patch("gt.ui.qt_import.QtWidgets.QApplication.instance")
    def test_get_font_with_font_path(self, mock_instance, mock_load_custom_font, mock_is_font_available):
        mock_instance.return_value = MagicMock()
        from gt.ui import resource_library

        result = qt_utils.get_font(resource_library.Font.roboto)
        expected_font = ui_qt.QtGui.QFont("CustomFont")
        self.assertEqual(expected_font, result)

    @patch("gt.ui.qt_import.QtWidgets.QApplication.instance")
    def test_get_font_invalid_font(self, mock_instance):
        mock_instance.return_value = MagicMock()

        invalid_font = 123  # Invalid input type
        font = qt_utils.get_font(invalid_font)

        expected_font = ui_qt.QtGui.QFont()  # Default font

        self.assertEqual(font, expected_font)

    def test_get_qt_color_valid_hex_color(self):
        # Test with a valid hex color
        expected = ui_qt.QtGui.QColor("#FF0000")
        result = qt_utils.get_qt_color("#FF0000")
        self.assertEqual(expected, result)

    def test_get_qt_color_valid_color_name(self):
        # Test with a valid color name
        expected = ui_qt.QtGui.QColor("red")
        result = qt_utils.get_qt_color("red")
        self.assertEqual(expected, result)

    def test_get_qt_color_invalid_color_input(self):
        # Test with an invalid color input
        expected = None
        result = qt_utils.get_qt_color("invalid_color")
        self.assertEqual(expected, result)

    def test_get_qt_color_color_object_input(self):
        # Test with a QColor object as input
        input_color = ui_qt.QtGui.QColor("#00FF00")
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

        expected = ui_qt.QtGui.QColor(255, 0, 0)
        result = qt_utils.get_qt_color(resource_library.Color.RGB.red)
        self.assertEqual(expected, result)

    def test_resize_to_screen_valid_percentage(self):
        mock_geometry = MagicMock()
        mock_geometry.width.return_value = 100
        mock_geometry.height.return_value = 200
        mock_screen = MagicMock()
        mock_screen.availableGeometry.return_value = mock_geometry
        window = MagicMock()

        if ui_qt.IS_PYSIDE6:
            with patch(
                "gt.ui.qt_import.QtGui.QGuiApplication.primaryScreen",
                return_value=mock_screen,
            ):
                qt_utils.resize_to_screen(window, percentage=50)
        else:
            with patch("gt.ui.qt_import.QtWidgets.QDesktopWidget") as mock_desktop_widget:
                mock_desktop_widget.return_value = mock_screen
                qt_utils.resize_to_screen(window, percentage=50)

        expected_width = 50
        expected_height = 100
        self.assertEqual(window.setGeometry.call_args[0][2], expected_width)
        self.assertEqual(window.setGeometry.call_args[0][3], expected_height)

    def test_resize_to_screen_invalid_percentage(self):
        window = Mock()
        with self.assertRaises(ValueError):
            qt_utils.resize_to_screen(window, percentage=110)

    def test_get_main_window_screen_number(self):
        mock_app = MagicMock()
        mock_main_window = MagicMock()
        mock_app.activeWindow.return_value = mock_main_window

        if ui_qt.IS_PYSIDE6:
            mock_screen = MagicMock()
            mock_main_window.geometry.return_value.center.return_value = ui_qt.QtCore.QPoint(0, 0)
            with patch("gt.ui.qt_import.QtWidgets.QApplication") as mock_qapplication:
                with patch("gt.ui.qt_import.QtGui.QGuiApplication") as mock_qgui_application:
                    mock_qapplication.instance.return_value = mock_app
                    mock_qgui_application.screenAt.return_value = mock_screen
                    mock_qgui_application.screens.return_value = [mock_screen]
                    result = qt_utils.get_main_window_screen_number()
            expected = 0
        else:
            mock_screen_number = MagicMock()
            mock_screen_number.screenNumber.return_value = 10
            with patch("gt.ui.qt_import.QtWidgets.QApplication") as mock_qapplication:
                mock_qapplication.instance.return_value = mock_app
                mock_qapplication.desktop.return_value = mock_screen_number
                result = qt_utils.get_main_window_screen_number()
            expected = 10

        self.assertEqual(expected, result)

    def test_get_window_screen_number(self):
        window = MagicMock()

        if ui_qt.IS_PYSIDE6:
            mock_screen = MagicMock()
            mock_screen.geometry.return_value.contains.return_value = True
            mock_app = MagicMock()
            mock_app.screens.return_value = [mock_screen]
            with patch("gt.ui.qt_import.QtGui.QGuiApplication") as mock_qgui_application:
                mock_qgui_application.instance.return_value = mock_app
                result = qt_utils.get_window_screen_number(window)
            expected = 0
        else:
            mock_screen_number = MagicMock()
            mock_screen_number.screenNumber.return_value = 10
            with patch("gt.ui.qt_import.QtWidgets.QDesktopWidget") as mock_desktop_widget:
                mock_desktop_widget.return_value = mock_screen_number
                result = qt_utils.get_window_screen_number(window)
            expected = 10

        self.assertEqual(expected, result)

    def test_center_window(self):
        mock_window = MagicMock()
        qt_utils.center_window(mock_window)
        mock_window.move.assert_called()

    def test_update_formatted_label_default_format(self):
        mock_label = ui_qt.QtWidgets.QLabel()
        expected_html = "<html><div style='text-align:center;'><font>Text</font></div></html>"
        qt_utils.update_formatted_label(mock_label, "Text")
        result_html = mock_label.text()
        self.assertEqual(expected_html, result_html)

    def test_update_formatted_label_custom_format(self):
        mock_label = ui_qt.QtWidgets.QLabel()
        expected_html = (
            "<html><div style='text-align:left;'><b><font size='16' color='blue' style='background-color:"
            "yellow;'>Text</font></b><b><font size='14' color='red'>Output</font></b></div></html>"
        )
        qt_utils.update_formatted_label(
            mock_label,
            "Text",
            text_size=16,
            text_color="blue",
            text_bg_color="yellow",
            text_is_bold=True,
            output_text="Output",
            output_size=14,
            output_color="red",
            text_output_is_bold=True,
            overall_alignment="left",
        )
        result_html = mock_label.text()
        self.assertEqual(expected_html, result_html)

    def test_load_and_scale_pixmap_scale_by_percentage(self):
        # Test scaling by percentage
        from gt.ui import resource_library

        input_path = resource_library.Icon.dev_code

        scale_percentage = 50
        scaled_pixmap = qt_utils.load_and_scale_pixmap(image_path=input_path, scale_percentage=scale_percentage)

        expected_width = 256  # 50% of the original width
        expected_height = 256  # 50% of the original height

        self.assertEqual(scaled_pixmap.width(), expected_width)
        self.assertEqual(scaled_pixmap.height(), expected_height)

    def test_load_and_scale_pixmap_scale_by_exact_height(self):
        # Test scaling by exact height
        from gt.ui import resource_library

        input_path = resource_library.Icon.dev_code
        exact_height = 200
        scaled_pixmap = qt_utils.load_and_scale_pixmap(
            image_path=input_path, scale_percentage=100, exact_height=exact_height
        )

        expected_height = 200  # Exact height specified

        self.assertEqual(scaled_pixmap.height(), expected_height)

    def test_load_and_scale_pixmap_scale_by_exact_width(self):
        # Test scaling by exact width
        from gt.ui import resource_library

        input_path = resource_library.Icon.dev_code
        exact_width = 300
        scaled_pixmap = qt_utils.load_and_scale_pixmap(
            image_path=input_path, scale_percentage=100, exact_width=exact_width
        )

        expected_width = 300  # Exact width specified

        self.assertEqual(scaled_pixmap.width(), expected_width)

    def test_load_and_scale_pixmap_scale_with_both_exact_dimensions(self):
        # Test scaling with both exact dimensions specified
        from gt.ui import resource_library

        input_path = resource_library.Icon.dev_code
        exact_width = 300
        exact_height = 200
        scaled_pixmap = qt_utils.load_and_scale_pixmap(
            image_path=input_path, scale_percentage=100, exact_height=exact_height, exact_width=exact_width
        )

        expected_width = 300  # Exact width specified
        expected_height = 200  # Exact height specified

        self.assertEqual(scaled_pixmap.width(), expected_width)
        self.assertEqual(scaled_pixmap.height(), expected_height)

    def test_create_color_pixmap_valid_color(self):
        expected_width_height = 24
        result = qt_utils.create_color_pixmap(
            color=ui_qt.QtGui.QColor(255, 0, 0), width=expected_width_height, height=expected_width_height
        )
        self.assertEqual(ui_qt.QtGui.QPixmap, type(result))
        self.assertEqual(expected_width_height, result.height())
        self.assertEqual(expected_width_height, result.width())

    def test_create_color_pixmap_invalid_color(self):
        # Test with an invalid color (not a QColor)
        result = qt_utils.create_color_pixmap("invalid_color")
        self.assertIsNone(result)

    def test_create_color_icon_valid_color(self):
        result = qt_utils.create_color_icon(color=ui_qt.QtGui.QColor(255, 0, 0))
        self.assertEqual(ui_qt.QtGui.QIcon, type(result))

    def test_create_color_icon_invalid_color(self):
        # Test with an invalid color (not a QColor)
        result = qt_utils.create_color_icon("invalid_color")
        self.assertIsNone(result)

    @patch("gt.ui.qt_import.QtWidgets.QApplication")
    def test_get_screen_dpi_scale_valid_screen_number(self, mock_qapp):
        # Create a mock QApplication instance with mock screens
        app = MagicMock()
        screen1 = MagicMock()
        screen2 = MagicMock()
        screen1.logicalDotsPerInch.return_value = 120.0
        screen2.logicalDotsPerInch.return_value = 96.0
        app.screens.return_value = [screen1, screen2]

        # Replace the QApplication instance with the mock
        mock_qapp.instance.return_value = app

        expected_result = 1
        result = qt_utils.get_screen_dpi_scale(screen_number=1)
        self.assertEqual(expected_result, result)
        expected_result = 1.25
        result = qt_utils.get_screen_dpi_scale(screen_number=0)
        self.assertEqual(expected_result, result)

    @patch("gt.ui.qt_import.QtWidgets.QApplication")
    def test_get_screen_dpi_scale_negative_screen_number(self, mock_app):
        # Create a mock QApplication instance with mock screens
        app = MagicMock()
        screen1 = MagicMock()
        screen2 = MagicMock()
        screen1.logicalDotsPerInch.return_value = 120.0
        screen2.logicalDotsPerInch.return_value = 96.0
        app.screens.return_value = [screen1, screen2]

        # Replace the QApplication instance with the mock
        mock_app.instance.return_value = app

        # Test with a negative screen number (screen_number = -1)
        with self.assertRaises(ValueError):
            qt_utils.get_screen_dpi_scale(-1)
