"""Unit tests for import-safe cleanup name filtering."""

import unittest

from gt.tools.utility_options.cleanup_options_model import get_names_to_delete


class TestCleanupOptionsModel(unittest.TestCase):
    """Tests literal filters and namespace hierarchy protection."""

    def test_match_modes(self):
        """Matches prefixes, substrings and suffixes independently."""
        names = ["keep_layer", "layer_keep", "other", "layer_keep_more"]
        expected_by_mode = {
            "Starts With": ["layer_keep", "other", "layer_keep_more"],
            "Contains": ["other"],
            "Ends With": ["keep_layer", "other", "layer_keep_more"],
        }
        for mode, expected in expected_by_mode.items():
            with self.subTest(mode=mode):
                self.assertEqual(expected, get_names_to_delete(names, "keep", mode))

    def test_empty_filter_keeps_all_candidates(self):
        """An empty filter retains every deletion candidate."""
        names = ["one", "two"]
        self.assertEqual(names, get_names_to_delete(names))

    def test_case_sensitive_literal_matching(self):
        """Treats case and wildcard characters literally."""
        names = ["Keep", "keep", "keep*", "keep_more"]
        self.assertEqual(["Keep", "keep", "keep_more"], get_names_to_delete(names, "keep*"))
        self.assertEqual(["Keep"], get_names_to_delete(names, "keep"))

    def test_namespace_hierarchy_protection(self):
        """Keeps matching descendants, ancestors and the matched namespace itself."""
        names = ["asset", "asset:keep", "asset:keep:rig", "asset:delete", "asset_other", "delete"]
        expected = ["asset:delete", "asset_other", "delete"]
        self.assertEqual(expected, get_names_to_delete(names, "keep", "Contains", namespaces=True))
        self.assertEqual(["delete"], get_names_to_delete(names, "asset", namespaces=True))
        self.assertEqual(
            ["asset_other", "delete"], get_names_to_delete(names, "asset:", namespaces=True),
        )

    def test_no_matches_and_all_matches(self):
        """Supports empty, fully ignored, and unmatched candidate lists."""
        self.assertEqual([], get_names_to_delete([], "keep"))
        self.assertEqual([], get_names_to_delete(["keep"], "keep"))
        self.assertEqual(["keep"], get_names_to_delete(["keep"], "missing"))

    def test_invalid_mode(self):
        """Rejects unsupported filters instead of deleting unexpected candidates."""
        with self.assertRaises(ValueError):
            get_names_to_delete(["keep"], "keep", "Invalid")
