"""Tests for Auto Rigger controller project lifecycle behavior."""

import unittest
from unittest.mock import MagicMock

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


if __name__ == "__main__":
    unittest.main()
