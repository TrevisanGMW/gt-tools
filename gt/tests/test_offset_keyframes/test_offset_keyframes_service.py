"""Maya tests for the Offset Keyframes service."""

import os
import sys
import unittest


test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for directory_path in [package_root_dir, tests_dir]:
    if directory_path not in sys.path:
        sys.path.append(directory_path)

from gt.tests import maya_test_tools
from gt.core import anim as core_anim
from gt.tools.offset_keyframes.offset_keyframes_service import OffsetKeyframesService


cmds = maya_test_tools.cmds


class TestOffsetKeyframesService(unittest.TestCase):
    """Tests Maya actions exposed by OffsetKeyframesService."""

    @classmethod
    def setUpClass(cls):
        """Initializes Maya once for the test class."""
        maya_test_tools.import_maya_standalone(initialize=True)

    def setUp(self):
        """Creates a clean Maya scene for each test."""
        maya_test_tools.force_new_scene()

    def test_offset_with_euler_filter_undoes_in_one_step(self):
        """Tests Offset and Euler Filter are grouped in one undo action."""
        source = cmds.polyCube(name="offset_source", createUVs=4, ch=False)[0]
        cmds.setKeyframe(source, attribute="rotateX", time=1, value=2)
        cmds.setKeyframe(source, attribute="rotateX", time=5, value=200)
        curve = core_anim.get_time_keyframes([source])[0]
        cmds.selectKey(clear=True)
        cmds.selectKey(curve, add=True, time=(1, 1))
        cmds.flushUndo()

        service = OffsetKeyframesService()
        service.offset(nodes=[source], offset=2, scope="selected", apply_euler_filter=True)

        after_offset = cmds.keyframe(curve, query=True, timeChange=True)
        cmds.undo()
        after_undo = cmds.keyframe(curve, query=True, timeChange=True)

        self.assertEqual([3.0, 5.0], after_offset)
        self.assertEqual([1.0, 5.0], after_undo)

    def test_stagger_undoes_in_one_step(self):
        """Tests Stagger and its per-object offsets are one undo action."""
        first = cmds.polyCube(name="first", createUVs=4, ch=False)[0]
        second = cmds.polyCube(name="second", createUVs=4, ch=False)[0]
        for node in [first, second]:
            cmds.setKeyframe(node, attribute="translateX", time=1, value=1)
            cmds.setKeyframe(node, attribute="translateX", time=5, value=5)
        second_curve = core_anim.get_time_keyframes([second])[0]
        cmds.flushUndo()

        service = OffsetKeyframesService()
        service.stagger(nodes=[first, second], step=2, scope="all")

        after_stagger = cmds.keyframe(second_curve, query=True, timeChange=True)
        cmds.undo()
        after_undo = cmds.keyframe(second_curve, query=True, timeChange=True)

        self.assertEqual([3.0, 7.0], after_stagger)
        self.assertEqual([1.0, 5.0], after_undo)


if __name__ == "__main__":
    unittest.main()
