"""Tests for ngSkinTools2 utility wrappers."""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

repository_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if repository_root not in sys.path:
    sys.path.append(repository_root)

import gt.utils.ngskin as utils_ng


class TestNGSkinUtils(unittest.TestCase):
    """Tests import-safe ngSkinTools2 utility behavior."""

    def test_vertex_transfer_mode_values(self):
        """Tests the complete supported vertex transfer mode list."""
        expected = ["closestPoint", "uvSpace", "vertexId"]
        result = utils_ng.VertexTransferMode.get_values()
        self.assertEqual(expected, result)

    def test_resolve_name_mapping_full_path(self):
        """Tests explicit full DAG path mapping."""
        expected = "|rig|C_hip_jnt"
        result = utils_ng.resolve_name_mapping(
            "|old_rig|hip_jnt", {"|old_rig|hip_jnt": "|rig|C_hip_jnt"}
        )
        self.assertEqual(expected, result)

    def test_resolve_name_mapping_short_name_without_namespace(self):
        """Tests short-name fallback mapping with a source namespace."""
        expected = "C_hip_jnt"
        result = utils_ng.resolve_name_mapping("|source:rig|source:hip_jnt", {"hip_jnt": "C_hip_jnt"})
        self.assertEqual(expected, result)

    def test_get_influences_from_file(self):
        """Tests influence metadata extraction from current ngSkinTools2 JSON."""
        file_descriptor, file_path = tempfile.mkstemp(suffix=".json")
        os.close(file_descriptor)
        try:
            with open(file_path, "w", encoding="utf-8") as stream:
                json.dump({"influences": [{"path": "|root_jnt"}, {"path": "|tip_jnt"}]}, stream)
            expected = ["|root_jnt", "|tip_jnt"]
            result = utils_ng.get_influences_from_file(file_path)
            self.assertEqual(expected, result)
        finally:
            os.remove(file_path)

    def test_build_influence_mapping_config(self):
        """Tests conversion from utility settings into an API configuration."""

        class MockConfig:
            """Minimal stand-in for ngSkinTools2 InfluenceMappingConfig."""

            @classmethod
            def transfer_defaults(cls):
                """Creates default mock configuration.

                Returns:
                    MockConfig: New configuration.
                """
                return cls()

        mock_api = mock.Mock()
        mock_api.InfluenceMappingConfig = MockConfig
        settings = utils_ng.InfluenceMappingSettings(
            use_name_matching=False,
            use_label_matching=False,
            use_distance_matching=True,
            use_dg_link_matching=False,
            distance_threshold=2.5,
        )
        with mock.patch.object(utils_ng, "_get_ngskin_api", return_value=mock_api):
            result = utils_ng.build_influence_mapping_config(settings)
        self.assertFalse(result.use_name_matching)
        self.assertFalse(result.use_label_matching)
        self.assertTrue(result.use_distance_matching)
        self.assertFalse(result.use_dg_link_matching)
        self.assertEqual(2.5, result.distance_threshold)

    def test_validate_vertex_transfer_mode_rejects_invalid_value(self):
        """Tests rejection of unsupported transfer modes."""
        with self.assertRaises(ValueError):
            utils_ng._validate_vertex_transfer_mode("invalid")


if __name__ == "__main__":
    unittest.main()
