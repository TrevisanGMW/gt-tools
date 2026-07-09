import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tests import maya_test_tools
from gt.core import undo as core_undo

cmds = maya_test_tools.cmds


class TestUndoCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_undo_chunk_context(self):
        with patch("maya.cmds.undoInfo") as mock_undoInfo, patch("maya.cmds.undo") as mock_undo:
            with core_undo.UndoChunk("Test Chunk"):
                mock_undoInfo.assert_called_with(openChunk=True, undoName="Test Chunk")

            mock_undoInfo.assert_any_call(closeChunk=True)

    def test_undo_suspended_context(self):
        with patch("maya.cmds.undoInfo") as mock_undoInfo:
            mock_undoInfo.return_value = True
            with core_undo.UndoSuspended():
                mock_undoInfo.assert_any_call(stateWithoutFlush=False)
            mock_undoInfo.assert_any_call(stateWithoutFlush=True)

    def test_suspend_undo_decorator(self):
        with patch("maya.cmds.undoInfo") as mock_undoInfo:

            @core_undo.suspend_undo
            def dummy_func(x, y):
                return x + y

            result = dummy_func(2, 3)
            self.assertEqual(result, 5)
            mock_undoInfo.assert_any_call(stateWithoutFlush=False)

    def test_undo_chunk_decorator(self):
        with patch("maya.cmds.undoInfo") as mock_undoInfo, patch("gt.core.undo.cmds.undo") as mock_undo:

            @core_undo.undo_chunk(chunk_name="Decorator Chunk")
            def dummy_func(x):
                return x * 2

            result = dummy_func(4)
            self.assertEqual(result, 8)
            mock_undoInfo.assert_any_call(openChunk=True, undoName="Decorator Chunk")
            mock_undoInfo.assert_any_call(closeChunk=True)
