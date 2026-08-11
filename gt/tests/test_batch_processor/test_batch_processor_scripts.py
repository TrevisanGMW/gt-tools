"""Tests for Batch Processor task script samples."""

import unittest

from gt.tools.batch_processor.tasks import task_utils


class TestBatchProcessorScripts(unittest.TestCase):
    """Tests that task sample scripts are dynamically discoverable."""

    def test_task_sample_scripts_are_discoverable_and_readable(self):
        """Ensures each initial example is located in its task sample directory."""
        expected_samples = (
            ("external_blender", "import_file_export_fbx.py", "open_input_file(input_path)"),
            ("external_mobu", "strip_geometry_export_fbx.py", "BATCH_INPUT"),
            ("external_unreal", "import_fbx_export_fbx.py", "import unreal"),
            ("hik_retarget", "print_post_retarget_context.py", "import maya.cmds as cmds"),
            ("hik_retarget", "print_pre_bake_context.py", "import maya.cmds as cmds"),
            ("maya_import", "print_import_context.py", "import maya.cmds as cmds"),
            ("python_script", "print_batch_context.py", "environment_variables"),
        )

        for sample_directory, expected_relative_path, expected_content in expected_samples:
            script_samples = task_utils.get_script_samples(sample_directory)
            sample_by_path = {
                sample["relative_path"].replace("\\", "/"): sample["path"]
                for sample in script_samples
            }

            self.assertIn(expected_relative_path, sample_by_path)
            script_text = task_utils.load_script_file(sample_by_path[expected_relative_path])
            self.assertIn(expected_content, script_text)

    def test_task_sample_directories_do_not_escape_scripts_root(self):
        """Ensures task sample lookup stays inside the packaged scripts directory."""
        expected = ""
        result = task_utils.get_script_samples_directory("../outside")

        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
