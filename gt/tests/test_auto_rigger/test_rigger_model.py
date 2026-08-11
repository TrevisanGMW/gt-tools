import os
import tempfile
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

    def test_project_file_directory_environment_variable(self):
        model = rigger_model.RiggerModel()
        project = model.get_project()

        def get_environment_variables():
            with patch(
                "gt.tools.auto_rigger.rig_framework.cmds.file",
                return_value="",
                create=True,
            ):
                return rigger_model.tools_rig_frm.get_environment_variables(
                    rig_project=project
                )

        environment_variables = get_environment_variables()

        self.assertEqual("{project-file-dir}", project.get_project_dir_path())
        self.assertEqual("", environment_variables.get("{project-file-dir}"))
        self.assertEqual("", environment_variables.get("{project-dir}"))

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = os.path.join(temp_dir, "test_project.rig")
            model.save_project_to_file(project_path)

            environment_variables = get_environment_variables()

            self.assertEqual(
                os.path.normpath(temp_dir),
                environment_variables.get("{project-file-dir}"),
            )
            self.assertEqual(
                os.path.normpath(temp_dir),
                environment_variables.get("{project-dir}"),
            )
            with patch(
                "gt.tools.auto_rigger.rig_framework.cmds.file",
                return_value="",
                create=True,
            ):
                self.assertEqual(
                    os.path.normpath(temp_dir),
                    project.get_project_dir_path(parse_vars=True),
                )

            fixed_project_dir = os.path.join(temp_dir, "fixed_project")
            project.set_project_dir_path(fixed_project_dir)
            environment_variables = get_environment_variables()

            self.assertEqual(
                os.path.normpath(fixed_project_dir),
                environment_variables.get("{project-dir}"),
            )
            self.assertEqual(
                os.path.normpath(temp_dir),
                environment_variables.get("{project-file-dir}"),
            )

            os.remove(project_path)

            environment_variables = get_environment_variables()

            self.assertEqual("", environment_variables.get("{project-file-dir}"))
            self.assertEqual(
                os.path.normpath(fixed_project_dir),
                environment_variables.get("{project-dir}"),
            )


if __name__ == "__main__":
    unittest.main()
