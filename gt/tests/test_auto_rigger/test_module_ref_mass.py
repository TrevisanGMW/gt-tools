"""Tests for the Auto Rigger COM References side mirroring."""

import unittest
import sys
import os

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
import gt.tools.auto_rigger.modules.module_ref_mass as tools_mod_ref_mass
from gt.tests import maya_test_tools


class TestModuleRefMass(unittest.TestCase):
    """Tests the reference mirroring helpers of the COM References module."""

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_side_reference_attrs_lists_paired_attributes(self):
        """Lists only side attributes that have an opposite counterpart."""
        module = tools_mod_ref_mass.ModuleAnimMassReferences()

        result = module.get_side_reference_attrs("left")

        self.assertIn("left_arm_upper", result)
        self.assertIn("left_toe_pivot", result)
        self.assertEqual(len(module.get_side_reference_attrs("right")), len(result))
        self.assertTrue(all(attr.startswith("left_") for attr in result))

    def test_mirror_left_to_right(self):
        """Replaces the search text on the left names to set the right names."""
        module = tools_mod_ref_mass.ModuleAnimMassReferences()
        module.left_hand = "lf_hand_JNT"
        module.left_foot = "lf_foot_JNT"

        result = module.mirror_side_references(source_side="left", search="lf_", replace="rt_")

        self.assertEqual("rt_hand_JNT", module.right_hand)
        self.assertEqual("rt_foot_JNT", result.get("right_foot"))
        self.assertEqual("lf_hand_JNT", module.left_hand)

    def test_mirror_right_to_left(self):
        """Replaces the search text on the right names to set the left names."""
        module = tools_mod_ref_mass.ModuleAnimMassReferences()
        module.right_ball = "R_toe_JNT"

        module.mirror_side_references(source_side="right", search="R_", replace="L_")

        expected = "L_toe_JNT"
        self.assertEqual(expected, module.left_ball)

    def test_mirror_with_empty_search_is_skipped(self):
        """Keeps the references unchanged when the search text is empty."""
        module = tools_mod_ref_mass.ModuleAnimMassReferences()
        module.right_hand = "custom_JNT"

        result = module.mirror_side_references(source_side="left", search="", replace="R_")

        self.assertEqual({}, result)
        self.assertEqual("custom_JNT", module.right_hand)


if __name__ == "__main__":
    unittest.main()
