"""Tests for Auto Rigger controller project lifecycle behavior."""

import unittest
from unittest.mock import MagicMock, patch

from gt.tools.auto_rigger.rigger_controller import RiggerController


class TestRiggerController(unittest.TestCase):
    """Tests controller actions without constructing the full Qt interface."""

    def test_initialize_new_project_clears_attribute_editor(self):
        """Clears stale project controls after replacing the current project."""
        controller = object.__new__(RiggerController)
        controller.model = MagicMock()
        controller.view = MagicMock()
        controller.show_unsaved_changes_warning_dialog = MagicMock(return_value=False)
        controller.refresh_widgets = MagicMock()
        controller.clear_opened_project = MagicMock()
        controller._has_high_level_changes = True

        controller.initialize_new_project()

        controller.model.clear_project.assert_called_once_with()
        controller.view.clear_module_widget.assert_called_once_with()
        controller.refresh_widgets.assert_called_once_with()
        controller.clear_opened_project.assert_called_once_with()
        self.assertFalse(controller._has_high_level_changes)

    @patch("gt.tools.auto_rigger.rigger_controller.core_session.is_script_in_interactive_maya")
    def test_show_log_view_for_build_docks_below_rigger_in_maya(self, mock_is_interactive):
        """Uses the Auto Rigger workspace control as the Maya docking target."""
        controller = object.__new__(RiggerController)
        controller._on_build_auto_dock_log = True
        controller.view = MagicMock()
        controller.view.objectName.return_value = "AutoRiggerView"
        controller.log_view = MagicMock()
        mock_is_interactive.return_value = True

        controller.show_log_view_for_build()

        controller.log_view.show_if_not_visible.assert_called_once_with(
            dock_to_control="AutoRiggerViewWorkspaceControl"
        )

    @patch("gt.tools.auto_rigger.rigger_controller.core_session.is_script_in_interactive_maya")
    def test_show_log_view_for_build_skips_docking_outside_maya(self, mock_is_interactive):
        """Preserves normal log-window behavior outside interactive Maya."""
        controller = object.__new__(RiggerController)
        controller._on_build_auto_dock_log = True
        controller.view = MagicMock()
        controller.log_view = MagicMock()
        mock_is_interactive.return_value = False

        controller.show_log_view_for_build()

        controller.log_view.show_if_not_visible.assert_called_once_with(dock_to_control=None)

    @patch("gt.tools.auto_rigger.rigger_controller.core_io.read_data")
    def test_import_project_from_file_uses_randomize_uuids_preference(self, mock_read_data):
        """Appends project modules using the UUID randomization automation state."""
        controller = object.__new__(RiggerController)
        controller.model = MagicMock()
        controller.refresh_widgets = MagicMock()
        controller._on_import_randomize_uuids = False
        mock_read_data.return_value = '{"modules": [{"module": "ModuleGeneric"}]}'
        project = controller.model.get_project.return_value
        project.import_modules_from_project_dict.return_value = [MagicMock()]

        result = controller.import_project_from_file(file_path="project.rig")

        self.assertTrue(result)
        project.import_modules_from_project_dict.assert_called_once_with(
            project_dict={"modules": [{"module": "ModuleGeneric"}]}, reinitialize_uuids=False
        )
        controller.refresh_widgets.assert_called_once_with()

    @patch("gt.tools.auto_rigger.rigger_controller.core_io.read_data")
    def test_import_project_from_file_skips_refresh_when_nothing_imported(self, mock_read_data):
        """Keeps the current state when the imported project has no modules."""
        controller = object.__new__(RiggerController)
        controller.model = MagicMock()
        controller.refresh_widgets = MagicMock()
        controller._on_import_randomize_uuids = True
        mock_read_data.return_value = "{}"
        controller.model.get_project.return_value.import_modules_from_project_dict.return_value = []

        result = controller.import_project_from_file(file_path="project.rig")

        self.assertFalse(result)
        controller.refresh_widgets.assert_not_called()


if __name__ == "__main__":
    unittest.main()
