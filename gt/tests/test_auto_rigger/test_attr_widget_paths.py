"""Tests Auto Rigger path fields and path-information windows."""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import gt.ui.qt_import as ui_qt
from gt.tools.auto_rigger import rigger_path_utils
from gt.tools.auto_rigger.attr_widgets.attr_widget_base import AttrWidget
from gt.tools.auto_rigger.attr_widgets.attr_widget_project import AttrWidgetProject
from gt.tools.auto_rigger.rigger_geo_preprocessor import ProjectContextPathWidget
from gt.tools.auto_rigger.rig_framework import RigProject


class TestAttrWidgetPaths(unittest.TestCase):
    """Tests shared Auto Rigger path widget behavior."""

    @classmethod
    def setUpClass(cls):
        """Creates a Qt application when one does not already exist."""
        application = ui_qt.QtWidgets.QApplication.instance()
        if not application:
            cls.application = ui_qt.QtWidgets.QApplication(sys.argv)
        else:
            cls.application = application

    def tearDown(self):
        """Closes any widgets created by a test."""
        for widget in getattr(self, "widgets", []):
            widget.close()

    def test_open_env_var_feedback_dialog_uses_highlighted_output_window(self):
        """Displays resolved path details and discovered files in the rich output view."""
        self.widgets = []
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "source.ma")
            with open(file_path, "w", encoding="utf-8") as source_file:
                source_file.write("// Maya ASCII")
            module = MagicMock()
            module.parse_path.return_value = temp_dir
            widget = AttrWidget(module=module, project=RigProject())
            self.widgets.append(widget)
            field = ui_qt.QtWidgets.QLineEdit("{project-dir}")

            with patch(
                "gt.tools.auto_rigger.rigger_path_utils.ui_python_output_view.PythonOutputView"
            ) as output_view_class:
                output_view = output_view_class.return_value

                widget.open_env_var_feedback_dialog(field)

            output_view.setWindowTitle.assert_called_once_with("Path Information")
            output_view.show.assert_called_once_with()
            result = output_view.set_python_output_text.call_args.args[0]
            self.assertIn("Configured Path:\n{project-dir}", result)
            self.assertIn(f"Parsed Path:\n{os.path.normpath(temp_dir)}", result)
            self.assertIn("Exists: True", result)
            self.assertIn("Directory: True", result)
            self.assertIn("File: False", result)
            self.assertIn("Count: 1", result)
            self.assertIn(os.path.normpath(file_path), result)

    def test_geometry_preprocessor_uses_highlighted_path_information(self):
        """Routes geometry preprocessor path information through the shared rich view."""
        self.widgets = []
        widget = ProjectContextPathWidget(
            nice_name="Geometry Directory",
            default_text="{project-dir}/geometry",
            project=RigProject(),
        )
        self.widgets.append(widget)

        with patch.object(widget, "parse_path", return_value="C:/project/geometry"):
            with patch.object(rigger_path_utils, "show_path_information") as show_path_information:
                widget._open_env_var_feedback_dialog()

        show_path_information.assert_called_once_with(
            parent=widget,
            configured_path="{project-dir}/geometry",
            parsed_path="C:/project/geometry",
            title="Path Information",
        )

    def test_resolve_path_uses_project_file_directory(self):
        """Resolves project-level fields without requiring a module."""
        self.widgets = []
        with tempfile.TemporaryDirectory() as temp_dir:
            project_file_path = os.path.join(temp_dir, "test_project.rig")
            with open(project_file_path, "w", encoding="utf-8") as project_file:
                project_file.write("{}")
            project = RigProject()
            project.project_file_path = project_file_path
            widget = AttrWidget(project=project)
            self.widgets.append(widget)

            with patch(
                "gt.tools.auto_rigger.rig_framework.cmds.file",
                return_value="",
                create=True,
            ):
                result = widget.resolve_path("{project-file-dir}")

            expected = os.path.normpath(temp_dir)
            self.assertEqual(expected, result)

    def test_project_directory_has_path_information_button(self):
        """Adds a path-information action beside the project directory field."""
        self.widgets = []
        widget = AttrWidgetProject(project=RigProject())
        self.widgets.append(widget)

        result = [
            button
            for button in widget.findChildren(ui_qt.QtWidgets.QPushButton)
            if button.toolTip() == "Get more information about the current path."
        ]

        expected = 1
        self.assertEqual(expected, len(result))


if __name__ == "__main__":
    unittest.main()
