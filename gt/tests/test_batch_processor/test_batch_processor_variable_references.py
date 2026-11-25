"""Regression tests for finding Batch Processor environment-variable references."""

import os
import sys
import unittest

test_package_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_package_dir)
package_root_dir = os.path.dirname(tests_dir)
for path_to_append in [package_root_dir, tests_dir]:
    if path_to_append not in sys.path:
        sys.path.append(path_to_append)

from gt.tools.batch_processor import batch_processor_environment_variables as variables_io
from gt.tools.batch_processor import batch_processor_model


class TestBatchProcessorVariableReferences(unittest.TestCase):
    """Tests reference scanning on serialized project data without Maya or Qt."""

    def setUp(self):
        """Creates a project with folders, custom variables, and tasks."""
        self.model = batch_processor_model.BatchProcessorModel()
        self.model.set_custom_environment_variables(
            {
                "fbx-dir": {"value": "{output-dir}/fbx", "query": False},
                "selection": {"value": "env['fbx-dir'] + cmds.ls()[0]", "query": True},
            }
        )
        self.task = self.model.tasks[0]
        self.task.settings["custom_path"] = "{FBX_DIR}/{previous-task-idx}.fbx"

    def get_project_references(self):
        """Gets references for the test project.

        Returns:
            dict: Token keys mapped to reference dictionaries.
        """
        return variables_io.find_project_references(self.model.to_dict())

    def test_task_settings_use_normalized_and_legacy_tokens(self):
        """Matches the model normalization and maps legacy aliases to current keys."""
        references = self.get_project_references()

        task_fields = [
            reference["field"]
            for reference in references["fbx-dir"]
            if reference["source_kind"] == "task"
        ]
        self.assertEqual(["parameters.custom_path"], task_fields)
        alias_sources = [reference["source_id"] for reference in references["previous-task-idx-padded"]]
        self.assertEqual([self.task.id], alias_sources)

    def test_query_code_access_counts_as_variable_dependency(self):
        """Treats env[...] inside a query as a use of that variable."""
        references = self.get_project_references()

        sources = [
            (reference["source_label"], reference["via"])
            for reference in references["fbx-dir"]
            if reference["source_kind"] == "variable"
        ]
        expected = [("{selection} (query)", [])]
        self.assertEqual(expected, sources)

    def test_project_dir_reaches_tasks_through_relative_output_folder(self):
        """Reports a task using a variable built from a relative output folder."""
        references = self.get_project_references()

        indirect_task_chains = [
            reference["via"]
            for reference in references["project-dir"]
            if reference["source_kind"] == "task"
        ]
        self.assertIn(["output-dir", "fbx-dir"], indirect_task_chains)

    def test_disabled_tasks_are_reported_as_disabled(self):
        """Keeps references from disabled tasks but marks them disabled."""
        self.task.enabled = False
        references = self.get_project_references()

        task_states = [
            reference["enabled"]
            for reference in references["fbx-dir"]
            if reference["source_kind"] == "task"
        ]
        self.assertEqual([False], task_states)


if __name__ == "__main__":
    unittest.main()
