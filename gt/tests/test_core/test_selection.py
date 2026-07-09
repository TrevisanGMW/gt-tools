import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# This pattern ensures the script can find the local 'gt' package
package_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if package_root_dir not in sys.path:
    sys.path.append(package_root_dir)

from gt.core import selection as core_selection
from gt.tests import maya_test_tools

# Alias for convenience
cmds = maya_test_tools.cmds


class TestCoreSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initializes Maya Standalone once for the entire test class."""
        try:
            maya_test_tools.import_maya_standalone(initialize=True)
        except Exception as e:
            logger.error(f"Failed to initialize Maya Standalone: {e}")
            sys.exit(1)

    def setUp(self):
        """Resets the Maya scene before each individual test runs."""
        maya_test_tools.force_new_scene()

    # --------------------------------------------------------------------------
    # Tests for select_non_unique_objects
    # --------------------------------------------------------------------------

    def test_select_non_unique_objects_no_duplicates(self):
        """Tests that nothing is selected when all names are unique."""
        # 1. Assign expected value
        cmds.polyCube(name="cube")
        cmds.polySphere(name="sphere")
        cmds.polyCylinder(name="cylinder")
        expected = []

        # 2. Assign result value
        core_selection.select_non_unique_objects()
        result = cmds.ls(selection=True)

        # 3. Assert equality
        self.assertEqual(result, expected)

    def test_select_non_unique_objects_empty_scene(self):
        """Tests that the function runs without error in an empty scene."""
        # 1. Assign expected value
        expected = []

        # 2. Assign result value
        core_selection.select_non_unique_objects()
        result = cmds.ls(selection=True)

        # 3. Assert equality
        self.assertEqual(result, expected)

    # --------------------------------------------------------------------------
    # Tests for ensure_selection_count
    # --------------------------------------------------------------------------

    def test_ensure_selection_exact_match_success(self):
        """Tests successful validation with an exact count requirement."""
        # 1. Assign expected value
        created_objects = [cmds.polyCube()[0] for _ in range(3)]
        cmds.select(created_objects)
        expected = created_objects

        # 2. Assign result value
        result = core_selection.ensure_selection_count(selection_limit=3, require_exact_count=True)

        # 3. Assert equality
        self.assertEqual(result, expected)

    def test_ensure_selection_up_to_match_success(self):
        """Tests successful validation with an "up to" requirement."""
        # 1. Assign expected value
        created_objects = [cmds.polyCube()[0] for _ in range(2)]
        cmds.select(created_objects)
        expected = created_objects

        # 2. Assign result value
        result = core_selection.ensure_selection_count(selection_limit=3, require_exact_count=False)

        # 3. Assert equality
        self.assertEqual(result, expected)

    def test_ensure_selection_tuple(self):
        """Tests successful validation with a range."""
        created_objects = [cmds.polyCube()[0] for _ in range(2)]
        cmds.select(created_objects)
        expected = created_objects
        result = core_selection.ensure_selection_count(selection_limit=(1, 3), require_exact_count=False)
        self.assertEqual(result, expected)
        cmds.file(new=True, force=True)
        created_objects = [cmds.polyCube()[0] for _ in range(5)]
        cmds.select(created_objects)
        expected = []
        result = core_selection.ensure_selection_count(selection_limit=(1, 3), require_exact_count=False)
        self.assertEqual(result, expected)

    def test_ensure_selection_no_limit_success(self):
        """Tests successful validation when the selection limit is None."""
        # 1. Assign expected value
        created_objects = [cmds.polyCube()[0] for _ in range(10)]
        cmds.select(created_objects)
        expected = created_objects

        # 2. Assign result value
        result = core_selection.ensure_selection_count(selection_limit=None)

        # 3. Assert equality
        self.assertEqual(result, expected)

    def test_ensure_selection_no_selection_fail(self):
        """Tests failure when nothing is selected."""
        # 1. Assign expected value
        expected = []

        # 2. Assign result value
        result = core_selection.ensure_selection_count()

        # 3. Assert equality
        self.assertEqual(result, expected)

    def test_ensure_selection_exact_match_fail_too_many(self):
        """Tests failure with an exact count requirement and too many items."""
        # 1. Assign expected value
        [cmds.polyCube() for _ in range(3)]
        expected = []

        # 2. Assign result value
        result = core_selection.ensure_selection_count(selection_limit=2, require_exact_count=True)

        # 3. Assert equality
        self.assertEqual(result, expected)

    def test_ensure_selection_invalid_argument_fail(self):
        """Tests failure when a non-integer is passed as the limit."""
        # 1. Assign expected value
        cmds.polyCube()
        expected = []

        # 2. Assign result value
        result = core_selection.ensure_selection_count(selection_limit="abc")

        # 3. Assert equality
        self.assertEqual(result, expected)
