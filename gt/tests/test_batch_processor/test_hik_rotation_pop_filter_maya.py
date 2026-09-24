"""Maya integration tests for the HumanIK rotation pop post-script sample."""

import contextlib
import io
import unittest
from unittest import mock

from gt.tools.batch_processor.tasks.scripts.hik_retarget import smooth_rotation_pops as pop_filter
from gt.tools.batch_processor.tasks import task_utils


class TestRotationPopFilterMaya(unittest.TestCase):
    """Verifies native Butterworth behavior on disposable baked skeletons."""

    @classmethod
    def setUpClass(cls):
        """Initializes standalone only when no Maya session is already running."""
        try:
            import maya.cmds as cmds
            import maya.standalone
        except ImportError:
            raise unittest.SkipTest("Maya is unavailable; run with mayapy.")
        cls.initialized_standalone = False
        try:
            cmds.about(version=True)
        except (RuntimeError, AttributeError):
            maya.standalone.initialize(name="python")
            cls.initialized_standalone = True
        cls.cmds = cmds

    @classmethod
    def tearDownClass(cls):
        """Uninitializes Maya only when this test class initialized it."""
        if cls.initialized_standalone:
            import maya.standalone
            maya.standalone.uninitialize()

    def setUp(self):
        """Creates distinct source and target skeletons with a synthetic jump."""
        self.cmds.file(new=True, force=True)
        self.cmds.currentUnit(time="ntsc", angle="deg")
        self.joints = {}
        for namespace in ("source", "target"):
            self.cmds.namespace(add=namespace)
            self.cmds.select(clear=True)
            joint = self.cmds.joint(name=f"{namespace}:upperarm_r")
            self.joints[namespace] = joint
            for frame in range(1, 62):
                for channel in ("rotateX", "rotateY", "rotateZ"):
                    value = 80.0 if channel == "rotateX" and frame >= 31 else 0.0
                    self.cmds.setKeyframe(joint, attribute=channel, time=frame, value=value)
        self.target = self.joints["target"]
        self.cmds.playbackOptions(minTime=1, maxTime=10)
        self.cmds.currentTime(5)
        self.cmds.select(self.joints["source"])
        self.cmds.selectKey(self.target, attribute="rotateX", time=(2, 3))

    def values(self, joint):
        """Reads a joint's keyed X rotation.

        Args:
            joint (str): Joint to inspect.

        Returns:
            list: Key values in the current angular unit.
        """
        return self.cmds.keyframe(joint, attribute="rotateX", query=True, valueChange=True)

    def test_native_filter_changes_only_target_window_and_preserves_state(self):
        """Reduces the jump without following selected keys or playback limits."""
        before = self.values(self.target)
        source_before = self.values(self.joints["source"])
        selection = self.cmds.ls(selection=True)
        selected_keys = self.cmds.keyframe(query=True, selected=True, timeChange=True)
        with contextlib.redirect_stdout(io.StringIO()):
            reports = pop_filter.smooth_rotation_pops({"imported_target_nodes": [self.target]})
        after = self.values(self.target)
        self.assertEqual(3, len(reports))
        self.assertEqual([31.0], reports[0]["pops"])
        self.assertEqual([(21.0, 41.0)], reports[0]["windows"])
        self.assertEqual(len(before), len(after))
        self.assertEqual(before[:20], after[:20])
        self.assertEqual(before[41:], after[41:])
        self.assertLess(abs(after[30] - after[29]), 25.0)
        self.assertEqual(source_before, self.values(self.joints["source"]))
        self.assertEqual(selection, self.cmds.ls(selection=True))
        self.assertEqual(selected_keys, self.cmds.keyframe(query=True, selected=True, timeChange=True))
        self.assertEqual(5.0, self.cmds.currentTime(query=True))
        self.assertEqual(10.0, self.cmds.playbackOptions(query=True, maxTime=True))

    def test_dry_run_and_explicit_range(self):
        """Reports without edits and ignores pops outside an explicit interval."""
        before = self.values(self.target)
        with mock.patch.object(pop_filter, "DRY_RUN", True), contextlib.redirect_stdout(io.StringIO()):
            reports = pop_filter.smooth_rotation_pops({"imported_target_nodes": [self.target]})
        self.assertEqual(3, len(reports))
        self.assertEqual(before, self.values(self.target))
        with mock.patch.object(pop_filter, "END_FRAME", 20), contextlib.redirect_stdout(io.StringIO()):
            reports = pop_filter.smooth_rotation_pops({"imported_target_nodes": [self.target]})
        self.assertEqual([], reports)
        self.assertEqual(before, self.values(self.target))

    def test_radian_scene_and_shared_curve_protection(self):
        """Uses degree thresholds in radian scenes and skips shared outputs."""
        self.cmds.currentUnit(angle="rad")
        with mock.patch.object(pop_filter, "DRY_RUN", True), contextlib.redirect_stdout(io.StringIO()):
            reports = pop_filter.smooth_rotation_pops({"imported_target_nodes": [self.target]})
        self.assertEqual([31.0], reports[0]["pops"])
        curve = self.cmds.listConnections(f"{self.target}.rotateX", source=True, destination=False)[0]
        self.cmds.connectAttr(f"{curve}.output", f"{self.joints['source']}.rotateX", force=True)
        with contextlib.redirect_stdout(io.StringIO()):
            reports = pop_filter.smooth_rotation_pops({"imported_target_nodes": [self.target]})
        self.assertEqual([], reports)

    def test_executes_through_batch_inline_runner(self):
        """Runs the actual sample through the context used by HumanIK tasks."""
        script = task_utils.load_script_file(pop_filter.__file__)
        with contextlib.redirect_stdout(io.StringIO()):
            task_utils.run_inline_python_script(script, {"imported_target_nodes": [self.target]})
        after = self.values(self.target)
        self.assertLess(abs(after[30] - after[29]), 25.0)


if __name__ == "__main__":
    unittest.main()
