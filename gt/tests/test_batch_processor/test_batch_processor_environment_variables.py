"""Regression tests for custom-variable file and clipboard serialization."""

import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

from gt.tools.batch_processor import batch_processor_environment_variables as variables_io


class TestBatchProcessorEnvironmentVariables(unittest.TestCase):
    """Tests portable definitions without a Maya or Qt application."""

    def test_round_trip_preserves_order_values_and_query_flags(self):
        """Keeps expression dependencies ordered and values unmodified."""
        variables = {
            "z-source": {"value": "D:\\assets\\café\n{project-dir}", "query": False},
            "a-result": {"value": "env['z-source'] + '\\nfinish'", "query": True},
            "empty": {"value": "", "query": False},
        }
        with tempfile.TemporaryDirectory(prefix="gt_variables_test_") as directory:
            file_path = os.path.join(directory, "variables.json")
            variables_io.write_variables(file_path, variables)
            result = variables_io.read_variables(file_path)
        self.assertEqual(variables, result)
        self.assertEqual(list(variables), list(result))
        self.assertEqual(variables, variables_io.deserialize_variables(variables_io.serialize_variables(variables)))

    def test_invalid_payloads_are_rejected(self):
        """Rejects malformed data before any variables reach the editor."""
        invalid_variables = [
            [],
            {"bad name": {"value": "", "query": False}},
            {"{{nested}}": {"value": "", "query": False}},
            {"project-dir": {"value": "", "query": False}},
            {"valid": "not a definition"},
            {"valid": {"value": [], "query": False}},
            {"valid": {"value": "", "query": "false"}},
            {"valid": {"value": "", "query": 1}},
            {"valid": {"value": ""}},
            {
                "MY_PATH": {"value": "first", "query": False},
                "{my-path}": {"value": "second", "query": True},
            },
        ]
        for variables in invalid_variables:
            with self.subTest(variables=variables), self.assertRaises(ValueError):
                variables_io.deserialize_variables(
                    json.dumps({"version": 1, "custom_environment_variables": variables})
                )
        for payload in ("not JSON", "[]", "{}", '{"version": true, "custom_environment_variables": {}}'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                variables_io.deserialize_variables(payload)

    def test_import_normalizes_names_and_accepts_utf8_bom(self):
        """Accepts edited UTF-8 files and the same name aliases as the model."""
        variables = {"{MY_PATH}": {"value": "café", "query": False}}
        payload = {"version": 1, "custom_environment_variables": variables}
        with tempfile.TemporaryDirectory(prefix="gt_variables_test_") as directory:
            file_path = os.path.join(directory, "variables.json")
            with open(file_path, "w", encoding="utf-8-sig") as variables_file:
                json.dump(payload, variables_file, ensure_ascii=False)
            result = variables_io.read_variables(file_path)
        self.assertEqual({"my-path": {"value": "café", "query": False}}, result)

    def test_failed_export_preserves_existing_file(self):
        """Leaves the previous export intact when validation or replacement fails."""
        original = {"original": {"value": "keep", "query": False}}
        replacement = {"replacement": {"value": "new", "query": False}}
        with tempfile.TemporaryDirectory(prefix="gt_variables_test_") as directory:
            file_path = os.path.join(directory, "variables.json")
            variables_io.write_variables(file_path, original)
            with self.assertRaises(ValueError):
                variables_io.write_variables(file_path, {"bad": {"value": []}})
            with mock.patch.object(variables_io.batch_processor_model.os, "replace", side_effect=OSError("locked")):
                with self.assertRaises(OSError):
                    variables_io.write_variables(file_path, replacement)
            self.assertEqual(original, variables_io.read_variables(file_path))
            self.assertEqual(["variables.json"], os.listdir(directory))


class TestEnvironmentVariableQueryPreview(unittest.TestCase):
    """Tests expression evaluation and project isolation with a stub Maya runtime."""

    def setUp(self):
        """Creates a project and intercepts Maya command imports."""
        self.project = variables_io.batch_processor_model.BatchProcessorModel()
        self.project.project_name = "Preview Project"
        self.project.custom_environment_variables = {"saved": {"value": "original", "query": False}}
        maya_module = types.ModuleType("maya")
        self.cmds = types.ModuleType("maya.cmds")
        self.cmds.ls = mock.MagicMock(return_value=["hero_ctrl"])
        maya_module.cmds = self.cmds
        maya_patch = mock.patch.dict(sys.modules, {"maya": maya_module, "maya.cmds": self.cmds})
        maya_patch.start()
        self.addCleanup(maya_patch.stop)

    def test_preview_uses_edited_rows_and_project_without_saving(self):
        """Resolves earlier rows and project context without replacing saved definitions."""
        variables = {
            "prefix": {"value": "edited", "query": False},
            "selected": {"value": "cmds.ls(selection=True)", "query": True},
            "result": {
                "value": "[env['prefix'], env['selected'], env['project-name'], project.project_name, task]",
                "query": True,
            },
            "later": {"value": "cmds.ls()", "query": True},
        }
        saved_data = self.project.to_dict()
        result = variables_io.evaluate_variable("{RESULT}", variables, project=self.project)
        self.assertEqual(["edited", ["hero_ctrl"], "Preview Project", "Preview Project", None], result)
        self.assertEqual(saved_data, self.project.to_dict())
        self.cmds.ls.assert_called_once_with(selection=True)

    def test_preview_propagates_query_failures_even_when_suppressed(self):
        """Distinguishes a failed expression from a successful empty result."""
        self.project.set_suppress_custom_environment_query_errors(True)
        for failing_name in ("earlier", "result"):
            variables = {
                "earlier": {"value": "literal", "query": False},
                "result": {"value": "env['earlier']", "query": True},
            }
            variables[failing_name] = {"value": "1 / 0", "query": True}
            with self.subTest(failing_name=failing_name), self.assertRaisesRegex(
                ValueError, f"Query {{{failing_name}}} failed: division by zero"
            ):
                variables_io.evaluate_variable("result", variables, project=self.project)
        self.assertEqual({"saved": {"value": "original", "query": False}},
                         self.project.custom_environment_variables)

    def test_preview_without_project_preserves_result_types_and_namespace(self):
        """Supports literal query results, JSON, and import_module in a standalone editor."""
        for expression, expected in (("0", 0), ("False", False), ("None", None), ("''", ""),
                                     ("json.loads('[1, 2]')", [1, 2]), ("import_module('math').sqrt(4)", 2.0)):
            with self.subTest(expression=expression):
                result = variables_io.evaluate_variable("result", {"result": {"value": expression, "query": True}})
                self.assertEqual(expected, result)

    def test_missing_preview_name_does_not_execute_any_queries(self):
        """Rejects missing rows before querying the scene."""
        variables = {"selected": {"value": "cmds.ls(selection=True)", "query": True}}
        with self.assertRaisesRegex(ValueError, "Unknown custom environment variable"):
            variables_io.evaluate_variable("missing", variables, project=self.project)
        self.cmds.ls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
