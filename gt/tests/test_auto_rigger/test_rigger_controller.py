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


if __name__ == "__main__":
    unittest.main()
