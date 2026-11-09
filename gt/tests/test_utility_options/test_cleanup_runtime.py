"""Maya and Qt regression tests for cleanup option windows."""

import unittest
from unittest.mock import patch


class TestCleanupRuntime(unittest.TestCase):
    """Exercises destructive scope limits and real option-window actions in Maya."""

    @classmethod
    def setUpClass(cls):
        """Initializes Maya only when needed and uses one shared Qt application."""
        import maya.standalone
        from gt.ui import qt_import as ui_qt

        # Standalone creates a QCoreApplication if a QApplication does not exist.
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])
        cls.initialized_maya = False
        try:
            maya.standalone.initialize(name="python")
            cls.initialized_maya = True
        except RuntimeError:
            pass  # A test runner or interactive Maya has already initialized it.

    @classmethod
    def tearDownClass(cls):
        """Uninitializes Maya only when this test class initialized it."""
        if cls.initialized_maya:
            import maya.standalone

            maya.standalone.uninitialize()

    def setUp(self):
        """Starts each test with a clean scene and enabled undo."""
        import maya.cmds as cmds

        cmds.file(new=True, force=True)
        cmds.undoInfo(state=True)
        self.windows = []

    def tearDown(self):
        """Closes test windows without starting a blocking Qt event loop."""
        import maya.cmds as cmds

        cmds.namespace(set=":")
        for window in self.windows:
            window.close()
        self.application.processEvents()

    def _open_window(self, factory):
        """Creates a tracked window with Maya parenting disabled for headless Qt.

        Args:
            factory (callable): Window entry point to invoke.

        Returns:
            OptionWindow: Constructed window.
        """
        from gt.ui.option_window import OptionWindow

        with patch.object(OptionWindow, "_resolve_maya_parent", return_value=None):
            window = factory()
        self.windows.append(window)
        return window

    def _click(self, window, text):
        """Clicks the named action without entering a Qt event loop.

        Args:
            window (OptionWindow): Window containing the action.
            text (str): Button label.
        """
        from gt.ui import qt_import as ui_qt

        button = next(button for button in window.findChildren(ui_qt.QtWidgets.QPushButton) if button.text() == text)
        button.click()

    def test_empty_core_scopes(self):
        """Empty filtered lists never fall back to every item in the scene."""
        import maya.cmds as cmds
        from gt.core import display, namespace

        joint = cmds.joint()
        cmds.setAttr(f"{joint}.radius", 5)
        layer = cmds.createDisplayLayer(name="keep", empty=True)
        cmds.namespace(add="keep_namespace")
        cmds.jointDisplayScale(4)
        self.assertEqual(0, display.reset_joint_display([], verbose=False))
        self.assertEqual(0, display.delete_display_layers([], verbose=False))
        self.assertEqual(0, namespace.delete_namespaces(namespace_list=[], verbose=False))
        self.assertEqual(5, cmds.getAttr(f"{joint}.radius"))
        self.assertEqual(4, cmds.jointDisplayScale(query=True))
        self.assertTrue(cmds.objExists(layer))
        self.assertTrue(cmds.namespace(exists=":keep_namespace"))

    def test_joint_custom_values_and_undo(self):
        """A selected joint changes independently, including locked-attribute handling."""
        import maya.cmds as cmds
        from gt.core import display

        first = cmds.joint()
        second = cmds.joint()
        cmds.setAttr(f"{first}.radius", lock=True)
        cmds.jointDisplayScale(4)
        self.assertEqual(1, display.reset_joint_display(
            [first], verbose=False, radius=2.5, draw_style=3, global_scale=None, visibility=False,
        ))
        self.assertEqual(1, cmds.getAttr(f"{first}.radius"))
        self.assertEqual(3, cmds.getAttr(f"{first}.drawStyle"))
        self.assertEqual(False, cmds.getAttr(f"{first}.visibility"))
        self.assertEqual(0, cmds.getAttr(f"{second}.drawStyle"))
        self.assertEqual(4, cmds.jointDisplayScale(query=True))
        cmds.undo()
        self.assertEqual(0, cmds.getAttr(f"{first}.drawStyle"))
        self.assertEqual(True, cmds.getAttr(f"{first}.visibility"))
        self.assertEqual(1, display.reset_joint_display([second], verbose=False, radius=2.5, global_scale=2))
        self.assertEqual(2.5, cmds.getAttr(f"{second}.radius"))
        self.assertEqual(2, cmds.jointDisplayScale(query=True))

    def test_joint_default_values_entire_scene(self):
        """The default window action restores every joint to standard values."""
        import maya.cmds as cmds
        from gt.tools.utility_options import open_reset_joint_display_options

        joints = [cmds.joint(), cmds.joint()]
        for joint in joints:
            cmds.setAttr(f"{joint}.radius", 3)
            cmds.setAttr(f"{joint}.drawStyle", 2)
            cmds.setAttr(f"{joint}.visibility", False)
        cmds.jointDisplayScale(4)
        window = self._open_window(open_reset_joint_display_options)
        self._click(window, "Reset Joint Display")
        for joint in joints:
            self.assertEqual(1, cmds.getAttr(f"{joint}.radius"))
            self.assertEqual(0, cmds.getAttr(f"{joint}.drawStyle"))
            self.assertEqual(True, cmds.getAttr(f"{joint}.visibility"))
        self.assertEqual(1, cmds.jointDisplayScale(query=True))

    def test_namespace_default_scope_and_object_compatibility(self):
        """Default cleanup merges nested namespaces and preserves the object API."""
        import maya.cmds as cmds
        from gt.core import namespace

        for name in ("asset", "asset:rig", "other"):
            cmds.namespace(add=name)
        cmds.createNode("transform", name="asset:rig:protected")
        cmds.createNode("transform", name="other:retained")
        self.assertEqual(1, namespace.delete_namespaces(["other:retained"], verbose=False))
        self.assertTrue(cmds.objExists("retained"))
        self.assertTrue(cmds.objExists("asset:rig:protected"))
        self.assertEqual(2, namespace.delete_namespaces(verbose=False))
        self.assertTrue(cmds.objExists("protected"))
        self.assertTrue(cmds.namespace(exists=":UI"))
        self.assertTrue(cmds.namespace(exists=":shared"))
        cmds.undo()
        self.assertTrue(cmds.objExists("asset:rig:protected"))

    def test_namespace_filter_from_nonroot_namespace_and_undo(self):
        """Ignored nested paths survive merging and root-relative namespace queries."""
        import maya.cmds as cmds
        from gt.tools.utility_options import open_delete_namespaces_options

        for name in ("asset", "asset:keep", "asset:keep:rig", "asset:remove", "delete"):
            cmds.namespace(add=name)
        protected = cmds.createNode("transform", name="asset:keep:rig:protected")
        cmds.createNode("transform", name="asset:remove:merged")
        cmds.namespace(set=":asset:keep")
        window = self._open_window(open_delete_namespaces_options)
        window.controls["Ignore When"].setCurrentText("Contains")
        window.controls["Ignore Text"].setText("keep")
        self._click(window, "Delete Namespaces")
        self.assertTrue(cmds.objExists(f":{protected}"))
        self.assertTrue(cmds.namespace(exists=":asset:keep:rig"))
        self.assertFalse(cmds.namespace(exists=":asset:remove"))
        self.assertFalse(cmds.namespace(exists=":delete"))
        self.assertTrue(cmds.objExists(":merged"))
        self.assertEqual(":asset:keep", cmds.namespaceInfo(currentNamespace=True, absoluteName=True))
        cmds.undo()
        self.assertTrue(cmds.namespace(exists=":asset:remove"))
        self.assertTrue(cmds.namespace(exists=":delete"))

    def test_layers_preview_filter_and_undo(self):
        """Previews safely and applies filtering only when the action is clicked."""
        import maya.cmds as cmds
        from gt.tools.utility_options import open_delete_display_layers_options

        window = self._open_window(open_delete_display_layers_options)
        kept = cmds.createDisplayLayer(name="keep_layer", empty=True)
        removed = cmds.createDisplayLayer(name="delete_layer", empty=True)
        window.controls["Ignore Text"].setText("keep")
        self._click(window, "Preview")
        self.assertTrue(cmds.objExists(removed))
        self._click(window, "Delete Display Layers")
        self.assertFalse(cmds.objExists(removed))
        self.assertTrue(cmds.objExists(kept))
        self.assertTrue(cmds.objExists("defaultLayer"))
        cmds.undo()
        self.assertTrue(cmds.objExists(removed))
        window.controls["Ignore Text"].setText("_layer")
        window.controls["Ignore When"].setCurrentText("Ends With")
        self._click(window, "Delete Display Layers")
        self.assertTrue(cmds.objExists(removed))
        self.assertTrue(cmds.objExists(kept))
        window.controls["Ignore Text"].clear()
        self._click(window, "Delete Display Layers")
        self.assertFalse(cmds.objExists(removed))
        self.assertFalse(cmds.objExists(kept))
        self.assertTrue(cmds.objExists("defaultLayer"))

    def test_joint_window_selection_and_defaults(self):
        """Checks defaults, safe empty selection, custom targets and global opt-out."""
        import maya.cmds as cmds
        from gt.tools.utility_options import open_reset_joint_display_options

        first = cmds.joint()
        second = cmds.joint()
        window = self._open_window(open_reset_joint_display_options)
        self.assertEqual("Entire Scene", window.controls["Scope"].currentText())
        self.assertEqual(1, window.controls["Radius"].value())
        self.assertEqual("Bone", window.controls["Draw Style"].currentText())
        self.assertEqual(1, window.controls["Global Multiplier"].value())
        window.controls["Scope"].setCurrentText("Selection")
        cmds.select(clear=True)
        cmds.jointDisplayScale(3)
        self._click(window, "Reset Joint Display")
        self.assertEqual(3, cmds.jointDisplayScale(query=True))
        window.controls["Radius"].setValue(2.5)
        window.controls["Draw Style"].setCurrentText("None")
        window.controls["Set Global Scale"].setChecked(False)
        self.assertFalse(window.controls["Global Multiplier"].isEnabled())
        cmds.select(first)
        self._click(window, "Reset Joint Display")
        self.assertEqual(2.5, cmds.getAttr(f"{first}.radius"))
        self.assertEqual(2, cmds.getAttr(f"{first}.drawStyle"))
        self.assertEqual(1, cmds.getAttr(f"{second}.radius"))
        self.assertEqual(3, cmds.jointDisplayScale(query=True))
