"""Tests for the Auto Rigger custom control rig pose data model."""

import math
import unittest

from gt.tools.auto_rigger.control_rig_pose import ControlRigPoseData
from gt.tools.auto_rigger.control_rig_pose import ControlRigPoseMode
from gt.tools.auto_rigger.control_rig_pose import build_data_signature
from gt.tools.auto_rigger.control_rig_pose import is_matrix_valid


class TestControlRigPose(unittest.TestCase):
    """Tests mode constants, serialization, signatures, and validation."""

    def setUp(self):
        """Creates reusable valid matrix data."""
        self.identity_matrix = [
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]

    def test_control_rig_pose_modes(self):
        """Returns the three supported modes in UI order."""
        expected = ["automatic", "custom", "disabled"]
        result = ControlRigPoseMode.get_modes()
        self.assertEqual(expected, result)

    def test_build_data_signature_is_order_independent_for_dictionary_keys(self):
        """Builds matching signatures for equivalent dictionaries."""
        expected = build_data_signature({"a": 1, "b": {"c": 2}})
        result = build_data_signature({"b": {"c": 2}, "a": 1})
        self.assertEqual(expected, result)

    def test_is_matrix_valid_rejects_non_finite_values(self):
        """Rejects matrices containing values Maya cannot safely apply."""
        invalid_matrix = list(self.identity_matrix)
        invalid_matrix[0] = math.inf
        self.assertFalse(is_matrix_valid(invalid_matrix))

    def test_control_rig_pose_round_trip(self):
        """Preserves versioned pose data through dictionary serialization."""
        expected = ControlRigPoseData(
            project_uuid="project_uuid",
            proxy_signature="proxy_signature",
            transforms={"proxy_uuid": {"matrix": self.identity_matrix}},
        )
        result = ControlRigPoseData().read_data_from_dict(expected.get_data_as_dict())
        self.assertEqual(expected.get_data_as_dict(), result.get_data_as_dict())

    def test_validate_detects_stale_proxy_signature(self):
        """Reports a custom pose as stale when proxy configuration changes."""
        pose_data = ControlRigPoseData(
            project_uuid="project_uuid",
            proxy_signature="old_signature",
            transforms={"proxy_uuid": {"matrix": self.identity_matrix}},
        )
        result = pose_data.validate(
            project_uuid="project_uuid",
            proxy_signature="new_signature",
            expected_proxy_uuids=["proxy_uuid"],
        )
        self.assertFalse(result.get("valid"))
        self.assertIn("proxy configuration changed", " ".join(result.get("errors")))

    def test_validate_detects_missing_proxy_transform(self):
        """Reports active proxies that do not have a captured transform."""
        pose_data = ControlRigPoseData(
            project_uuid="project_uuid",
            proxy_signature="proxy_signature",
            transforms={"proxy_uuid": {"matrix": self.identity_matrix}},
        )
        result = pose_data.validate(expected_proxy_uuids=["proxy_uuid", "missing_uuid"])
        self.assertFalse(result.get("valid"))
        self.assertIn("missing 1 proxy transform", " ".join(result.get("errors")))


if __name__ == "__main__":
    unittest.main()
