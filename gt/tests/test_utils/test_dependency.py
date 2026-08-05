from unittest.mock import patch
import unittest
import sys

import gt.utils.dependency as utils_dependency


class TestDependencyUtils(unittest.TestCase):
    def test_normalize_dependencies_from_string(self):
        result = utils_dependency.normalize_dependencies("numpy")
        expected = {"numpy": "numpy"}
        self.assertEqual(expected, result)

    def test_normalize_dependencies_from_mapping(self):
        result = utils_dependency.normalize_dependencies({"PIL": "Pillow"})
        expected = {"PIL": "Pillow"}
        self.assertEqual(expected, result)

    def test_normalize_dependencies_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            utils_dependency.normalize_dependencies(12)

    @patch("gt.utils.dependency.importlib.import_module")
    def test_get_missing_dependencies(self, mock_import_module):
        def import_side_effect(import_name):
            """Raises an import error only for the missing test package.

            Args:
                import_name (str): Requested import name.

            Returns:
                object: Placeholder imported module.

            Raises:
                ImportError: When the requested name is ``missing_module``.
            """
            if import_name == "missing_module":
                raise ImportError
            return object()

        mock_import_module.side_effect = import_side_effect
        result = utils_dependency.get_missing_dependencies(
            {"available_module": "available-package", "missing_module": "missing-package"}
        )
        expected = {"missing_module": "missing-package"}
        self.assertEqual(expected, result)

    def test_build_pip_command_uses_current_interpreter(self):
        result = utils_dependency.build_pip_command("Pillow>=10")
        expected = [sys.executable, "-m", "pip", "install", "Pillow>=10"]
        self.assertEqual(expected, result)

    @patch("gt.utils.dependency.get_missing_dependencies", return_value={})
    def test_ensure_dependencies_skips_ui_when_available(self, _mock_missing):
        result = utils_dependency.ensure_dependencies(["available_module"])
        self.assertTrue(result)
