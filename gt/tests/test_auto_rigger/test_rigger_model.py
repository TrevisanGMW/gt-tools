import unittest
from unittest.mock import patch

from gt.tools.auto_rigger import rigger_model


class TestRiggerModel(unittest.TestCase):
    def test_load_project_failure_preserves_current_project(self):
        model = rigger_model.RiggerModel()
        original_project = model.get_project()

        with patch(
            "gt.tools.auto_rigger.rigger_model.core_io.read_json_dict",
            side_effect=ValueError("Invalid project data"),
        ):
            with self.assertRaises(ValueError):
                model.load_project_from_file("invalid.rig")

        self.assertIs(original_project, model.get_project())


if __name__ == "__main__":
    unittest.main()
