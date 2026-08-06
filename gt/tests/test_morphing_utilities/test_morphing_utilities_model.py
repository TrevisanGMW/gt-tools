"""Unit tests for Morphing Utilities model behavior."""

import unittest

from gt.tools.morphing_utilities.morphing_utilities_model import MorphingUtilitiesModel


class TestMorphingUtilitiesModel(unittest.TestCase):
    """Tests pure target filtering and naming behavior."""

    def test_build_rename_pairs(self):
        model = MorphingUtilitiesModel()
        model.set_search_replace("Right", "Left")

        result = model.build_rename_pairs(["browRight", "jaw", "eyeRight"])

        expected = [("browRight", "browLeft"), ("eyeRight", "eyeLeft")]
        self.assertEqual(expected, result)

    def test_build_duplicate_pairs_uses_operation_suffix(self):
        model = MorphingUtilitiesModel()
        model.set_search_replace("", "")

        result = model.build_duplicate_pairs(["brow", "jaw"], "mirror")

        expected = [("brow", "brow_Mirrored"), ("jaw", "jaw_Mirrored")]
        self.assertEqual(expected, result)

    def test_build_duplicate_pairs_uses_replacement(self):
        model = MorphingUtilitiesModel()
        model.set_search_replace("Right", "Left")

        result = model.build_duplicate_pairs(["browRight", "jaw"], "flip")

        expected = [("browRight", "browLeft")]
        self.assertEqual(expected, result)

    def test_validate_rename_requires_search_text(self):
        model = MorphingUtilitiesModel()

        result = model.validate_operation("rename")

        expected = (False, "Enter Search text before renaming target names.")
        self.assertEqual(expected, result)

    def test_set_source_state_clears_selected_node(self):
        model = MorphingUtilitiesModel()
        model.set_source_state("mesh", ["blendShapeA"])
        model.set_blend_node("blendShapeA")

        model.set_source_state("otherMesh", ["blendShapeB"])

        self.assertEqual("", model.blend_node)
        self.assertEqual(["blendShapeB"], model.blend_nodes)


if __name__ == "__main__":
    unittest.main()
