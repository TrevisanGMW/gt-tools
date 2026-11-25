"""Tests for finding Auto Rigger environment-variable references."""

import os
import sys
import unittest

tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
import gt.tools.auto_rigger.rigger_environment_references as rig_env_refs


class TestRiggerEnvironmentReferences(unittest.TestCase):
    """Tests reference scanning on serialized rig project data without Maya."""

    def setUp(self):
        """Creates serialized project data with two modules."""
        self.project_data = {
            "uuid": "project-uuid",
            "name": "Biped",
            "preferences": {"project_dir": "{project-file-dir}/rig"},
            "modules": [
                {
                    "module": "ModuleGeneric",
                    "uuid": "module-a",
                    "active": False,
                    "name": "Generic",
                    "geometry_path": "{project-dir}/geo/{module-name}.fbx",
                },
                {
                    "module": "ModuleSpine",
                    "uuid": "module-b",
                    "active": True,
                    "name": "Spine",
                    "code": {"pre_build": "print('{Project-Dir}')"},
                },
            ],
        }

    def test_module_uses_are_direct_and_project_file_dir_is_indirect(self):
        """Follows the project directory setting to module paths."""
        references = rig_env_refs.find_project_references(
            self.project_data, module_labels={"module-a": "Generic (Arm)"}
        )

        project_dir_uses = [
            (reference["source_label"], reference["enabled"]) for reference in references["project-dir"]
        ]
        expected = [("Generic (Arm)", False)]
        self.assertEqual(expected, project_dir_uses)
        project_file_dir_uses = [
            (reference["source_kind"], reference["via"]) for reference in references["project-file-dir"]
        ]
        expected = [("variable", []), ("module", ["project-dir"])]
        self.assertEqual(expected, project_file_dir_uses)

    def test_tokens_are_case_sensitive(self):
        """Keeps exact keys because Auto Rigger replaces tokens case-sensitively."""
        references = rig_env_refs.find_project_references(self.project_data)

        self.assertIn("Project-Dir", references)
        self.assertNotIn("module-b", [ref["source_id"] for ref in references["project-dir"]])

    def test_missing_project_dir_uses_default(self):
        """Treats an unset project directory as the project file folder."""
        self.project_data["preferences"] = {}
        references = rig_env_refs.find_project_references(self.project_data)

        labels = [reference["source_label"] for reference in references["project-file-dir"]]
        self.assertIn("{project-dir} (default project directory)", labels)


if __name__ == "__main__":
    unittest.main()
