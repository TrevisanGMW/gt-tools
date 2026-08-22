"""Tests for the Auto Rigger logging view."""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from gt.tools.auto_rigger.rigger_log_view import RiggerLoggingView


class TestRiggerLoggingView(unittest.TestCase):
    """Tests Maya docking behavior without constructing a Qt window."""

    def test_dock_below_control_uses_maya_workspace_controls(self):
        """Docks the log workspace control beneath the requested target."""
        maya_cmds = types.ModuleType("maya.cmds")
        maya_module = types.ModuleType("maya")
        maya_module.cmds = maya_cmds

        workspace_control = MagicMock(return_value=True)
        maya_cmds.workspaceControl = workspace_control
        log_view = MagicMock()
        log_view.objectName.return_value = "AutoRiggerLoggingView"

        with patch.dict(sys.modules, {"maya": maya_module, "maya.cmds": maya_cmds}):
            result = RiggerLoggingView.dock_below_control(
                log_view,
                "AutoRiggerViewWorkspaceControl",
                dock_height=90,
            )

        self.assertTrue(result)
        workspace_control.assert_any_call(
            "AutoRiggerLoggingViewWorkspaceControl",
            edit=True,
            dockToControl=("AutoRiggerViewWorkspaceControl", "bottom"),
        )
        workspace_control.assert_any_call(
            "AutoRiggerLoggingViewWorkspaceControl",
            edit=True,
            resizeHeight=90,
        )

    def test_get_dock_height_uses_fifteen_percent_of_the_rigger_height(self):
        """Calculates a compact log-pane height from the Auto Rigger height."""
        maya_cmds = types.ModuleType("maya.cmds")
        maya_module = types.ModuleType("maya")
        maya_module.cmds = maya_cmds

        def workspace_control_side_effect(control_name, **kwargs):
            """Returns values used by the target workspace-control queries."""
            if kwargs.get("query") and kwargs.get("exists"):
                return True
            if kwargs.get("query") and kwargs.get("height"):
                return 600

        maya_cmds.workspaceControl = MagicMock(side_effect=workspace_control_side_effect)
        log_view = MagicMock()
        log_view.DOCK_HEIGHT_PERCENTAGE = RiggerLoggingView.DOCK_HEIGHT_PERCENTAGE
        log_view.DOCK_MINIMUM_HEIGHT = RiggerLoggingView.DOCK_MINIMUM_HEIGHT

        with patch.dict(sys.modules, {"maya": maya_module, "maya.cmds": maya_cmds}):
            result = RiggerLoggingView.get_dock_height(log_view, "AutoRiggerViewWorkspaceControl")

        self.assertEqual(90, result)

    def test_show_if_not_visible_pre_sizes_before_docking(self):
        """Prevents the initial dock operation from expanding the log pane."""
        log_view = MagicMock()
        log_view._is_open = False
        log_view.width.return_value = 800
        log_view.get_dock_height.return_value = 90

        RiggerLoggingView.show_if_not_visible(log_view, "AutoRiggerViewWorkspaceControl")

        log_view.resize.assert_called_once_with(800, 90)
        log_view.show.assert_called_once_with()
        log_view.dock_below_control.assert_called_once_with(
            "AutoRiggerViewWorkspaceControl",
            dock_height=90,
        )

    def test_dock_below_control_rejects_empty_target(self):
        """Skips docking when no Auto Rigger workspace control is available."""
        log_view = MagicMock()

        result = RiggerLoggingView.dock_below_control(log_view, "")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
