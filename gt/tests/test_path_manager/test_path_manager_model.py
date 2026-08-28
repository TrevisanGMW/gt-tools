"""Pure-Python tests for Path Manager model helpers."""

import logging
import os
import sys
import unittest


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

test_directory = os.path.dirname(__file__)
tests_directory = os.path.dirname(test_directory)
package_root_directory = os.path.dirname(tests_directory)
repository_root_directory = os.path.dirname(package_root_directory)
for path_to_add in [repository_root_directory, package_root_directory, tests_directory]:
    if path_to_add not in sys.path:
        sys.path.append(path_to_add)

from gt.tools.path_manager import path_manager_model


class TestPathManagerModel(unittest.TestCase):
    """Tests pure Path Manager helpers without Maya runtime imports."""

    def test_get_path_basename_supports_windows_separators(self):
        result = path_manager_model.get_path_basename(r"C:\textures\character\body.exr")

        expected = "body.exr"
        self.assertEqual(expected, result)

    def test_find_matching_path_prefers_exact_filename(self):
        candidates = [r"D:\assets\shared\body.exr", r"D:\assets\other\body.exr"]

        result = path_manager_model.find_matching_path(candidates, r"C:\missing\body.exr")

        expected = candidates[0]
        self.assertEqual(expected, result)

    def test_find_matching_path_supports_udim_tokens(self):
        candidates = [r"D:\textures\body.1001.exr", r"D:\textures\body.1002.exr"]

        result = path_manager_model.find_matching_path(candidates, r"C:\missing\body.<UDIM>.exr")

        expected = candidates[0]
        self.assertEqual(expected, result)

    def test_find_matching_path_returns_none_when_not_found(self):
        result = path_manager_model.find_matching_path([r"D:\textures\body.exr"], r"C:\missing\head.exr")

        expected = None
        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
