import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.utils import version_utils


class TestVersionUtils(unittest.TestCase):
    def test_parse_semantic_version(self):
        expected = (1, 2, 3)
        result = version_utils.parse_semantic_version(version_string="1.2.3")
        self.assertEqual(expected, result)

    def test_parse_semantic_version_bigger_numbers(self):
        expected = (123, 456, 789)
        result = version_utils.parse_semantic_version(version_string="123.456.789")
        self.assertEqual(expected, result)

    def test_parse_semantic_version_with_string(self):
        expected = (1, 2, 3)
        result = version_utils.parse_semantic_version(version_string="v1.2.3")
        self.assertEqual(expected, result)

    def test_parse_semantic_version_error(self):
        with self.assertRaises(ValueError):
            version_utils.parse_semantic_version(version_string="random.string")  # No version to be extracted/parsed

    def test_parse_semantic_version_error_two(self):
        with self.assertRaises(ValueError):
            version_utils.parse_semantic_version(version_string="1.2")  # Missing patch version

    def test_compare_versions(self):
        expected = 0  # equal
        result = version_utils.compare_versions(version_a="1.2.3", version_b="1.2.3")
        self.assertEqual(expected, result)

    def test_compare_versions_patch_older(self):
        expected = -1  # older
        result = version_utils.compare_versions(version_a="1.2.3", version_b="1.2.4")
        self.assertEqual(expected, result)

    def test_compare_versions_minor_older(self):
        expected = -1  # older
        result = version_utils.compare_versions(version_a="1.2.3", version_b="1.3.1")
        self.assertEqual(expected, result)

    def test_compare_versions_major_older(self):
        expected = -1  # older
        result = version_utils.compare_versions(version_a="1.2.3", version_b="2.1.1")
        self.assertEqual(expected, result)

    def test_compare_versions_patch_newer(self):
        expected = 1  # newer
        result = version_utils.compare_versions(version_a="1.2.2", version_b="1.2.1")
        self.assertEqual(expected, result)

    def test_compare_versions_minor_newer(self):
        expected = 1  # newer
        result = version_utils.compare_versions(version_a="1.3.3", version_b="1.2.5")
        self.assertEqual(expected, result)

    def test_compare_versions_major_newer(self):
        expected = 1  # newer
        result = version_utils.compare_versions(version_a="2.2.3", version_b="1.6.7")
        self.assertEqual(expected, result)

    @patch('os.path.exists')
    def test_get_package_version_bad_path(self, mock_eval):
        result = version_utils.get_package_version(package_path="mocked_package_path")
        mock_eval.assert_called_once()
        expected = "0.0.0"
        self.assertEqual(expected, result)

    @patch('sys.path')
    @patch('os.path.exists')
    def test_get_package_version(self, mock_exists, mock_path):
        mock_exists.return_value = True
        mock_path.return_value = ['/mocked/path', 'mocked_package_path']
        with patch('builtins.__import__') as mock_import:
            mock_instance = MagicMock()
            mock_instance.__version__ = '1.2.3'
            mock_import.return_value = mock_instance
            result = version_utils.get_package_version(package_path="mocked_package_path")
            mock_exists.assert_called_once()
            mock_import.assert_called_once()
            expected = '1.2.3'
            self.assertEqual(expected, result)
